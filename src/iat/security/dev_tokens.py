"""Local development token issuer.

This is a developer convenience that stands in for an enterprise identity provider. It signs
tokens with ``IAT_JWT_SECRET`` from the environment; it is not exposed over HTTP.

    uv run iat-token --sub alice
"""

from __future__ import annotations

import argparse
import datetime as dt
import uuid

import jwt

from iat.core.config import Settings, get_settings
from iat.security.identity import SCOPE_INVOKE, SCOPE_READ_CONVERSATIONS

DEFAULT_SCOPES = f"{SCOPE_INVOKE} {SCOPE_READ_CONVERSATIONS}"


def issue_token(
    settings: Settings,
    subject: str,
    scopes: str = DEFAULT_SCOPES,
    ttl: dt.timedelta = dt.timedelta(hours=1),
    now: dt.datetime | None = None,
) -> str:
    issued = now or dt.datetime.now(dt.UTC)
    claims = {
        "sub": subject,
        "scope": scopes,
        "iss": settings.jwt_issuer,
        "aud": settings.jwt_audience,
        "iat": issued,
        "exp": issued + ttl,
        "jti": uuid.uuid4().hex,
    }
    return jwt.encode(claims, settings.jwt_secret.get_secret_value(), settings.jwt_algorithm)


def main() -> None:
    parser = argparse.ArgumentParser(description="Issue a local IAT development token.")
    parser.add_argument("--sub", required=True, help="Subject (user id) for the token")
    parser.add_argument("--scopes", default=DEFAULT_SCOPES)
    parser.add_argument("--ttl-minutes", type=int, default=60)
    args = parser.parse_args()
    token = issue_token(
        get_settings(), args.sub, args.scopes, dt.timedelta(minutes=args.ttl_minutes)
    )
    print(token)


if __name__ == "__main__":
    main()
