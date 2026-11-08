# Intent Agent Toolkit (IAT)

A small, secure, evidence-producing foundation for building and operating AI agents, built with
**Python · FastAPI · LangGraph**, built in Intent-Driven Engineering progressions
([001](intent/INTENT-001.md) foundation · [002](intent/INTENT-002.md) hardening ·
[003](intent/INTENT-003.md) web console and runtime proof).

It ships one reference agent, **Supplier Readiness**, that answers questions like
*"Can Supplier Acme be approved for onboarding?"* with a structured, explainable decision drawn
only from the evidence on file:

```json
{ "supplier_id": "SUP-001", "decision": "READY",
  "supporting_evidence": [ ... 5 checks with sources ... ], "missing_evidence": [],
  "explanation": "Acme Industrial Supply satisfies all 5 required onboarding checks ...",
  "execution_id": "30060883620142f99d111cb6e3670803" }
```

Under that interaction: JWT authentication that fails closed, owner-scoped conversations, a
governed tool executor, deterministic decision rules, structured execution evidence with a workflow
trace, bounded memory, a web console, and a deterministic test suite (no LLM, no network). The
container image is built, run and smoke-tested in CI.

## Quick start (VS Code or any terminal)

Requires Python ≥ 3.11 and [uv](https://docs.astral.sh/uv/).

```bash
make setup      # install dependencies, create .env with a generated secret (never overwrites)
make run        # http://127.0.0.1:8000/ui/  — the web console (API docs at /docs)
make token      # in a second terminal: copy this token into the console's Access box
```

In **VS Code**: open the folder, accept the recommended extensions, then press **F5**
("IAT: Run service + console"). It runs setup, starts the service under the debugger and opens the
console. **Terminal → Run Task** has Token, Smoke test, Demo, Tests and Full check.

The service will not start without `IAT_JWT_SECRET`; there is no unauthenticated mode.

## Web console

`/ui/` is a single page served by the service. It uses the same authenticated API as any client.

- **Access:** paste a bearer token (`make token`). It is held for that browser tab only.
- **Run an agent:** pick the agent, type a question or click an example, and run it. The result shows
  the decision, explanation, supporting and missing evidence, the **workflow path** (which nodes
  ran, with timings, and which were skipped), tool calls, and the execution record.
- **Regression:** runs the agent's declared regression cases against the live service and shows
  pass/fail per case.
- **Download evidence:** a JSON file with the regression report and this session's runs (execution
  ids, workflow steps, keyed caller pseudonyms; never tokens).

## Proving a running deployment

```bash
make smoke                               # 8 checks against http://127.0.0.1:8000
make smoke BASE_URL=https://your-host    # same checks against any deployment
make console-check                       # optional: drives the console in a real browser (Playwright)
```

`scripts/smoke.py` uses only the Python standard library. It checks readiness, the auth boundary,
the console's security headers, one invocation per agent, and every agent's regression cases. CI
runs it, plus the browser check, against the built container.

## API usage

```bash
TOKEN=$(uv run iat-token --sub alice)     # local dev token signed with IAT_JWT_SECRET

curl -s http://127.0.0.1:8000/health/ready

curl -s -X POST http://127.0.0.1:8000/v1/agents/supplier-readiness/invoke \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -H "X-Request-ID: demo-request-0001" \
  -d '{"message": "Can Supplier Acme be approved for onboarding?"}'

# continue the same conversation (only its owner can)
curl -s -X POST http://127.0.0.1:8000/v1/agents/supplier-readiness/invoke \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"message": "What about Supplier Lumen?", "conversation_id": "<id from previous response>"}'

curl -s http://127.0.0.1:8000/v1/conversations -H "Authorization: Bearer $TOKEN"
```

| Endpoint | Auth | Purpose |
|---|---|---|
| `GET /health` | public | liveness |
| `GET /health/ready` | public | readiness of real dependencies (503 if not ready) |
| `GET /v1/agents` | `agents:invoke` | list agents, allowed tools, workflow, examples |
| `POST /v1/agents/{key}/regression` | `agents:invoke` | run the agent's regression cases |
| `POST /v1/agents/{key}/invoke` | `agents:invoke` | run an agent |
| `GET /v1/conversations` | `conversations:read` | caller's conversations |
| `GET /v1/conversations/{id}` | `conversations:read` | one conversation (owner only) |

Synthetic suppliers: **Acme** → READY, **Cobalt Ridge** → NOT_READY (sanctions match, expired
insurance), **Lumen** → INSUFFICIENT_EVIDENCE (three records missing). Anything else →
INSUFFICIENT_EVIDENCE. Set `IAT_ASSESSMENT_DATE` to pin expiry checks.

## Quality gate

```bash
make check     # ruff + format, mypy --strict, bandit, pip-audit, pytest, intent gate
make test      # tests only
```

CI (`.github/workflows/ci.yml`) runs the same gate plus the demo on Python 3.11–3.13.

## Layout

```
src/iat/
  api/        FastAPI app factory, routes, auth dependency, error envelope
  services/   AgentRunner (transport-independent), conversations, regression, supplier data
  agents/     registry + supplier_readiness (LangGraph graph, rules, narrator)
  tools/      Tool contract, registry, governed executor, supplier_evidence_lookup
  security/   TokenVerifier/JwtVerifier, Identity, dev token CLI
  schemas/    Pydantic contracts for API, assessment, execution evidence
  core/       settings, JSON logging with redaction, error taxonomy
  data/       synthetic suppliers.json
  web/        the console (static HTML/CSS/JS, served at /ui/)
tests/        pytest suite + intent-gate shell tests
scripts/      smoke.py (any deployment), console_check.py (browser), init_env.py
.vscode/      launch, tasks, recommended extensions
examples/     supplier_readiness demo (runs the agent's regression cases), curl script
intent/       INTENT-001…003, project intent, current-feature with deltas (from intent-drive-starter)
docs/         architecture, source decisions, security, AgentCore boundary, report, evidence
```

## Documentation

- [Architecture](docs/ARCHITECTURE.md)
- [Source decisions](docs/SOURCE_DECISIONS.md) — what was taken from which repository and why
- [Security model](docs/SECURITY.md) — guarantees, tests, enterprise IdP boundary
- [AgentCore future](docs/AGENTCORE_FUTURE.md)
- [Implementation report](docs/IMPLEMENTATION_REPORT.md) — INTENT-001 evidence
- [INTENT-001 baseline assessment](docs/assessments/INTENT-001-BASELINE.md) — RepoIntent self-assessment, preserved
- [INTENT-002 results](docs/INTENT-002-RESULTS.md) — hardening from that assessment
- [v0.2 assessment](docs/assessments/INTENT-002-REPOINTENT.md) — RepoIntent after INTENT-002, preserved
- [INTENT-003 results](docs/INTENT-003-RESULTS.md) — web console, workflow evidence, container proof
- [Adding an agent](docs/ADDING_AN_AGENT.md) — the template path for the next agents

## Known limitations

In-memory (bounded) conversations; local HMAC tokens (no IdP yet); no rate limiting; no LLM in the
decision path; no cloud deployment yet. Full list in the
[INTENT-003 results](docs/INTENT-003-RESULTS.md#known-limitations).

## Working on it

This repo was scaffolded from [intent-drive-starter](https://github.com/kendallmark3/intent-drive-starter).
Read `intent/current-feature.md` first. In Claude Code sessions, `.claude/settings.json` runs
`hooks/pre-implement-hook.sh` before code edits (Markdown is never blocked); `make check` and CI
run the same gate. Append deltas rather than rewriting the intent.

MIT licensed. Patterns adapted from three MIT projects — see [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).
