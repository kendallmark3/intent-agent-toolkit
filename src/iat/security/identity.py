"""Identity verification boundary.

``TokenVerifier`` is the seam for enterprise identity providers. V1 ships ``JwtVerifier``
(locally signed HMAC tokens). An OIDC/JWKS verifier (Entra ID, Okta, Cognito, AgentCore
Identity) can replace it without touching routes, agents or tools — see docs/SECURITY.md.

The caller's identity is *only* ever taken from a verified token's ``sub`` claim. Request
bodies cannot assert a user id. (This closes the cross-user access gap observed in
agent-service-toolkit, where ``user_id`` was accepted from the request payload.)
"""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass, field
from typing import Protocol

import jwt

from iat.core.config import Settings
from iat.core.errors import AuthenticationError, AuthorizationError

_SUBJECT_RE = re.compile(r"^[A-Za-z0-9._@:\-]{1,128}$")

SCOPE_INVOKE = "agents:invoke"
SCOPE_READ_CONVERSATIONS = "conversations:read"


@dataclass(frozen=True)
class Identity:
    subject: str
    scopes: frozenset[str] = field(default_factory=frozenset)

    @property
    def subject_hash(self) -> str:
        """Stable, non-reversible identifier for logs and evidence."""
        return hashlib.sha256(self.subject.encode()).hexdigest()[:16]

    def require_scope(self, scope: str) -> None:
        if scope not in self.scopes:
            raise AuthorizationError(f"Missing required scope: {scope}")


class TokenVerifier(Protocol):
    def verify(self, token: str) -> Identity: ...


class JwtVerifier:
    def __init__(self, settings: Settings) -> None:
        self._secret = settings.jwt_secret.get_secret_value()
        self._issuer = settings.jwt_issuer
        self._audience = settings.jwt_audience
        self._algorithm = settings.jwt_algorithm

    def verify(self, token: str) -> Identity:
        try:
            claims = jwt.decode(
                token,
                self._secret,
                algorithms=[self._algorithm],  # explicit allowlist: blocks "none"/alg confusion
                audience=self._audience,
                issuer=self._issuer,
                options={"require": ["exp", "iat", "sub", "iss", "aud"]},
            )
        except jwt.PyJWTError as exc:
            # Do not echo token contents or library detail back to the caller.
            raise AuthenticationError("Invalid or expired token") from exc

        subject = claims.get("sub")
        if not isinstance(subject, str) or not _SUBJECT_RE.match(subject):
            raise AuthenticationError("Invalid token subject")
        raw_scope = claims.get("scope", "")
        scopes = frozenset(raw_scope.split()) if isinstance(raw_scope, str) else frozenset()
        return Identity(subject=subject, scopes=scopes)
