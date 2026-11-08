"""INTENT-003: workflow trace, agent metadata, regression API, console security, smoke script."""

from __future__ import annotations

import json
import re
import runpy
import socket
import subprocess
import sys
import threading
import time
from collections.abc import Callable, Iterator
from pathlib import Path
from typing import Any

import pytest
import uvicorn
from fastapi.testclient import TestClient
from langgraph.graph import END, StateGraph

from iat.agents.registry import AgentDefinition, default_agents
from iat.api.app import CONSOLE_CSP, create_app
from iat.core.config import Settings
from iat.schemas.assessment import SupplierAssessment
from iat.security.identity import SCOPE_READ_CONVERSATIONS
from iat.services.regression import RegressionCase, evaluate, project
from tests.conftest import INVOKE, TokenFactory

ROOT = Path(__file__).resolve().parent.parent
STATIC = ROOT / "src" / "iat" / "web" / "static"
REGRESSION = "/v1/agents/supplier-readiness/regression"
Auth = Callable[[str], dict[str, str]]


# --- workflow trace ------------------------------------------------------------------------


def test_execution_records_full_workflow_path(client: TestClient, auth: Auth) -> None:
    body = client.post(
        INVOKE, json={"message": "Can Supplier Acme be approved?"}, headers=auth("alice")
    ).json()
    steps = body["execution"]["steps"]
    assert [s["node"] for s in steps] == ["identify", "lookup", "assess", "explain"]
    assert all(s["duration_ms"] >= 0 for s in steps)


def test_execution_trace_shows_skipped_lookup(client: TestClient, auth: Auth) -> None:
    body = client.post(
        INVOKE, json={"message": "Can we onboard them?"}, headers=auth("alice")
    ).json()
    assert [s["node"] for s in body["execution"]["steps"]] == ["identify", "assess", "explain"]
    assert body["execution"]["tools_invoked"] == []


# --- agent metadata ------------------------------------------------------------------------


def test_agent_info_exposes_workflow_examples_and_case_count(
    client: TestClient, auth: Auth
) -> None:
    (info,) = client.get("/v1/agents", headers=auth("alice")).json()
    assert info["workflow"] == ["identify", "lookup", "assess", "explain"]
    assert len(info["examples"]) >= 3
    assert info["regression_cases"] == 6


def test_declared_regression_cases_reference_real_output_fields() -> None:
    (agent,) = default_agents()
    fields = set(agent.output_model.model_fields)
    for case in agent.regression_cases:
        for key in case.expect:
            assert key.split(".")[0] in fields, f"{case.name}: unknown field {key}"


# --- regression evaluation and endpoint ------------------------------------------------------


def test_projection_and_evaluation_are_order_insensitive() -> None:
    output = {"decision": "X", "missing_evidence": [{"check": "b"}, {"check": "a"}], "n": None}
    assert project(output, "missing_evidence.check") == ["a", "b"]
    assert project(output, "n") is None
    assert project(output, "decision.check") is None
    assert evaluate({"decision": "X", "missing_evidence.check": ["b", "a"]}, output)[0]
    assert not evaluate({"decision": "Y"}, output)[0]


def test_regression_endpoint_passes_all_cases(client: TestClient, auth: Auth) -> None:
    report = client.post(REGRESSION, headers=auth("alice")).json()
    assert (report["total"], report["passed"], report["failed"]) == (6, 6, 0)
    assert all(c["execution_id"] for c in report["cases"])
    assert report["request_id"]


def test_regression_requires_invoke_scope(client: TestClient, make_token: TokenFactory) -> None:
    token = make_token("alice", scopes=SCOPE_READ_CONVERSATIONS)
    response = client.post(REGRESSION, headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 403


def test_regression_requires_authentication(client: TestClient) -> None:
    assert client.post(REGRESSION).status_code == 401


def test_regression_unknown_agent_is_404(client: TestClient, auth: Auth) -> None:
    assert client.post("/v1/agents/nope/regression", headers=auth("alice")).status_code == 404


def test_regression_reports_a_failing_expectation(settings: Settings, auth: Auth) -> None:
    (supplier,) = default_agents()
    wrong = RegressionCase(
        name="wrong", message="Can Supplier Acme be approved?", expect={"decision": "NOT_READY"}
    )
    agent = AgentDefinition(**{**supplier.__dict__, "regression_cases": (wrong,)})
    with TestClient(create_app(settings, agents=[agent])) as client:
        report = client.post(REGRESSION, headers=auth("alice")).json()
    assert report["failed"] == 1
    assert report["cases"][0]["actual"] == {"decision": "READY"}


def test_regression_records_agent_errors_as_failures(settings: Settings, auth: Auth) -> None:
    def explode(state: dict[str, Any]) -> dict[str, Any]:
        raise RuntimeError("boom")

    graph = StateGraph(dict)
    graph.add_node("explode", explode)
    graph.set_entry_point("explode")
    graph.add_edge("explode", END)
    broken = AgentDefinition(
        key="broken",
        description="fails",
        allowed_tools=frozenset(),
        graph=graph.compile(),
        output_key="assessment",
        output_model=SupplierAssessment,
        regression_cases=(RegressionCase(name="any", message="hi", expect={"decision": "READY"}),),
    )
    with TestClient(create_app(settings, agents=[broken])) as client:
        report = client.post("/v1/agents/broken/regression", headers=auth("alice")).json()
    assert report["failed"] == 1
    assert report["cases"][0]["error"] == "AGENT_EXECUTION_FAILED"
    assert report["cases"][0]["execution_id"]


# --- console and headers ---------------------------------------------------------------------


def test_root_redirects_to_console(client: TestClient) -> None:
    response = client.get("/", follow_redirects=False)
    assert response.status_code == 307
    assert response.headers["location"] == "/ui/"


def test_console_is_served_with_strict_csp(client: TestClient) -> None:
    response = client.get("/ui/")
    assert response.status_code == 200
    assert response.headers["content-security-policy"] == CONSOLE_CSP
    assert "script-src 'self'" in CONSOLE_CSP and "'unsafe-inline'" not in CONSOLE_CSP
    for asset in ("app.js", "styles.css", "favicon.svg"):
        assert client.get(f"/ui/{asset}").status_code == 200


def test_console_has_no_inline_script_or_remote_assets() -> None:
    html = (STATIC / "index.html").read_text()
    for tag in re.findall(r"<script\b[^>]*>", html):
        assert 'src="' in tag
    assert "http://" not in html and "https://" not in html
    assert not re.search(r"\son[a-z]+=", html)  # no inline event handlers


def test_console_script_renders_text_only() -> None:
    source = (STATIC / "app.js").read_text()
    script = "\n".join(line.split("//")[0] for line in source.splitlines())  # code, not comments
    for sink in ("innerHTML", "outerHTML", "insertAdjacentHTML", "document.write", "eval("):
        assert sink not in script
    assert "textContent" in script


@pytest.mark.parametrize("path", ["/health", "/v1/agents", "/ui/"])
def test_security_headers_on_all_surfaces(client: TestClient, auth: Auth, path: str) -> None:
    response = client.get(path, headers=auth("alice"))
    assert response.headers["x-content-type-options"] == "nosniff"
    assert response.headers["x-frame-options"] == "DENY"
    assert response.headers["referrer-policy"] == "no-referrer"


def test_api_responses_are_not_cached(client: TestClient, auth: Auth) -> None:
    assert client.get("/v1/agents", headers=auth("alice")).headers["cache-control"] == "no-store"


def test_swagger_docs_keep_working_without_console_csp(client: TestClient) -> None:
    response = client.get("/docs")
    assert response.status_code == 200
    assert "content-security-policy" not in response.headers


# --- developer tooling -----------------------------------------------------------------------


def test_init_env_creates_secret_once(tmp_path: Path) -> None:
    (tmp_path / ".env.example").write_text((ROOT / ".env.example").read_text())
    init = runpy.run_path(str(ROOT / "scripts" / "init_env.py"))["main"]
    assert init(tmp_path) == 0
    first = (tmp_path / ".env").read_text()
    secret = re.search(r"^IAT_JWT_SECRET=(.+)$", first, re.M)
    assert secret and len(secret.group(1)) >= 32
    assert oct((tmp_path / ".env").stat().st_mode)[-3:] == "600"
    assert init(tmp_path) == 0
    assert (tmp_path / ".env").read_text() == first  # never overwritten


def test_vscode_config_is_valid_and_consistent() -> None:
    tasks = json.loads((ROOT / ".vscode" / "tasks.json").read_text())["tasks"]
    labels = {t["label"] for t in tasks}
    launch = json.loads((ROOT / ".vscode" / "launch.json").read_text())["configurations"]
    for config in launch:
        if "preLaunchTask" in config:
            assert config["preLaunchTask"] in labels
    makefile = (ROOT / "Makefile").read_text()
    for task in tasks:
        target = task["command"].removeprefix("make ")
        assert re.search(rf"^{re.escape(target)}:", makefile, re.M), target


# --- smoke script against a real HTTP server -------------------------------------------------


@pytest.fixture
def live_server(settings: Settings) -> Iterator[str]:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        port = sock.getsockname()[1]
    server = uvicorn.Server(
        uvicorn.Config(create_app(settings), host="127.0.0.1", port=port, log_level="warning")
    )
    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()
    deadline = time.monotonic() + 10
    while not server.started and time.monotonic() < deadline:
        time.sleep(0.05)
    yield f"http://127.0.0.1:{port}"
    server.should_exit = True
    thread.join(timeout=5)


def test_smoke_script_passes_against_live_server(
    live_server: str, make_token: TokenFactory, tmp_path: Path
) -> None:
    out = tmp_path / "smoke.json"
    result = subprocess.run(  # noqa: S603 - fixed interpreter and repo script
        [
            sys.executable,
            str(ROOT / "scripts" / "smoke.py"),
            "--base-url",
            live_server,
            "--token",
            make_token("smoke"),
            "--out",
            str(out),
            "--wait",
            "10",
        ],
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    report = json.loads(out.read_text())
    assert report["passed"] and all(c["passed"] for c in report["checks"])
    assert report["regressions"][0]["passed"] == 6


def test_smoke_script_fails_with_bad_token(live_server: str) -> None:
    result = subprocess.run(  # noqa: S603 - fixed interpreter and repo script
        [
            sys.executable,
            str(ROOT / "scripts" / "smoke.py"),
            "--base-url",
            live_server,
            "--token",
            "not-a-token",
            "--wait",
            "10",
        ],
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert result.returncode == 1
    assert "FAIL token can list agents" in result.stdout


# --- agent-neutral HTTP contract (independent finding C-026/027) -----------------------------


def test_second_agent_with_different_output_model_works_over_http(
    settings: Settings, auth: Auth
) -> None:
    from pydantic import BaseModel

    class EchoResult(BaseModel):
        echoed: str
        length: int

    graph = StateGraph(dict)
    graph.add_node(
        "echo", lambda s: {"result": {"echoed": s["message"], "length": len(s["message"])}}
    )
    graph.set_entry_point("echo")
    graph.add_edge("echo", END)
    echo = AgentDefinition(
        key="echo",
        description="Echoes the message (contract test agent).",
        allowed_tools=frozenset(),
        graph=graph.compile(),
        output_key="result",
        output_model=EchoResult,
        examples=("hello",),
        regression_cases=(RegressionCase(name="echo", message="hello", expect={"length": 5}),),
    )
    with TestClient(create_app(settings, agents=[*default_agents(), echo])) as client:
        body = client.post("/v1/agents/echo/invoke", json={"message": "hello"}, headers=auth("a"))
        report = client.post("/v1/agents/echo/regression", headers=auth("a")).json()
        listed = {a["key"] for a in client.get("/v1/agents", headers=auth("a")).json()}
    assert body.status_code == 200, body.text
    assert body.json()["output"] == {"echoed": "hello", "length": 5}
    assert [s["node"] for s in body.json()["execution"]["steps"]] == ["echo"]
    assert report["passed"] == 1
    assert listed == {"echo", "supplier-readiness"}


def test_container_image_disables_api_docs_by_default() -> None:
    dockerfile = (ROOT / "Dockerfile").read_text()
    assert "IAT_DOCS_ENABLED=false" in dockerfile
    assert "USER iat" in dockerfile and "HEALTHCHECK" in dockerfile
