# Intent Agent Toolkit (IAT)

A small, secure, evidence-producing foundation for building and operating AI agents, built with
**Python · FastAPI · LangGraph**. Progression 001 of an Intent-Driven Engineering build
([intent](intent/INTENT-001.md)).

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
governed tool executor, deterministic decision rules, structured execution evidence, bounded memory, and 119
deterministic tests (no LLM, no network).

## Quick start

Requires Python ≥ 3.11 and [uv](https://docs.astral.sh/uv/).

```bash
uv sync                                   # install (locked by uv.lock)
make demo                                 # run the reproducible demo — no config needed
```

Run the server:

```bash
cp .env.example .env
python -c "import secrets; print(secrets.token_urlsafe(48))"   # paste into IAT_JWT_SECRET in .env
make run                                  # http://127.0.0.1:8000  (docs at /docs)
```

The service will not start without `IAT_JWT_SECRET` — there is no unauthenticated mode.

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
| `GET /v1/agents` | `agents:invoke` | list agents and their allowed tools |
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
  services/   AgentRunner (transport-independent), conversations, supplier data
  agents/     registry + supplier_readiness (LangGraph graph, rules, narrator)
  tools/      Tool contract, registry, governed executor, supplier_evidence_lookup
  security/   TokenVerifier/JwtVerifier, Identity, dev token CLI
  schemas/    Pydantic contracts for API, assessment, execution evidence
  core/       settings, JSON logging with redaction, error taxonomy
  data/       synthetic suppliers.json
tests/        119 tests + intent-gate shell tests
examples/     supplier_readiness demo, expected results, curl script
intent/       INTENT-001 and the current-feature intent (from intent-drive-starter)
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

## Known limitations

In-memory (bounded) conversations; local HMAC tokens (no IdP yet); no rate limiting; no LLM in the
decision path; Docker image defined but not yet built in CI. Full list in the
[INTENT-002 results](docs/INTENT-002-RESULTS.md#known-limitations).

## Working on it

This repo was scaffolded from [intent-drive-starter](https://github.com/kendallmark3/intent-drive-starter).
Read `intent/current-feature.md` first. In Claude Code sessions, `.claude/settings.json` runs
`hooks/pre-implement-hook.sh` before code edits (Markdown is never blocked); `make check` and CI
run the same gate. Append deltas rather than rewriting the intent.

MIT licensed. Patterns adapted from three MIT projects — see [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).
