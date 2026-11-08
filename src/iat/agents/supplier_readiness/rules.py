"""Deterministic onboarding readiness rules.

These rules do not need model reasoning, so they are enforced in ordinary code (the intent's
"deterministic enforcement" principle). A model may later *explain* an assessment, but it can
never change the decision. Unknown or unparseable evidence is reported as missing — never
interpreted optimistically.
"""

from __future__ import annotations

import datetime as dt
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from typing import Any

from iat.schemas.assessment import CheckOutcome, Decision, EvidenceItem, MissingEvidence


@dataclass(frozen=True)
class RequiredCheck:
    key: str
    label: str
    evaluate: Callable[[Mapping[str, Any], dt.date], tuple[CheckOutcome | None, str]]


def _status_check(
    satisfied: set[str], failed: set[str], label: str
) -> Callable[[Mapping[str, Any], dt.date], tuple[CheckOutcome | None, str]]:
    def evaluate(record: Mapping[str, Any], _: dt.date) -> tuple[CheckOutcome | None, str]:
        status = str(record.get("status", "")).lower()
        if status in satisfied:
            return CheckOutcome.SATISFIED, f"{label}: {status}"
        if status in failed:
            return CheckOutcome.FAILED, f"{label}: {status}"
        return None, f"unrecognized status '{status or 'none'}'"

    return evaluate


def _insurance(record: Mapping[str, Any], as_of: dt.date) -> tuple[CheckOutcome | None, str]:
    if str(record.get("status", "")).lower() != "on_file":
        return None, "no certificate on file"
    try:
        expires = dt.date.fromisoformat(str(record.get("expires_on")))
    except ValueError:
        return None, "certificate expiry date missing or unreadable"
    if expires < as_of:
        return CheckOutcome.FAILED, f"Insurance certificate expired on {expires.isoformat()}"
    return CheckOutcome.SATISFIED, f"Insurance certificate valid until {expires.isoformat()}"


REQUIRED_CHECKS: tuple[RequiredCheck, ...] = (
    RequiredCheck(
        "tax_registration",
        "Tax registration",
        _status_check({"verified"}, {"failed", "rejected"}, "Tax registration"),
    ),
    RequiredCheck(
        "sanctions_screening",
        "Sanctions screening",
        _status_check({"clear"}, {"potential_match", "match"}, "Sanctions screening"),
    ),
    RequiredCheck("insurance_certificate", "Insurance certificate", _insurance),
    RequiredCheck(
        "bank_account_verification",
        "Bank account verification",
        _status_check({"verified"}, {"failed", "rejected"}, "Bank account verification"),
    ),
    RequiredCheck(
        "code_of_conduct",
        "Supplier code of conduct",
        _status_check({"signed"}, {"refused", "declined"}, "Code of conduct"),
    ),
)


@dataclass(frozen=True)
class RuleResult:
    decision: Decision
    supporting: list[EvidenceItem]
    missing: list[MissingEvidence]


def evaluate_evidence(evidence: Mapping[str, Mapping[str, Any]], as_of: dt.date) -> RuleResult:
    supporting: list[EvidenceItem] = []
    missing: list[MissingEvidence] = []
    for check in REQUIRED_CHECKS:
        record = evidence.get(check.key)
        if record is None:
            missing.append(
                MissingEvidence(check=check.key, reason=f"{check.label}: no record on file")
            )
            continue
        outcome, detail = check.evaluate(record, as_of)
        if outcome is None:
            missing.append(MissingEvidence(check=check.key, reason=f"{check.label}: {detail}"))
            continue
        supporting.append(
            EvidenceItem(
                check=check.key,
                outcome=outcome,
                detail=detail,
                source=str(record.get("source", "unspecified source")),
            )
        )

    if any(item.outcome is CheckOutcome.FAILED for item in supporting):
        decision = Decision.NOT_READY
    elif missing:
        decision = Decision.INSUFFICIENT_EVIDENCE
    else:
        decision = Decision.READY
    return RuleResult(decision=decision, supporting=supporting, missing=missing)
