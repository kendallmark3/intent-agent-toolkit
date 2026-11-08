"""Agent regression cases: declared with the agent, runnable from the API, console, smoke and CI.

An expectation maps an output field to its expected value. A dotted key projects a list of
objects to the sorted values of one attribute, so ``"missing_evidence.check": [...]`` compares
the set of missing check names regardless of order or wording.
"""

from __future__ import annotations

import datetime as dt
import json
import time
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from iat import __version__
from iat.core.errors import IATError
from iat.schemas.api import RegressionCaseResult, RegressionReport
from iat.security.identity import Identity


class RegressionCase(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    name: str = Field(min_length=1, max_length=80)
    message: str = Field(min_length=1, max_length=2000)
    expect: dict[str, Any] = Field(min_length=1)


def load_cases(path: Path) -> tuple[RegressionCase, ...]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    return tuple(RegressionCase.model_validate(c) for c in raw["cases"])


def project(output: Mapping[str, Any], key: str) -> Any:
    field, _, attribute = key.partition(".")
    value = output.get(field)
    if not attribute:
        return value
    if not isinstance(value, list):
        return None
    return sorted(str(item.get(attribute)) for item in value if isinstance(item, Mapping))


def evaluate(expect: Mapping[str, Any], output: Mapping[str, Any]) -> tuple[bool, dict[str, Any]]:
    actual = {key: project(output, key) for key in expect}
    normalized = {k: sorted(v) if isinstance(v, list) else v for k, v in expect.items()}
    return actual == normalized, actual


def run_regression(
    runner: Any,
    agent_key: str,
    cases: tuple[RegressionCase, ...],
    identity: Identity,
    request_id: str | None,
) -> RegressionReport:
    started_at = dt.datetime.now(dt.UTC)
    results: list[RegressionCaseResult] = []
    for case in cases:
        began = time.perf_counter()
        try:
            outcome = runner.run(
                agent_key=agent_key, message=case.message, identity=identity, request_id=request_id
            )
        except IATError as exc:
            results.append(
                RegressionCaseResult(
                    name=case.name,
                    message=case.message,
                    passed=False,
                    expected=case.expect,
                    actual={},
                    execution_id=exc.execution_id,
                    error=exc.code.value,
                    duration_ms=round((time.perf_counter() - began) * 1000, 3),
                )
            )
            continue
        passed, actual = evaluate(case.expect, outcome.output.model_dump(mode="json"))
        results.append(
            RegressionCaseResult(
                name=case.name,
                message=case.message,
                passed=passed,
                expected=case.expect,
                actual=actual,
                execution_id=outcome.execution.execution_id,
                duration_ms=round((time.perf_counter() - began) * 1000, 3),
            )
        )
    passed_count = sum(r.passed for r in results)
    return RegressionReport(
        agent=agent_key,
        version=__version__,
        request_id=request_id,
        started_at=started_at,
        total=len(results),
        passed=passed_count,
        failed=len(results) - passed_count,
        cases=results,
    )
