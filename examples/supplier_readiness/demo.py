"""Reproducible Supplier Readiness demonstration.

Runs the real application in-process (same app factory, auth, tools and graph as the server),
with an ephemeral signing secret generated at runtime and a pinned assessment date, then
compares each result with expected.json. Exits non-zero on any mismatch.

    uv run python examples/supplier_readiness/demo.py
"""

from __future__ import annotations

import datetime as dt
import json
import secrets
import sys
from pathlib import Path

from fastapi.testclient import TestClient
from pydantic import SecretStr

from iat.api.app import create_app
from iat.core.config import Settings
from iat.security.dev_tokens import issue_token

HERE = Path(__file__).parent
EXPECTED = json.loads((HERE / "expected.json").read_text())


def main() -> int:
    settings = Settings(
        jwt_secret=SecretStr(secrets.token_urlsafe(48)),
        assessment_date=dt.date.fromisoformat(EXPECTED["as_of"]),
        log_level="WARNING",
        _env_file=None,  # type: ignore[call-arg]
    )
    headers = {"Authorization": f"Bearer {issue_token(settings, 'demo-user')}"}
    failures = 0
    with TestClient(create_app(settings)) as client:
        for case in EXPECTED["cases"]:
            response = client.post(
                "/v1/agents/supplier-readiness/invoke",
                json={"message": case["question"]},
                headers=headers,
            )
            body = response.json()
            out = body["output"]
            actual = {
                "supplier_id": out["supplier_id"],
                "decision": out["decision"],
                "missing_evidence": sorted(m["check"] for m in out["missing_evidence"]),
            }
            want = {k: case[k] for k in actual}
            status = "PASS" if (response.status_code == 200 and actual == want) else "FAIL"
            failures += status == "FAIL"
            print(f"[{status}] {case['question']}")
            print(f"       decision={out['decision']} supplier={out['supplier_id']}")
            print(f"       {out['explanation']}")
            tools = [f"{t['tool']}:{t['status']}" for t in body["execution"]["tools_invoked"]]
            print(f"       execution_id={body['execution']['execution_id']} tools={tools}")
        unauth = client.post("/v1/agents/supplier-readiness/invoke", json={"message": "x"})
        ok = unauth.status_code == 401
        failures += not ok
        label = "PASS" if ok else "FAIL"
        print(f"[{label}] Unauthenticated request rejected with {unauth.status_code}")
    print(
        f"\n{len(EXPECTED['cases']) + 1 - failures}/{len(EXPECTED['cases']) + 1} demo checks passed"
    )
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
