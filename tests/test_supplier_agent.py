"""Reference agent behaviour: decisions, structured output, and no fabrication."""

from __future__ import annotations

import datetime as dt
from collections.abc import Callable
from dataclasses import dataclass

import pytest
from fastapi.testclient import TestClient

from iat.agents.supplier_readiness.graph import extract_supplier_reference
from iat.agents.supplier_readiness.rules import REQUIRED_CHECKS, evaluate_evidence
from iat.core.config import DEFAULT_DATA_PATH
from iat.schemas.api import InvokeResponse
from iat.schemas.assessment import CheckOutcome, Decision, SupplierAssessment
from iat.schemas.execution import ExecutionRecord
from iat.security.identity import Identity
from iat.services.supplier_repository import SupplierRecord, SupplierRepository
from iat.tools.registry import ToolRegistry
from iat.tools.supplier_evidence import SupplierEvidenceLookupTool
from tests.conftest import AS_OF, INVOKE, build_runner

Auth = Callable[[str], dict[str, str]]
ALL_CHECKS = {c.key for c in REQUIRED_CHECKS}


@dataclass(frozen=True)
class Answer:
    output: SupplierAssessment
    execution: ExecutionRecord


def _ask(client: TestClient, auth: Auth, message: str) -> Answer:
    response = client.post(INVOKE, json={"message": message}, headers=auth("alice"))
    assert response.status_code == 200, response.text
    # Structured output validation: the envelope must satisfy the agent-neutral API contract,
    # and its output must satisfy this agent's own output model.
    envelope = InvokeResponse.model_validate(response.json())
    return Answer(SupplierAssessment.model_validate(envelope.output), envelope.execution)


def test_ready_supplier(client: TestClient, auth: Auth) -> None:
    result = _ask(client, auth, "Can Supplier Acme be approved for onboarding?")
    out = result.output
    assert out.decision is Decision.READY
    assert out.supplier_id == "SUP-001"
    assert out.missing_evidence == []
    assert {e.check for e in out.supporting_evidence} == ALL_CHECKS
    assert all(e.outcome is CheckOutcome.SATISFIED for e in out.supporting_evidence)
    assert out.execution_id == result.execution.execution_id
    assert out.as_of == AS_OF.isoformat()


def test_not_ready_supplier_reports_failures(client: TestClient, auth: Auth) -> None:
    out = _ask(client, auth, "Is supplier Cobalt Ridge ready to onboard?").output
    assert out.decision is Decision.NOT_READY
    failed = {e.check for e in out.supporting_evidence if e.outcome is CheckOutcome.FAILED}
    assert failed == {"sanctions_screening", "insurance_certificate"}
    assert "expired on 2025-03-31" in out.explanation


def test_missing_evidence_is_reported_not_invented(client: TestClient, auth: Auth) -> None:
    out = _ask(client, auth, "Can Supplier Lumen be approved?").output
    assert out.decision is Decision.INSUFFICIENT_EVIDENCE
    missing = {m.check for m in out.missing_evidence}
    present = {e.check for e in out.supporting_evidence}
    assert missing == {"insurance_certificate", "bank_account_verification", "code_of_conduct"}
    assert present == {"tax_registration", "sanctions_screening"}
    assert missing.isdisjoint(present)  # nothing is both "found" and "missing"
    assert "No missing evidence was assumed" in out.explanation


def test_unknown_supplier_is_insufficient_evidence(client: TestClient, auth: Auth) -> None:
    out = _ask(client, auth, "Can Supplier Zenith be approved?").output
    assert out.decision is Decision.INSUFFICIENT_EVIDENCE
    assert out.supplier_id is None
    assert out.supporting_evidence == []
    assert out.missing_evidence[0].check == "supplier_record"


def test_question_without_supplier_skips_tools(client: TestClient, auth: Auth) -> None:
    result = _ask(client, auth, "Can we onboard them?")
    assert result.output.decision is Decision.INSUFFICIENT_EVIDENCE
    assert result.output.missing_evidence[0].check == "supplier_identity"
    assert result.execution.tools_invoked == []


def test_supplier_id_lookup(client: TestClient, auth: Auth) -> None:
    assert _ask(client, auth, "Assess sup-001 please").output.supplier_id == "SUP-001"


@pytest.mark.parametrize(
    ("message", "expected"),
    [
        ("Can Supplier Acme be approved for onboarding?", "Acme"),
        ("Can supplier Acme Industrial Supply be onboarded?", "Acme Industrial Supply"),
        ("Is SUP-002 ready?", "SUP-002"),
        ("Check supplier Lumen.", "Lumen"),
        ("Can we onboard them?", None),
        ("supplier readiness please", None),
    ],
)
def test_reference_extraction(message: str, expected: str | None) -> None:
    assert extract_supplier_reference(message) == expected


def test_ambiguous_supplier_is_not_guessed() -> None:
    repo = SupplierRepository(
        [
            SupplierRecord(supplier_id="SUP-101", name="Delta Metals", evidence={}),
            SupplierRecord(supplier_id="SUP-102", name="Delta Plastics", evidence={}),
        ]
    )
    runner = build_runner(ToolRegistry([SupplierEvidenceLookupTool(repo)]))
    outcome = runner.run(
        agent_key="supplier-readiness",
        message="Can Supplier Delta be approved?",
        identity=Identity("alice"),
        request_id=None,
    )
    assert isinstance(outcome.output, SupplierAssessment)
    assert outcome.output.decision is Decision.INSUFFICIENT_EVIDENCE
    assert "SUP-101, SUP-102" in outcome.output.missing_evidence[0].reason


def test_runner_is_transport_independent() -> None:
    """The agent runs without FastAPI — the seam a future AgentCore entrypoint will use."""
    repo = SupplierRepository.from_json(DEFAULT_DATA_PATH)
    runner = build_runner(ToolRegistry([SupplierEvidenceLookupTool(repo)]))
    outcome = runner.run(
        agent_key="supplier-readiness",
        message="Can Supplier Acme be approved?",
        identity=Identity("svc-batch"),
        request_id="batch-0001",
    )
    assert outcome.execution.request_id == "batch-0001"
    assert outcome.execution.status.value == "COMPLETED"
    assert outcome.output.decision is Decision.READY  # type: ignore[attr-defined]


# --- deterministic rules ---------------------------------------------------------------

_COMPLETE = {
    "tax_registration": {"status": "verified", "source": "s"},
    "sanctions_screening": {"status": "clear", "source": "s"},
    "insurance_certificate": {"status": "on_file", "expires_on": "2026-11-08", "source": "s"},
    "bank_account_verification": {"status": "verified", "source": "s"},
    "code_of_conduct": {"status": "signed", "source": "s"},
}


def test_rules_expiry_boundary_is_inclusive() -> None:
    assert evaluate_evidence(_COMPLETE, AS_OF).decision is Decision.READY
    next_day = AS_OF + dt.timedelta(days=1)
    assert evaluate_evidence(_COMPLETE, next_day).decision is Decision.NOT_READY


def test_rules_unknown_status_is_missing_not_satisfied() -> None:
    evidence = {**_COMPLETE, "tax_registration": {"status": "pending_review", "source": "s"}}
    result = evaluate_evidence(evidence, AS_OF)
    assert result.decision is Decision.INSUFFICIENT_EVIDENCE
    assert result.missing[0].check == "tax_registration"


def test_rules_unreadable_expiry_is_missing() -> None:
    evidence = {**_COMPLETE, "insurance_certificate": {"status": "on_file", "expires_on": "soon"}}
    assert evaluate_evidence(evidence, AS_OF).decision is Decision.INSUFFICIENT_EVIDENCE


def test_rules_failure_outranks_missing() -> None:
    evidence = {"sanctions_screening": {"status": "match", "source": "s"}}
    assert evaluate_evidence(evidence, AS_OF).decision is Decision.NOT_READY


def test_rules_empty_evidence_is_insufficient() -> None:
    result = evaluate_evidence({}, AS_OF)
    assert result.decision is Decision.INSUFFICIENT_EVIDENCE
    assert result.supporting == []
    assert {m.check for m in result.missing} == ALL_CHECKS


def test_assessment_schema_rejects_unknown_decision() -> None:
    with pytest.raises(ValueError):
        SupplierAssessment.model_validate(
            {
                "supplier_id": "SUP-001",
                "decision": "PROBABLY_FINE",
                "supporting_evidence": [],
                "missing_evidence": [],
                "explanation": "x",
                "execution_id": "e",
                "as_of": "2026-11-08",
            }
        )
