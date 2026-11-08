"""Drive the web console in a real browser and capture evidence (INTENT-003).

Optional tooling — needs Playwright, which is not a project dependency:

    pip install playwright && playwright install chromium     # or set CHROME_PATH
    python scripts/console_check.py --token "$(uv run iat-token --sub you)"

Checks: console loads under its CSP with no browser errors; sign-in works; an example question
returns READY with a workflow trace; a no-supplier question skips the lookup node; the regression
suite passes. Writes screenshots and a JSON summary to --out.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any


def main() -> int:
    from playwright.sync_api import expect, sync_playwright

    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default="http://127.0.0.1:8000")
    parser.add_argument("--token", required=True)
    parser.add_argument("--out", default="console-evidence")
    args = parser.parse_args()
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    problems: list[str] = []
    summary: dict[str, Any] = {"base_url": args.base_url, "checks": {}}

    with sync_playwright() as p:
        launch: dict[str, Any] = {"headless": True}
        if os.environ.get("CHROME_PATH"):
            launch["executable_path"] = os.environ["CHROME_PATH"]
        browser = p.chromium.launch(**launch)
        page = browser.new_page(viewport={"width": 1280, "height": 900})
        page.on("console", lambda m: problems.append(m.text) if m.type == "error" else None)
        page.on("pageerror", lambda e: problems.append(str(e)))

        page.goto(args.base_url + "/ui/")
        expect(page.locator("#health-text")).to_contain_text("Service ready")
        page.fill("#token", args.token)
        page.click("#connect")
        expect(page.locator("#who")).to_contain_text("Signed in")
        summary["checks"]["sign_in"] = True

        page.locator("#examples button").first.click()
        page.click("#invoke")
        expect(page.locator("#decision")).to_have_text("READY")
        expect(page.locator("#workflow-run .node.ran")).to_have_count(4)
        summary["checks"]["ready_example"] = page.locator("#explanation").inner_text()
        page.screenshot(path=str(out / "01-ready.png"), full_page=True)

        page.fill("#message", "Can we onboard them?")
        page.click("#invoke")
        expect(page.locator("#decision")).to_have_text("INSUFFICIENT EVIDENCE")
        expect(page.locator("#workflow-run .node.skipped")).to_have_text("lookupskipped")
        summary["checks"]["lookup_skipped_without_supplier"] = True

        page.click("#run-regression")
        expect(page.locator("#reg-summary")).to_contain_text("passed", timeout=15000)
        summary["checks"]["regression"] = page.locator("#reg-summary").inner_text()
        page.screenshot(path=str(out / "02-regression.png"), full_page=True)

        page.click("#disconnect")
        expect(page.locator("#run")).to_be_hidden()
        summary["checks"]["sign_out_hides_console"] = True
        browser.close()

    summary["browser_errors"] = problems
    regression_ok = (
        summary["checks"]["regression"].split(" / ")[0]
        == summary["checks"]["regression"].split(" / ")[1].split(" ")[0]
    )
    summary["passed"] = not problems and regression_ok
    (out / "summary.json").write_text(json.dumps(summary, indent=2))
    print(json.dumps(summary, indent=2))
    return 0 if summary["passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
