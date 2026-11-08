"""Authentication, authorization and cross-user isolation."""

from __future__ import annotations

import datetime as dt
from collections.abc import Callable

import jwt
import pytest
from fastapi.testclient import TestClient

from iat.core.config import Settings
from iat.security.identity import SCOPE_INVOKE, SCOPE_READ_CONVERSATIONS
from tests.conftest import INVOKE, TEST_SECRET, TokenFactory

Auth = Callable[[str], dict[str, str]]
QUESTION = {"message": "Can Supplier Acme be approved for onboarding?"}


def _bearer(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.parametrize(
    ("method", "path"),
    [
        ("get", "/v1/agents"),
        ("post", INVOKE),
        ("get", "/v1/conversations"),
        ("get", "/v1/conversations/" + "a" * 32),
    ],
)
def test_protected_endpoints_require_authentication(
    client: TestClient, method: str, path: str
) -> None:
    response = client.request(method, path, json=QUESTION if method == "post" else None)
    assert response.status_code == 401
    assert response.headers["WWW-Authenticate"] == "Bearer"
    assert response.json()["error"]["code"] == "UNAUTHENTICATED"


def _claims(settings: Settings, **overrides: object) -> dict[str, object]:
    now = dt.datetime.now(dt.UTC)
    claims: dict[str, object] = {
        "sub": "alice",
        "scope": f"{SCOPE_INVOKE} {SCOPE_READ_CONVERSATIONS}",
        "iss": settings.jwt_issuer,
        "aud": settings.jwt_audience,
        "iat": now,
        "exp": now + dt.timedelta(minutes=5),
    }
    claims.update(overrides)
    return {k: v for k, v in claims.items() if v is not None}


@pytest.mark.parametrize(
    "label",
    [
        "wrong_secret",
        "expired",
        "wrong_audience",
        "wrong_issuer",
        "missing_sub",
        "missing_exp",
        "bad_subject",
        "alg_none",
        "garbage",
    ],
)
def test_invalid_tokens_are_rejected(client: TestClient, settings: Settings, label: str) -> None:
    now = dt.datetime.now(dt.UTC)
    secret = TEST_SECRET
    claims = _claims(settings)
    algorithm = "HS256"
    if label == "wrong_secret":
        secret = "another-secret-" + "y" * 40
    elif label == "expired":
        claims = _claims(settings, iat=now - dt.timedelta(hours=2), exp=now - dt.timedelta(hours=1))
    elif label == "wrong_audience":
        claims = _claims(settings, aud="someone-else")
    elif label == "wrong_issuer":
        claims = _claims(settings, iss="evil-issuer")
    elif label == "missing_sub":
        claims = _claims(settings, sub=None)
    elif label == "missing_exp":
        claims = _claims(settings, exp=None)
    elif label == "bad_subject":
        claims = _claims(settings, sub="alice; DROP TABLE")

    if label == "garbage":
        token = "not-a-jwt"
    elif label == "alg_none":
        token = jwt.encode(claims, None, algorithm="none")  # type: ignore[arg-type]
    else:
        token = jwt.encode(claims, secret, algorithm=algorithm)

    response = client.get("/v1/agents", headers=_bearer(token))
    assert response.status_code == 401
    assert token not in response.text  # never echo credentials


def test_valid_token_is_accepted(client: TestClient, auth: Auth) -> None:
    response = client.get("/v1/agents", headers=auth("alice"))
    assert response.status_code == 200
    assert response.json()[0]["key"] == "supplier-readiness"


def test_scope_is_enforced_for_invoke(client: TestClient, make_token: TokenFactory) -> None:
    token = make_token("alice", scopes=SCOPE_READ_CONVERSATIONS)
    response = client.post(INVOKE, json=QUESTION, headers=_bearer(token))
    assert response.status_code == 403
    assert response.json()["error"]["code"] == "FORBIDDEN"


def test_scope_is_enforced_for_conversations(client: TestClient, make_token: TokenFactory) -> None:
    token = make_token("alice", scopes=SCOPE_INVOKE)
    assert client.get("/v1/conversations", headers=_bearer(token)).status_code == 403


def test_caller_cannot_assert_a_user_id(client: TestClient, auth: Auth) -> None:
    body = {**QUESTION, "user_id": "bob"}
    response = client.post(INVOKE, json=body, headers=auth("alice"))
    assert response.status_code == 422
    assert "user_id" in response.json()["error"]["message"]


def test_cross_user_conversation_isolation(client: TestClient, auth: Auth) -> None:
    created = client.post(INVOKE, json=QUESTION, headers=auth("alice")).json()
    conversation_id = created["conversation_id"]

    # Owner can read it.
    own = client.get(f"/v1/conversations/{conversation_id}", headers=auth("alice"))
    assert own.status_code == 200
    assert len(own.json()["turns"]) == 2

    # Another user cannot read it, and cannot tell it exists.
    other = client.get(f"/v1/conversations/{conversation_id}", headers=auth("bob"))
    missing = client.get("/v1/conversations/" + "0" * 32, headers=auth("bob"))
    assert other.status_code == missing.status_code == 404
    assert other.json()["error"]["message"] == missing.json()["error"]["message"]

    # Another user cannot append to it.
    hijack = client.post(
        INVOKE, json={**QUESTION, "conversation_id": conversation_id}, headers=auth("bob")
    )
    assert hijack.status_code == 404
    assert (
        len(
            client.get(f"/v1/conversations/{conversation_id}", headers=auth("alice")).json()[
                "turns"
            ]
        )
        == 2
    )

    # Listings are scoped to the caller.
    assert [
        c["conversation_id"] for c in client.get("/v1/conversations", headers=auth("alice")).json()
    ] == [conversation_id]
    assert client.get("/v1/conversations", headers=auth("bob")).json() == []


def test_owner_can_continue_conversation(client: TestClient, auth: Auth) -> None:
    first = client.post(INVOKE, json=QUESTION, headers=auth("alice")).json()
    second = client.post(
        INVOKE,
        json={"message": "What about Supplier Lumen?", "conversation_id": first["conversation_id"]},
        headers=auth("alice"),
    )
    assert second.status_code == 200
    assert second.json()["conversation_id"] == first["conversation_id"]
    view = client.get(f"/v1/conversations/{first['conversation_id']}", headers=auth("alice")).json()
    assert len(view["turns"]) == 4


def test_malformed_conversation_id_rejected(client: TestClient, auth: Auth) -> None:
    response = client.get("/v1/conversations/../../etc", headers=auth("alice"))
    assert response.status_code in {404, 422}
