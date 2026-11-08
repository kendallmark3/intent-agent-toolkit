from __future__ import annotations

import json
import os
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from pydantic import SecretStr, ValidationError

from iat import __version__
from iat.api.app import create_app
from iat.core.config import Settings
from tests.conftest import AS_OF, TEST_SECRET


def test_app_starts_and_serves_openapi(client: TestClient) -> None:
    response = client.get("/openapi.json")
    assert response.status_code == 200
    spec = response.json()
    assert spec["info"]["version"] == __version__
    assert "HTTPBearer" in spec["components"]["securitySchemes"]
    assert "/v1/agents/{agent_key}/invoke" in spec["paths"]


def test_startup_fails_closed_without_secret(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("IAT_JWT_SECRET", raising=False)
    with pytest.raises(ValidationError):
        Settings(_env_file=None)  # type: ignore[call-arg]


def test_startup_rejects_weak_secret() -> None:
    with pytest.raises(ValidationError, match="at least 32"):
        Settings(jwt_secret=SecretStr("short"), _env_file=None)  # type: ignore[call-arg]


def test_startup_rejects_non_hmac_algorithm() -> None:
    with pytest.raises(ValidationError):
        Settings(jwt_secret=SecretStr(TEST_SECRET), jwt_algorithm="none", _env_file=None)  # type: ignore[call-arg]


def test_liveness_is_public(client: TestClient) -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "version": __version__, "checks": {}}


def test_readiness_reports_real_dependencies(client: TestClient) -> None:
    body = client.get("/health/ready").json()
    assert body["status"] == "ok"
    assert body["checks"] == {
        "supplier_data_loaded": True,
        "agents_registered": True,
        "tools_registered": True,
    }


def test_readiness_is_503_when_dependency_missing(tmp_path: Path) -> None:
    empty = tmp_path / "suppliers.json"
    empty.write_text(json.dumps({"suppliers": []}))
    settings = Settings(
        jwt_secret=SecretStr(TEST_SECRET),
        assessment_date=AS_OF,
        supplier_data_path=empty,
        _env_file=None,  # type: ignore[call-arg]
    )
    with TestClient(create_app(settings)) as client:
        response = client.get("/health/ready")
    assert response.status_code == 503
    assert response.json()["checks"]["supplier_data_loaded"] is False


def test_docs_can_be_disabled() -> None:
    settings = Settings(jwt_secret=SecretStr(TEST_SECRET), docs_enabled=False, _env_file=None)  # type: ignore[call-arg]
    with TestClient(create_app(settings)) as client:
        assert client.get("/openapi.json").status_code == 404
        assert client.get("/docs").status_code == 404


def test_documented_env_example_setup_starts(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """README path: copy .env.example, set only IAT_JWT_SECRET, start (INTENT-002 regression)."""
    root = Path(__file__).resolve().parent.parent
    example = (root / ".env.example").read_text()
    assert "\nIAT_JWT_SECRET=\n" in example
    (tmp_path / ".env").write_text(
        example.replace("\nIAT_JWT_SECRET=\n", f"\nIAT_JWT_SECRET={TEST_SECRET}\n")
    )
    for key in list(os.environ):
        if key.startswith("IAT_"):
            monkeypatch.delenv(key)
    monkeypatch.chdir(tmp_path)
    settings = Settings()  # type: ignore[call-arg]
    assert settings.assessment_date is None
    assert settings.subject_pseudonym_key is None
    with TestClient(create_app(settings)) as client:
        assert client.get("/health/ready").status_code == 200
