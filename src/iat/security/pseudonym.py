"""Keyed pseudonyms for caller identities in logs and execution evidence.

INTENT-002 finding B. INTENT-001 logged ``sha256(subject)[:16]``. That is unsalted, so anyone can
hash a list of likely user names and match log lines. IAT now logs::

    HMAC-SHA256(key, subject) truncated to 128 bits (32 hex characters)

* **Correlation still works:** the same subject yields the same value for a given key, so one
  user's executions can be grouped across log lines.
* **Dictionary hashing does not work without the key:** an attacker with logs but not the key
  cannot test candidate user names.

The key is ``IAT_SUBJECT_PSEUDONYM_KEY`` when set. Otherwise it is derived from the JWT secret
with a fixed domain-separation label, so no new required setting is introduced and the JWT
secret itself is never used directly as an HMAC key for this purpose.

Limitations (see docs/SECURITY.md): anyone holding the key can recompute pseudonyms; rotating the
key (or, when derived, the JWT secret) breaks correlation with older log lines; this is
pseudonymisation, not anonymisation.
"""

from __future__ import annotations

import hashlib
import hmac

from pydantic import SecretStr

PSEUDONYM_HEX_CHARS = 32
_DERIVATION_LABEL = b"iat/subject-pseudonym/v1"


def derive_key(jwt_secret: SecretStr, explicit_key: SecretStr | None) -> bytes:
    if explicit_key is not None:
        return explicit_key.get_secret_value().encode()
    return hmac.new(
        jwt_secret.get_secret_value().encode(), _DERIVATION_LABEL, hashlib.sha256
    ).digest()


class SubjectPseudonymizer:
    __slots__ = ("_key",)

    def __init__(self, key: bytes) -> None:
        if len(key) < 32:
            raise ValueError("Pseudonym key must be at least 32 bytes")
        self._key = key

    def __call__(self, subject: str) -> str:
        digest = hmac.new(self._key, subject.encode(), hashlib.sha256).hexdigest()
        return digest[:PSEUDONYM_HEX_CHARS]

    def __repr__(self) -> str:  # never render the key
        return "SubjectPseudonymizer(key=***)"
