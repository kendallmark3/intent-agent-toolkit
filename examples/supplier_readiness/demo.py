"""Reproducible Supplier Readiness demonstration.

Runs the real application in-process (same app factory, auth, tools and graph as the server)
with an ephemeral signing secret, invokes each of the agent's declared regression cases through
the HTTP API, and checks the unauthenticated boundary. Exits non-zero on any mismatch.

The cases live with the agent (src/iat/agents/supplier_readiness/regression_cases.json), so this
demo, the console, the smoke script and CI all check the same expectations.

    uv run python examples/supplier_readiness/demo.py
"""

from __future__ import annotations

import secrets
import sys

from fastapi.testclient import TestClient
from pydantic import SecretStr

from iat.agents.registry import default_agents
from iat.api.app import create_app
from iat.core.config import Settings
from iat.security.dev_tokens import issue_token
from iat.services.regression import evaluate

AGENT = "supplier-readiness"


def main() -> int:
    settings = Settings(
        jwt_secret=SecretStr(secrets.token_urlsafe(48)),
        log_level="WARNING",
        _env_file=None,  # type: ignore[call-arg]
    )
    headers = {"Authorization": f"Bearer {issue_token(settings, 'demo-user')}"}
    (agent,) = [a for a in default_agents() if a.key == AGENT]
    failures = 0
    with TestClient(create_app(settings)) as client:
        for case in agent.regression_cases:
            response = client.post(
                f"/v1/agents/{AGENT}/invoke", json={"message": case.message}, headers=headers
            )
            body = response.json()
            out = body["output"]
            passed, _ = evaluate(case.expect, out)
            passed = passed and response.status_code == 200
            failures += not passed
            steps = " → ".join(s["node"] for s in body["execution"]["steps"])
            print(f"[{'PASS' if passed else 'FAIL'}] {case.name}: {case.message}")
            print(f"       decision={out['decision']} supplier={out['supplier_id']} path={steps}")
            print(f"       {out['explanation']}")
        unauth = client.post(f"/v1/agents/{AGENT}/invoke", json={"message": "x"})
        ok = unauth.status_code == 401
        failures += not ok
        label = "PASS" if ok else "FAIL"
        print(f"[{label}] Unauthenticated request rejected with {unauth.status_code}")
    total = len(agent.regression_cases) + 1
    print(f"\n{total - failures}/{total} demo checks passed")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
