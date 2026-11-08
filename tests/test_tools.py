"""Tool registration, authorization, validation and failure containment."""

from __future__ import annotations

from typing import ClassVar

import pytest
from pydantic import BaseModel

from iat.core.config import DEFAULT_DATA_PATH
from iat.schemas.assessment import Decision, SupplierAssessment
from iat.schemas.execution import ToolStatus
from iat.security.identity import Identity
from iat.services.supplier_repository import SupplierRepository
from iat.tools.base import Tool
from iat.tools.registry import ExecutionRecorder, ToolExecutor, ToolPolicy, ToolRegistry
from iat.tools.supplier_evidence import SupplierEvidenceLookupTool
from tests.conftest import build_runner

LOOKUP = SupplierEvidenceLookupTool.name


class _Empty(BaseModel):
    pass


class DeleteSupplierTool(Tool[_Empty, _Empty]):
    """A registered, write-capable tool the reference agent is NOT allowed to use."""

    name: ClassVar[str] = "delete_supplier"
    description: ClassVar[str] = "Deletes a supplier."
    read_only: ClassVar[bool] = False
    input_model: ClassVar[type[BaseModel]] = _Empty
    output_model: ClassVar[type[BaseModel]] = _Empty
    calls = 0

    def run(self, args: _Empty) -> _Empty:
        DeleteSupplierTool.calls += 1
        return _Empty()


class ExplodingRepository(SupplierRepository):
    def find(self, reference: str) -> list:  # type: ignore[type-arg]
        raise ConnectionError("backend down: password=hunter2")


@pytest.fixture
def repo() -> SupplierRepository:
    return SupplierRepository.from_json(DEFAULT_DATA_PATH)


@pytest.fixture
def registry(repo: SupplierRepository) -> ToolRegistry:
    return ToolRegistry([SupplierEvidenceLookupTool(repo), DeleteSupplierTool()])


def _invoke(registry: ToolRegistry, tool: str, args: dict[str, object]):  # type: ignore[no-untyped-def]
    recorder = ExecutionRecorder()
    policy = ToolPolicy({"supplier-readiness": {LOOKUP}}, registry)
    gateway = ToolExecutor(registry, policy).bind("supplier-readiness", recorder)
    return gateway.invoke(tool, args), recorder


def test_approved_tool_executes(registry: ToolRegistry) -> None:
    result, recorder = _invoke(registry, LOOKUP, {"supplier_reference": "Acme"})
    assert result.status is ToolStatus.OK
    assert result.output is not None and result.output["supplier_id"] == "SUP-001"
    assert recorder.records[0].status is ToolStatus.OK


def test_unregistered_tool_is_denied(registry: ToolRegistry) -> None:
    result, recorder = _invoke(registry, "shell_exec", {"cmd": "rm -rf /"})
    assert result.status is ToolStatus.DENIED
    assert recorder.records[0].error_class == "UnregisteredTool"


def test_registered_but_unauthorized_tool_is_denied(registry: ToolRegistry) -> None:
    DeleteSupplierTool.calls = 0
    result, recorder = _invoke(registry, "delete_supplier", {})
    assert result.status is ToolStatus.DENIED
    assert recorder.records[0].error_class == "ToolNotAllowed"
    assert DeleteSupplierTool.calls == 0  # never executed


@pytest.mark.parametrize(
    "args",
    [
        {},
        {"supplier_reference": ""},
        {"supplier_reference": "x" * 101},
        {"supplier_reference": "Acme; DROP TABLE"},
        {"supplier_reference": "Acme", "unexpected": True},
    ],
)
def test_tool_inputs_are_validated(registry: ToolRegistry, args: dict[str, object]) -> None:
    result, recorder = _invoke(registry, LOOKUP, args)
    assert result.status is ToolStatus.INVALID_INPUT
    assert recorder.records[0].status is ToolStatus.INVALID_INPUT


def test_tool_failure_is_contained_and_not_leaked() -> None:
    registry = ToolRegistry([SupplierEvidenceLookupTool(ExplodingRepository([]))])
    result, recorder = _invoke(registry, LOOKUP, {"supplier_reference": "Acme"})
    assert result.status is ToolStatus.ERROR
    assert result.error == "Tool execution failed"
    assert "hunter2" not in result.model_dump_json()
    assert recorder.records[0].error_class == "ConnectionError"


def test_agent_fails_closed_when_tool_fails() -> None:
    registry = ToolRegistry([SupplierEvidenceLookupTool(ExplodingRepository([]))])
    runner = build_runner(registry)
    outcome = runner.run(
        agent_key="supplier-readiness",
        message="Can Supplier Acme be approved?",
        identity=Identity("alice"),
        request_id=None,
    )
    assert isinstance(outcome.output, SupplierAssessment)
    assert outcome.output.decision is Decision.INSUFFICIENT_EVIDENCE
    assert outcome.execution.tools_invoked[0].status is ToolStatus.ERROR


def test_duplicate_registration_rejected(repo: SupplierRepository) -> None:
    with pytest.raises(ValueError, match="already registered"):
        ToolRegistry([SupplierEvidenceLookupTool(repo), SupplierEvidenceLookupTool(repo)])


def test_tool_spec_is_mcp_shaped(registry: ToolRegistry) -> None:
    spec = next(s for s in registry.specs() if s.name == LOOKUP)
    assert spec.read_only is True
    assert spec.input_schema["type"] == "object"
    assert spec.input_schema["required"] == ["supplier_reference"]
    assert spec.input_schema["additionalProperties"] is False
