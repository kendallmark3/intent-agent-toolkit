"""Error handling, request identification, execution evidence and log hygiene."""

from __future__ import annotations

import json
import logging
from collections.abc import Callable
from typing import Any

import pytest
from fastapi.testclient import TestClient
from langgraph.graph import END, StateGraph

from iat.agents.registry import AgentDefinition, default_agents
from iat.api.app import create_app
from iat.core.config import Settings
from iat.core.logging import JsonFormatter, redact_text
from iat.schemas.assessment import SupplierAssessment
from tests.conftest import INVOKE, TokenFactory

Auth = Callable[[str], dict[str, str]]


def _broken_agent() -> AgentDefinition:
    def explode(state: dict[str, Any]) -> dict[str, Any]:
        raise RuntimeError("internal detail: db password=hunter2")

    graph = StateGraph(dict)
    graph.add_node("explode", explode)
    graph.set_entry_point("explode")
    graph.add_edge("explode", END)
    return AgentDefinition(
        key="broken",
        description="Always fails",
        allowed_tools=frozenset(),
        graph=graph.compile(),
        output_key="assessment",
        output_model=SupplierAssessment,
    )


def _bad_output_agent() -> AgentDefinition:
    graph = StateGraph(dict)
    graph.add_node("emit", lambda s: {"assessment": {"decision": "MAYBE"}})
    graph.set_entry_point("emit")
    graph.add_edge("emit", END)
    return AgentDefinition(
        key="sloppy",
        description="Returns invalid output",
        allowed_tools=frozenset(),
        graph=graph.compile(),
        output_key="assessment",
        output_model=SupplierAssessment,
    )


@pytest.fixture
def faulty_client(settings: Settings) -> TestClient:
    app = create_app(settings, agents=[*default_agents(), _broken_agent(), _bad_output_agent()])
    return TestClient(app, raise_server_exceptions=False)


def test_agent_failure_returns_safe_envelope(faulty_client: TestClient, auth: Auth) -> None:
    response = faulty_client.post(
        "/v1/agents/broken/invoke", json={"message": "hi"}, headers=auth("alice")
    )
    assert response.status_code == 500
    error = response.json()["error"]
    assert error["code"] == "AGENT_EXECUTION_FAILED"
    assert len(error["execution_id"]) == 32
    assert error["request_id"] == response.headers["X-Request-ID"]
    assert "hunter2" not in response.text and "RuntimeError" not in response.text


def test_invalid_agent_output_is_rejected(faulty_client: TestClient, auth: Auth) -> None:
    response = faulty_client.post(
        "/v1/agents/sloppy/invoke", json={"message": "hi"}, headers=auth("alice")
    )
    assert response.status_code == 500
    assert response.json()["error"]["message"] == "Agent produced an invalid result"


def test_failed_execution_does_not_create_conversation(
    faulty_client: TestClient, auth: Auth
) -> None:
    faulty_client.post("/v1/agents/broken/invoke", json={"message": "hi"}, headers=auth("alice"))
    assert faulty_client.get("/v1/conversations", headers=auth("alice")).json() == []


def test_unknown_agent_is_404(client: TestClient, auth: Auth) -> None:
    response = client.post("/v1/agents/nope/invoke", json={"message": "hi"}, headers=auth("alice"))
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "NOT_FOUND"


def test_unknown_route_uses_envelope(client: TestClient) -> None:
    assert client.get("/does-not-exist").json()["error"]["code"] == "NOT_FOUND"


@pytest.mark.parametrize("body", [{}, {"message": ""}, {"message": "x" * 2001}, {"message": 5}])
def test_validation_errors_do_not_echo_input(
    client: TestClient, auth: Auth, body: dict[str, Any]
) -> None:
    response = client.post(INVOKE, json=body, headers=auth("alice"))
    assert response.status_code == 422
    error = response.json()["error"]
    assert error["code"] == "VALIDATION_ERROR"
    assert "xxxx" not in response.text


def test_request_id_is_propagated(client: TestClient, auth: Auth) -> None:
    response = client.post(
        INVOKE,
        json={"message": "Can Supplier Acme be approved?"},
        headers={**auth("alice"), "X-Request-ID": "demo-request-0001"},
    )
    assert response.headers["X-Request-ID"] == "demo-request-0001"
    assert response.json()["request_id"] == "demo-request-0001"
    assert response.json()["execution"]["request_id"] == "demo-request-0001"


def test_unsafe_request_id_is_replaced(client: TestClient) -> None:
    response = client.get("/health", headers={"X-Request-ID": "bad id\r\ninjected: 1"})
    assert response.headers["X-Request-ID"] != "bad id\r\ninjected: 1"
    assert len(response.headers["X-Request-ID"]) == 32


def test_execution_evidence_is_complete(client: TestClient, auth: Auth) -> None:
    execution = client.post(
        INVOKE, json={"message": "Can Supplier Acme be approved?"}, headers=auth("alice")
    ).json()["execution"]
    assert execution["agent"] == "supplier-readiness"
    assert execution["status"] == "COMPLETED"
    assert execution["duration_ms"] >= 0
    assert execution["error_class"] is None
    assert [t["tool"] for t in execution["tools_invoked"]] == ["supplier_evidence_lookup"]
    assert execution["subject_hash"] != "alice"


def test_logs_exclude_secrets_and_message_content(
    client: TestClient, make_token: TokenFactory, capsys: pytest.CaptureFixture[str]
) -> None:
    token = make_token("alice")
    secret_question = "Can Supplier Acme be approved? confidential-marker-42"
    client.post(
        INVOKE, json={"message": secret_question}, headers={"Authorization": f"Bearer {token}"}
    )
    out = capsys.readouterr().out
    lines = [json.loads(line) for line in out.splitlines() if line.startswith("{")]
    assert any(line["event"] == "agent_execution" for line in lines)
    assert token not in out
    assert "confidential-marker-42" not in out
    assert "alice" not in out  # identity appears only as a hash


def test_formatter_redacts_sensitive_fields() -> None:
    record = logging.makeLogRecord(
        {
            "msg": "auth Bearer abc.def.ghi",
            "levelname": "INFO",
            "name": "iat.test",
            "authorization": "Bearer xyz",
            "nested": {"password": "p"},
        }
    )
    rendered = json.loads(JsonFormatter().format(record))
    assert "abc.def.ghi" not in rendered["event"]
    assert rendered["authorization"] == "[REDACTED]"
    assert rendered["nested"]["password"] == "[REDACTED]"


def test_redact_text_strips_bare_jwts() -> None:
    assert "eyJ" not in redact_text("token eyJhbGciOi.eyJzdWIiOi.c2lnbmF0dXJl here")
