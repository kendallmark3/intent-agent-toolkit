# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

# Repository Rules
Read intent/current-feature.md first. It holds INTENT-001 plus appended deltas (INTENT-002, INTENT-003); full texts are in intent/INTENT-00N.md. Add new work as a delta appended to it; do not rewrite earlier intents.
Run hooks/pre-implement.sh before implementing. A PreToolUse hook (.claude/settings.json → hooks/pre-implement-hook.sh) blocks Edit/Write on non-Markdown files while the intent lacks an Outcome or Success/Evidence section.
Build the smallest useful delta, then let the human observe it and decide: continue or stop.
Always write tests. `make check` must pass (ruff, mypy --strict, bandit + pip-audit, pytest, intent gate).
Respect architecture: api → services/runner → agents → tools → services. Agents never read data directly; they call tools.
Never weaken security for a demo: no auth bypass, no caller-supplied user ids, no secrets or message content in logs.
Results docs (docs/INTENT-00N-RESULTS.md, docs/evidence/) record only checks that were actually run.

# Commands
Python ≥ 3.11, managed with uv.

```bash
make setup          # uv sync + create .env with a generated IAT_JWT_SECRET (never overwrites)
make run            # uv run iat-serve → http://127.0.0.1:8000/ui/ (console), /docs (OpenAPI)
make token          # dev bearer token signed with IAT_JWT_SECRET (uv run iat-token --sub <name>)
make check          # lint + typecheck + security + test + intent — the gate
make lint           # ruff check . && ruff format --check .
make typecheck      # mypy (strict, package iat)
make test           # pytest
make smoke [BASE_URL=...]   # scripts/smoke.py against a running service
make demo           # examples/supplier_readiness/demo.py

uv run pytest tests/test_supplier_agent.py::test_name   # single test
uv run ruff format .                                    # fix formatting
```

The service refuses to start without `IAT_JWT_SECRET`; there is no unauthenticated mode. Settings are `IAT_*` env vars (src/iat/core/config.py).

# Architecture
FastAPI service hosting LangGraph agents. Read docs/ARCHITECTURE.md for the full diagram; the points that span several files:

- **One path to an agent.** `api/routes.py` extracts `Identity` (JWT via `TokenVerifier`, scopes checked per route) and calls `services/runner.AgentRunner`, which has no FastAPI imports. The runner resolves the agent from `agents/registry.py`, enforces conversation ownership, invokes the compiled graph, validates the result against the agent's `output_model`, builds the `ExecutionRecord` (including the workflow `steps`), and stores turns.
- **Tool permission comes only from registration.** `AgentDefinition.allowed_tools` → `ToolPolicy`, built once in `create_app` (api/app.py) and frozen; granting an unregistered tool fails startup. Graph nodes get an `AgentToolGateway` via `config["configurable"]["tools"]` and call `invoke(tool_name, args)`. The gateway takes no agent name or permission list, so runtime input cannot widen access. `ToolExecutor` validates input/output with Pydantic and records every attempt.
- **Decisions are deterministic; prose cannot change them.** For Supplier Readiness (`agents/supplier_readiness/`), the graph is identify → lookup → assess → explain. `rules.py` decides (failed check beats missing evidence; unknown means missing, never satisfied; not-found/ambiguous/tool failure all fail closed to `INSUFFICIENT_EVIDENCE`). `narrator.py` only writes the explanation from a finished result. Any future LLM belongs in a node like the narrator, never in the decision.
- **Evidence and logging.** Each run logs one JSON `agent_execution` line with a keyed HMAC caller pseudonym (`security/pseudonym.py`); never raw identity, tokens or message content. Errors go through one envelope (`core/errors.py`) that does not leak internals.
- **Bounded memory.** `services/conversations.InMemoryConversationRepository` is owner-scoped and bounded (total, per-owner, turns, message size, idle TTL). Limits live in config.
- **Web console.** `web/static/` is served at `/ui/` with a strict CSP and uses the same authenticated `/v1/*` API. `POST /v1/agents/{key}/regression` runs the agent's `regression_cases.json` through the runner. The console, smoke script and CI container job all reuse those cases.
- **Adding an agent.** Follow docs/ADDING_AN_AGENT.md: read-only tool → frozen output schema → rules.py → graph.py → regression_cases.json → `AgentDefinition` in the registry → tests. Write tools need their own intent. Use only synthetic data (src/iat/data/).

# Tests
Tests are fully deterministic: no LLM, no network. tests/conftest.py pins `assessment_date` to 2026-11-08, uses a test-only JWT secret with `_env_file=None`, and provides `app`/`client` fixtures built with `create_app(settings)`. tests/pre-implement.test.sh tests the intent gate itself (run by `make intent`).
