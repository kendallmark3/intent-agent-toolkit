# Implementation Report — INTENT-001 (Progression 1)

**Date:** 2026-11-08 · **Version:** 0.1.0 · **Environment:** Linux x86_64, Python 3.13.18, uv 0.11.32

## What was built

A runnable FastAPI service that executes a LangGraph agent behind fail-closed JWT
authentication. The reference **Supplier Readiness** agent extracts a supplier reference,
retrieves evidence through a governed read-only tool, applies five deterministic readiness
rules, and returns a structured assessment (`READY` / `NOT_READY` / `INSUFFICIENT_EVIDENCE`)
with supporting evidence, missing evidence, explanation and execution id. Every run emits an
`ExecutionRecord` (request id, execution id, agent, hashed caller, tool attempts, status,
duration, error class). Execution is transport-independent (`AgentRunner`), so the same agent can
later be hosted by AgentCore Runtime.

Stack: fastapi 0.162.2, langgraph 1.2.20, langchain-core 1.7.6, pydantic 2.14.3, pyjwt 2.15.1,
uvicorn 0.54.0. Locked in `uv.lock`.

## What was reused

| Pattern | Source | Where in IAT |
|---|---|---|
| Keyed agent registry with descriptions; FastAPI service shape; uv project; fake-model testing; CI; multi-stage Docker | A — agent-service-toolkit | `agents/registry.py`, `api/`, `pyproject.toml`, `.github/workflows/ci.yml`, `Dockerfile` |
| JWT `sub`-bound identity; session ownership; request-correlated structured logs | B — fastapi-langgraph template | `security/identity.py`, `services/conversations.py`, `core/logging.py` |
| Minimal explicit `StateGraph` with named nodes and conditional edges | C — ai-agents-masterclass | `agents/supplier_readiness/graph.py` |
| Intent files, pre-implement gate, hooks, skills, agent roles | intent-drive-starter | `intent/`, `hooks/`, `skills/`, `agents/`, `templates/`, `.claude/` |

All patterns were re-implemented, not copied. Details: [SOURCE_DECISIONS.md](SOURCE_DECISIONS.md).

## What was deliberately excluded

Durable persistence (Postgres/migrations), user registration/login, rate limiting, Langfuse,
Prometheus/Grafana, long-term memory, model retry/fallback, streaming, Streamlit/voice/AG-UI,
multi-agent supervisors, LlamaGuard, MCP server, AWS dependencies. Each was either outside the
progression's required outcomes or needed infrastructure the intent said not to add; rationale per
item is in SOURCE_DECISIONS.md ("Deliberately not adopted").

## Evidence

All results below were produced by commands actually executed in this environment on 2026-11-08.
Raw output: [`docs/evidence/`](evidence/).

| Check | Command | Result |
|---|---|---|
| Unit/API tests | `uv run pytest` | **75 executed, 75 passed, 0 failed** (`evidence/test-results.xml`) |
| Coverage | `pytest --cov=iat` | **97%** of 850 statements (`evidence/coverage.txt`); uncovered: `main.py` entrypoint, `iat-token` CLI `main()` |
| Lint + format | `ruff check .` / `ruff format --check .` | pass |
| Types | `mypy` (strict) | pass — 32 source files, no issues |
| Static security | `bandit -r src` | no issues identified |
| Dependency vulnerabilities | `pip-audit` on exported runtime lock | no known vulnerabilities |
| Intent gate | `hooks/pre-implement.sh` + `tests/pre-implement.test.sh` | sufficient; 15/15 gate tests pass |
| Demo | `make demo` | **5/5** checks pass (`evidence/demo-output.txt`) |
| Live server | `uv run iat-serve` + curl | `/health` 200, `/health/ready` 200, `/openapi.json` 200, unauthenticated invoke 401, authenticated Acme invoke 200 READY; token absent from server log |
| Fail-closed startup | `iat-serve` without `IAT_JWT_SECRET` | refused to start: `jwt_secret Field required` |
| Docker build | `docker build .` | **not executed** — no Docker daemon in this environment. Dockerfile is unverified. |

**Security checks performed:** 9 invalid-token variants (wrong key, expired, wrong audience,
wrong issuer, missing `sub`, missing `exp`, malformed subject, `alg=none`, garbage); missing
token on every protected route; scope enforcement; caller-asserted `user_id` rejected; cross-user
read, append and list isolation with no existence leak; unregistered and unallowlisted tool
denial (denied tool never runs); tool input validation (5 cases); tool exception containment with
no detail leak; fail-closed on tool failure; log redaction; error envelopes with no internals or
input echo; request-id header injection.

## Known limitations

1. Conversations are in process memory: lost on restart, not shared across workers.
2. Local HMAC tokens only; no enterprise IdP, JWKS, or token revocation yet.
3. No rate limiting or quotas (expected at gateway/AgentCore layer).
4. Supplier reference extraction is rule-based: it needs the word "supplier" followed by a
   capitalised name, or an id like `SUP-001`. Lower-case names after "supplier" are not
   recognised, and the agent returns `INSUFFICIENT_EVIDENCE` rather than guessing.
5. No LLM in the loop. The graph and `Narrator` port are ready for one; none is exercised.
6. Single reference agent and single tool; no MCP adapter yet.
7. Docker image not built or scanned here; CI does not yet build it.
8. Evidence is logged to stdout only, with no trace backend.
9. The three source RepoIntent reports were not available; upstream code was inspected
   directly at the commits recorded in SOURCE_DECISIONS.md.

No maturity score is claimed. The next RepoIntent assessment decides the Radius.

## How to run it

```bash
uv sync
make check                       # full quality gate
make demo                        # reproducible demonstration, no configuration needed

cp .env.example .env             # set IAT_JWT_SECRET (≥32 chars)
make run                         # http://127.0.0.1:8000/docs
TOKEN=$(uv run iat-token --sub alice)
curl -s -X POST http://127.0.0.1:8000/v1/agents/supplier-readiness/invoke \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"message": "Can Supplier Acme be approved for onboarding?"}'
```

## Demonstration

`examples/supplier_readiness/demo.py` runs the real app factory in-process with an ephemeral
secret and `as_of = 2026-11-08`, and compares results with `expected.json`:

| Question | Expected decision | Missing evidence |
|---|---|---|
| Can Supplier Acme be approved for onboarding? | READY (SUP-001) | — |
| Is supplier Cobalt Ridge ready to onboard? | NOT_READY (SUP-002) | — (sanctions potential match; insurance expired 2025-03-31) |
| Can Supplier Lumen be approved? | INSUFFICIENT_EVIDENCE (SUP-003) | insurance, bank verification, code of conduct |
| Can Supplier Zenith be approved? | INSUFFICIENT_EVIDENCE (none) | supplier_record |
| (no token) | 401 | — |

## Next progression — recommendation for INTENT-002

**The smallest useful step is a governed MCP tool adapter.** Expose the existing `ToolRegistry`
through MCP, and allow a remote MCP tool to be registered as an IAT `Tool`. The executor's
allowlist, validation and evidence must apply to MCP tools exactly as they do to local ones.
Prove it by registering one remote read-only tool and repeating the denial and validation tests
over MCP. This builds on the `Tool.spec()` seam that already exists and matches the roadmap item
"Governed MCP and capability registry". Do not combine it with durable persistence. That belongs
in its own progression.

INTENT-002 has not been implemented.
