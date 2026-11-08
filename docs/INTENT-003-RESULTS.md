# INTENT-003 Results — Run It: Web Console, Workflow Evidence, Runtime Proof

**Date:** 2026-11-08 · **Version:** 0.3.0 · **Baseline:** `cc01f2a` (v0.2)
**Inputs:** [intent/INTENT-003.md](../intent/INTENT-003.md); the v0.2 self-assessment and the
[independent v0.2 assessment](assessments/INTENT-002-INDEPENDENT.md), which was merged during this progression.

Everything below was executed. Local raw output is in [`docs/evidence/intent-003/`](evidence/intent-003/).
CI evidence is in GitHub Actions; links are in the CI table below.

## What was built

| Outcome | Where |
|---|---|
| Web console: sign in, run an agent from a form, see decision, evidence, **workflow path**, tool calls and execution record; run regression; download evidence | `/ui/` → `src/iat/web/static/` |
| Workflow trace in every execution record (nodes that ran, in order, with timings) | `ExecutionRecord.steps`, `AgentRunner` |
| Agents declare examples and regression cases; API runs them | `AgentDefinition`, `POST /v1/agents/{key}/regression` |
| Agent-neutral HTTP contract (independent finding C-026/027) | `InvokeResponse.output` |
| Smoke test for any deployment (stdlib only) | `scripts/smoke.py`, `make smoke` |
| Browser check of the console | `scripts/console_check.py`, `make console-check` |
| Container: pinned uv for lockfile rev 3, non-editable install, non-root, health check, docs off by default | `Dockerfile` |
| CI `container` job: build → run → health → non-root → smoke → browser → log leak check | `.github/workflows/ci.yml` |
| Dependabot for Docker, Actions, uv (independent finding C-034) | `.github/dependabot.yml` |
| VS Code: F5 runs service and opens the console; tasks for token, smoke, demo, tests, full check | `.vscode/` |
| First run in three commands: `make setup`, `make run`, `make token` | `Makefile`, `scripts/init_env.py` |
| Template path for the next agents | [docs/ADDING_AN_AGENT.md](ADDING_AN_AGENT.md) |

## Findings addressed

| Source | Finding | Resolution |
|---|---|---|
| Both v0.2 assessments | Container never built or run | Built, run and smoke-tested in CI on every push and PR |
| Both v0.2 assessments | README test count drift (C-036 / C-029) | Counts removed from README; the evidence files are the source |
| Independent C-026/027 | HTTP output typed to one agent | `output` is an object validated by each agent's own model; a second agent with a different output model works over HTTP |
| Independent C-033 | Docs on by default in the image | `IAT_DOCS_ENABLED=false` in the image; local development keeps docs |
| Independent C-034 | Base images tag-pinned | Dependabot added; **digest pinning deferred** (registry not reachable from the build environment) |
| Independent C-038 | Version wording drift | Corrected |
| Found while building | The INTENT-001 Dockerfile pinned `uv:0.5`, which predates lockfile revision 3, so the image had very likely never built | Pinned `uv:0.11`; build proven in CI |
| Found while building | `make token` failed where `$USER` is empty (containers, some CI) | Falls back to `developer` |

## Evidence — local

| Check | Result |
|---|---|
| `make check` (ruff, format, mypy strict, bandit, pip-audit, pytest, intent gate) | exit 0 |
| Tests | **146 passed**, 0 failed (`test-results.xml`); 26 new in `tests/test_console_and_runtime.py` |
| Coverage | **98%** of 1,106 statements |
| Demo (`make demo`, now runs the agent's declared cases) | **7/7** |
| Smoke (`scripts/smoke.py`, plain system Python) against a live server | **8/8** (`smoke-local.json`) |
| Installed wheel outside the source tree (the container's install path) | smoke **8/8** |
| Browser (`scripts/console_check.py`, headless Chrome) | sign-in, READY example with 4-node trace, `lookup` shown skipped for a question with no supplier, regression **6/6**, sign-out hides console; **0 browser errors (no CSP violations)** — `console/summary.json`, screenshots `01-ready.png`, `02-regression.png` |
| First run from nothing | `make env` created `.env` (mode 600, 64-character secret), a second run left it unchanged; `make token`, `make run`, `make smoke` 8/8 |
| Token in server log | **0** occurrences |

## Evidence — CI (GitHub Actions, commit `5522978`)

| Run | Result |
|---|---|
| [CI push run 42488571655](https://github.com/kendallmark3/intent-agent-toolkit/actions/runs/42488571655) | success (check × 3 Python versions, container) |
| [CI pull_request run 42488575513](https://github.com/kendallmark3/intent-agent-toolkit/actions/runs/42488575513) | success; container job 14:12:08–14:12:55 UTC |

Container job steps on the first CI run (`c372ab9`), all **success**: build image, run with an
ephemeral secret, Docker health check reaches `healthy`, runs as uid 10001, smoke test, console in a
real browser, logs contain no token or raw subject. The `container-evidence` artifact (smoke report,
browser screenshots, container log) is attached to each run. It could not be downloaded into the
build environment (artifact storage blocked by its network allowlist), so its contents are not
quoted here.

## Security review of the new surface

- The console is static and uses the same JWT API with the same scopes; no auth bypass and no
  token-minting endpoint were added.
- Strict CSP on `/ui/*` (`default-src 'none'; script-src 'self'; …; frame-ancestors 'none'`); no
  inline script or event handlers; no remote assets; tests enforce all three.
- All API data is rendered with `textContent`; a test checks the script has no HTML sinks.
- Every response gets `nosniff`, `X-Frame-Options: DENY` and `Referrer-Policy: no-referrer`; `/v1/*`
  gets `Cache-Control: no-store`.
- The token is held in `sessionStorage` for the tab and excluded from evidence downloads. Script
  running in the same origin could read it; the CSP is the control. For enterprise use, prefer the
  identity provider's browser flow (OIDC with PKCE).

## Public behaviour changes

| Change | Note |
|---|---|
| `InvokeResponse.output` is a generic object in the schema | JSON shape for supplier-readiness is unchanged |
| `ExecutionRecord.steps` added | additive |
| `AgentInfo` adds `workflow`, `examples`, `regression_cases` | additive |
| `POST /v1/agents/{key}/regression` | new, `agents:invoke` |
| `/` redirects to `/ui/` | new |
| Container serves no `/docs` unless `IAT_DOCS_ENABLED=true` | image default only |

## Radius position (self-reported, to be confirmed by assessment)

The one Radius 4 gap both v0.2 assessments named as the smallest next step (container build and
run) now has runtime evidence in CI. Still not evidenced: deployment to an environment, durable
state, rate limiting, a production identity provider, and digest-pinned images. No score is claimed
here; the next RepoIntent run decides it.

## Known limitations

- Local HMAC tokens pasted into the console; no IdP browser flow.
- In-memory, per-process conversations (bounded); lost on restart.
- No rate limiting in the service (expected at a gateway).
- Base images pinned by tag, not digest.
- No deployment; AWS is the next step.
- Supplier extraction needs "supplier" plus a capitalised name or an id.

## Recommended next progression

1. **INTENT-004: deploy to AWS** (the owner's stated direction): the container on a managed runtime
   behind HTTPS, the secret in a secrets manager, `make smoke BASE_URL=…` against it in CI, and an
   OIDC verifier behind the existing `TokenVerifier` seam. That closes the remaining Radius 4
   evidence gaps.
2. **Second agent from the template** (onboarding or credit card) via `docs/ADDING_AN_AGENT.md`, as
   its own intent. The agent-neutral contract and the generic console already support it.

INTENT-004 has not been started.
