"""INTENT-002 finding A: tool permissions come from registration, not agent-controlled input."""

from __future__ import annotations

from typing import Any, ClassVar

import pytest
from langchain_core.runnables import RunnableConfig
from langgraph.graph import END, StateGraph
from pydantic import BaseModel

from iat.agents.registry import AgentDefinition, AgentRegistry, default_agents
from iat.agents.supplier_readiness import graph as supplier_graph
from iat.core.config import DEFAULT_DATA_PATH
from iat.schemas.assessment import Decision, SupplierAssessment
from iat.schemas.execution import ToolStatus
from iat.security.identity import Identity
from iat.services.supplier_repository import SupplierRepository
from iat.tools.base import Tool
from iat.tools.registry import (
    AgentToolGateway,
    ExecutionRecorder,
    ToolExecutor,
    ToolPolicy,
    ToolRegistry,
)
from iat.tools.supplier_evidence import SupplierEvidenceLookupTool
from tests.conftest import build_runner

LOOKUP = SupplierEvidenceLookupTool.name


class _Empty(BaseModel):
    pass


class DeleteSupplierTool(Tool[_Empty, _Empty]):
    name: ClassVar[str] = "delete_supplier"
    description: ClassVar[str] = "Deletes a supplier (write)."
    read_only: ClassVar[bool] = False
    input_model: ClassVar[type[BaseModel]] = _Empty
    output_model: ClassVar[type[BaseModel]] = _Empty
    calls = 0

    def run(self, args: _Empty) -> _Empty:
        DeleteSupplierTool.calls += 1
        return _Empty()


@pytest.fixture(autouse=True)
def _reset_calls() -> None:
    DeleteSupplierTool.calls = 0


@pytest.fixture
def tools() -> ToolRegistry:
    repo = SupplierRepository.from_json(DEFAULT_DATA_PATH)
    return ToolRegistry([SupplierEvidenceLookupTool(repo), DeleteSupplierTool()])


def _agent_that_calls(key: str, tool: str, registered: frozenset[str]) -> AgentDefinition:
    """An agent registered with ``registered`` whose graph attempts to call ``tool``."""

    def act(state: dict[str, Any], config: RunnableConfig) -> dict[str, Any]:
        gateway: AgentToolGateway = config["configurable"]["tools"]
        result = gateway.invoke(tool, {})
        exposed = [type(v).__name__ for v in config["configurable"].values()]
        return {"assessment": {"attempt": result.status.value, "seen": exposed}}

    graph = StateGraph(dict)
    graph.add_node("act", act)
    graph.set_entry_point("act")
    graph.add_edge("act", END)

    class Attempt(BaseModel):
        attempt: str
        seen: list[str]

    return AgentDefinition(
        key=key,
        description="test agent",
        allowed_tools=registered,
        graph=graph.compile(),
        output_key="assessment",
        output_model=Attempt,
    )


def _run(runner: Any, agent_key: str) -> Any:
    return runner.run(
        agent_key=agent_key, message="go", identity=Identity("alice"), request_id=None
    )


def test_agent_cannot_call_tool_outside_its_registration(tools: ToolRegistry) -> None:
    rogue = _agent_that_calls("rogue", "delete_supplier", registered=frozenset({LOOKUP}))
    outcome = _run(build_runner(tools, [rogue]), "rogue")
    assert outcome.output.attempt == "DENIED"
    assert outcome.execution.tools_invoked[0].error_class == "ToolNotAllowed"
    assert DeleteSupplierTool.calls == 0


def test_registered_permission_still_works(tools: ToolRegistry) -> None:
    admin = _agent_that_calls("admin", "delete_supplier", registered=frozenset({"delete_supplier"}))
    outcome = _run(build_runner(tools, [admin]), "admin")
    assert outcome.output.attempt == "OK"
    assert DeleteSupplierTool.calls == 1


def test_permission_is_bound_to_the_running_agent_not_shared(tools: ToolRegistry) -> None:
    admin = _agent_that_calls("admin", "delete_supplier", registered=frozenset({"delete_supplier"}))
    rogue = _agent_that_calls("rogue", "delete_supplier", registered=frozenset())
    runner = build_runner(tools, [admin, rogue])
    assert _run(runner, "rogue").output.attempt == "DENIED"
    assert _run(runner, "admin").output.attempt == "OK"
    assert DeleteSupplierTool.calls == 1


def test_agent_receives_only_a_bound_gateway(tools: ToolRegistry) -> None:
    probe = _agent_that_calls("probe", LOOKUP, registered=frozenset())
    seen = _run(build_runner(tools, [probe]), "probe").output.seen
    # LangGraph adds its own runtime keys; check by type that only the bound gateway is exposed.
    assert "AgentToolGateway" in seen
    assert not {"ToolExecutor", "ToolPolicy", "ExecutionRecorder", "ToolRegistry"} & set(seen)


def test_gateway_signature_accepts_no_permission_arguments(tools: ToolRegistry) -> None:
    executor = ToolExecutor(tools, ToolPolicy({}, tools))
    gateway = executor.bind("supplier-readiness", ExecutionRecorder())
    with pytest.raises(TypeError):
        gateway.invoke(LOOKUP, {}, allowed_tools={"delete_supplier"})  # type: ignore[call-arg]


def test_changing_agent_constant_at_runtime_grants_nothing(
    tools: ToolRegistry, monkeypatch: pytest.MonkeyPatch
) -> None:
    runner = build_runner(tools)  # policy snapshot taken at startup
    registry = AgentRegistry(default_agents())
    executor = ToolExecutor(tools, ToolPolicy(registry.tool_grants(), tools))
    monkeypatch.setattr(supplier_graph, "ALLOWED_TOOLS", frozenset({LOOKUP, "delete_supplier"}))
    outcome = runner.run(
        agent_key="supplier-readiness",
        message="Can Supplier Acme be approved?",
        identity=Identity("alice"),
        request_id=None,
    )
    assert isinstance(outcome.output, SupplierAssessment)
    assert outcome.output.decision is Decision.READY
    result = executor.bind("supplier-readiness", ExecutionRecorder()).invoke("delete_supplier", {})
    assert result.status is ToolStatus.DENIED
    assert DeleteSupplierTool.calls == 0


def test_unknown_agent_has_no_permissions(tools: ToolRegistry) -> None:
    policy = ToolPolicy({"supplier-readiness": {LOOKUP}}, tools)
    gateway = ToolExecutor(tools, policy).bind("not-registered", ExecutionRecorder())
    assert gateway.invoke(LOOKUP, {"supplier_reference": "Acme"}).status is ToolStatus.DENIED


def test_policy_rejects_grants_for_unregistered_tools(tools: ToolRegistry) -> None:
    with pytest.raises(ValueError, match="unregistered tools"):
        ToolPolicy({"supplier-readiness": {LOOKUP, "shell_exec"}}, tools)


def test_policy_is_immutable(tools: ToolRegistry) -> None:
    policy = ToolPolicy({"supplier-readiness": {LOOKUP}}, tools)
    with pytest.raises(TypeError):
        policy._grants["supplier-readiness"] = frozenset({"delete_supplier"})  # type: ignore[index]


def test_app_startup_fails_when_agent_grant_references_missing_tool(
    settings: Any, tools: ToolRegistry
) -> None:
    from iat.api.app import create_app

    broken = _agent_that_calls("broken", LOOKUP, registered=frozenset({"no_such_tool"}))
    with pytest.raises(ValueError, match="unregistered tools"):
        create_app(settings, agents=[broken])
