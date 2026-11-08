"""Explanation port.

``Narrator`` turns a finished, rule-derived result into prose. It receives the decision as
input and returns text only, so even a future LLM-backed narrator cannot alter the decision
or add evidence. V1 ships a deterministic template narrator so no model is required.
"""

from __future__ import annotations

from typing import Protocol

from iat.schemas.assessment import CheckOutcome, Decision, EvidenceItem, MissingEvidence


class Narrator(Protocol):
    def explain(
        self,
        supplier_name: str | None,
        decision: Decision,
        supporting: list[EvidenceItem],
        missing: list[MissingEvidence],
    ) -> str: ...


class TemplateNarrator:
    def explain(
        self,
        supplier_name: str | None,
        decision: Decision,
        supporting: list[EvidenceItem],
        missing: list[MissingEvidence],
    ) -> str:
        who = supplier_name or "The supplier"
        failed = [e.detail for e in supporting if e.outcome is CheckOutcome.FAILED]
        satisfied = [e for e in supporting if e.outcome is CheckOutcome.SATISFIED]
        if decision is Decision.READY:
            return (
                f"{who} satisfies all {len(satisfied)} required onboarding checks "
                "based on the evidence on file."
            )
        if decision is Decision.NOT_READY:
            return f"{who} is not ready for onboarding: " + "; ".join(failed) + "."
        gaps = "; ".join(m.reason for m in missing)
        return (
            f"{who} cannot be assessed as ready because required evidence is missing: {gaps}. "
            "No missing evidence was assumed."
        )
