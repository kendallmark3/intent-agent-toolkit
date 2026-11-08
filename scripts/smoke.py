"""Smoke-test any running IAT deployment over HTTP. Standard library only.

    python scripts/smoke.py --base-url http://127.0.0.1:8000 --token "$(uv run iat-token --sub ci)"

Checks readiness, the auth boundary, the console's security headers, one invocation per agent
(with a workflow trace), and every agent's declared regression cases. Prints a JSON report and
optionally writes it to --out. Exits non-zero if any check fails. Used locally, in CI against the
built container, and later against cloud deployments.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
import urllib.error
import urllib.request
from typing import Any
from urllib.parse import urlparse


def call(
    base: str, method: str, path: str, token: str | None = None, body: dict[str, Any] | None = None
) -> tuple[int, dict[str, str], Any]:
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    data = json.dumps(body).encode() if body is not None else None
    request = urllib.request.Request(base + path, data=data, headers=headers, method=method)  # noqa: S310 - scheme validated in main()
    try:
        with urllib.request.urlopen(request, timeout=30) as response:  # noqa: S310 - scheme validated in main()
            raw = response.read()
            status, response_headers = response.status, dict(response.headers)
    except urllib.error.HTTPError as err:
        raw, status, response_headers = err.read(), err.code, dict(err.headers)
    try:
        payload = json.loads(raw) if raw else None
    except json.JSONDecodeError:
        payload = raw.decode(errors="replace")
    return status, {k.lower(): v for k, v in response_headers.items()}, payload


def wait_ready(base: str, seconds: float) -> bool:
    deadline = time.monotonic() + seconds
    while time.monotonic() < deadline:
        try:
            if call(base, "GET", "/health/ready")[0] == 200:
                return True
        except OSError:
            pass
        time.sleep(1)
    return False


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--base-url", default="http://127.0.0.1:8000")
    parser.add_argument("--token", required=True)
    parser.add_argument("--wait", type=float, default=30.0, help="seconds to wait for readiness")
    parser.add_argument("--out", help="write the JSON report to this file")
    args = parser.parse_args()
    base = args.base_url.rstrip("/")
    if urlparse(base).scheme not in {"http", "https"}:
        parser.error("--base-url must be http or https")

    checks: list[dict[str, Any]] = []

    def check(name: str, ok: bool, detail: Any = None) -> None:
        checks.append({"check": name, "passed": bool(ok), "detail": detail})

    check("service becomes ready", wait_ready(base, args.wait))
    status, _, health = call(base, "GET", "/health/ready")
    check("readiness reports all dependencies", status == 200, health)

    status, headers, _ = call(
        base, "POST", "/v1/agents/supplier-readiness/invoke", body={"message": "x"}
    )
    check(
        "unauthenticated invoke is rejected",
        status == 401 and headers.get("www-authenticate") == "Bearer",
        status,
    )

    status, headers, _ = call(base, "GET", "/ui/")
    csp = headers.get("content-security-policy", "")
    check(
        "console is served with a strict CSP", status == 200 and "script-src 'self'" in csp, status
    )
    check(
        "security headers present",
        headers.get("x-content-type-options") == "nosniff"
        and headers.get("x-frame-options") == "DENY",
    )

    status, _, agents = call(base, "GET", "/v1/agents", args.token)
    check("token can list agents", status == 200 and isinstance(agents, list) and agents, status)
    regressions: list[Any] = []
    for agent in agents if isinstance(agents, list) else []:
        key = agent["key"]
        if agent.get("examples"):
            status, _, result = call(
                base,
                "POST",
                f"/v1/agents/{key}/invoke",
                args.token,
                {"message": agent["examples"][0]},
            )
            steps = [s["node"] for s in result["execution"]["steps"]] if status == 200 else []
            check(
                f"{key}: example invocation completes with a workflow trace",
                status == 200 and bool(steps),
                steps,
            )
        status, _, report = call(base, "POST", f"/v1/agents/{key}/regression", args.token)
        ok = status == 200 and report["total"] > 0 and report["failed"] == 0
        check(
            f"{key}: regression suite",
            ok,
            f"{report['passed']}/{report['total']}" if status == 200 else status,
        )
        regressions.append(report)

    passed = all(c["passed"] for c in checks)
    result = {
        "kind": "iat-smoke",
        "base_url": base,
        "version": health.get("version") if isinstance(health, dict) else None,
        "at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "passed": passed,
        "checks": checks,
        "regressions": regressions,
    }
    text = json.dumps(result, indent=2, default=str)
    if args.out:
        with open(args.out, "w", encoding="utf-8") as fh:
            fh.write(text)
    for c in checks:
        print(
            ("PASS " if c["passed"] else "FAIL ")
            + c["check"]
            + ("" if c["detail"] is None else f"  [{c['detail']}]")
        )
    print(f"\n{sum(c['passed'] for c in checks)}/{len(checks)} smoke checks passed")
    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main())
