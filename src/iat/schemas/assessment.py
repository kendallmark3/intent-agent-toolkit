"""Structured output contract for the Supplier Readiness reference agent."""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field


class Decision(StrEnum):
    READY = "READY"
    NOT_READY = "NOT_READY"
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"


class CheckOutcome(StrEnum):
    SATISFIED = "SATISFIED"
    FAILED = "FAILED"


class EvidenceItem(BaseModel):
    """A piece of evidence that was actually found in the source data."""

    model_config = ConfigDict(frozen=True)

    check: str
    outcome: CheckOutcome
    detail: str
    source: str


class MissingEvidence(BaseModel):
    """A required piece of evidence that could not be found. Never filled with guesses."""

    model_config = ConfigDict(frozen=True)

    check: str
    reason: str


class SupplierAssessment(BaseModel):
    model_config = ConfigDict(frozen=True)

    supplier_id: str | None = Field(
        description="Resolved supplier id; null when the supplier could not be identified."
    )
    supplier_name: str | None = None
    decision: Decision
    supporting_evidence: list[EvidenceItem]
    missing_evidence: list[MissingEvidence]
    explanation: str
    execution_id: str
    as_of: str = Field(description="ISO date used for expiry checks.")
