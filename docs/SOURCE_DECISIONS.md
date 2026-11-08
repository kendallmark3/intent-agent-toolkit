# Source Decisions — INTENT-001

## Sources examined

| ID | Repository | Commit examined (2026-11-08) | License |
|---|---|---|---|
| A | [JoshuaC215/agent-service-toolkit](https://github.com/JoshuaC215/agent-service-toolkit) | `8bb3cd36264ca20e63a7c3a92bb8fcd383f09822` | MIT |
| B | [wassim249/fastapi-langgraph-agent-production-ready-template](https://github.com/wassim249/fastapi-langgraph-agent-production-ready-template) | `fe052a7c6acf692c05ca0e0a50c0ff2ffba448b7` | MIT |
| C | [coleam00/ai-agents-masterclass](https://github.com/coleam00/ai-agents-masterclass) | `1879176f4a000026786185841800fe404b9c12cb` | MIT |
| Base | [kendallmark3/intent-drive-starter](https://github.com/kendallmark3/intent-drive-starter) | `c0601821fe7e3e88ee2de2d3c1c7e88bb1bc7f15` | — |

**Missing evidence.** The three RepoIntent reports named in the intent
(`repo-intent/reports/{ai-agents-masterclass,agent-service-toolkit,fastapi-langgraph-template}/REPORT.md`)
were not present in the working environment or in
[kendallmark3/repo-intent](https://github.com/kendallmark3/repo-intent) at `fce683fefa5d8bdff06bfc3ce24a80e8de0597ff`
(its `reports/` holds only `multi-agent-supply-chain-system` and `clinical-evidence-coordinator`).
The assessment summaries in INTENT-001 were used as hypotheses, and the specific claims relied on
below were re-verified directly in upstream source at the commits listed.

No source file was copied verbatim. Patterns were re-implemented; attribution is in
[THIRD_PARTY_NOTICES.md](../THIRD_PARTY_NOTICES.md) and inline module docstrings.

## Decisions

### D1 — Service foundation: FastAPI app + agent registry + LangGraph → **Source A pattern**
- **Evidence:** A's `src/service/service.py` and `src/agents/agents.py` — keyed registry with
  descriptions, `/info`-style agent listing, FastAPI router, uv + `pyproject.toml`, fake model for tests.
- **Weakness addressed:** A loads every agent in a large registry (10+ agents, voice, Streamlit,
  AG-UI). IAT keeps the registry shape and adds a per-agent **tool allowlist** and a declared
  **output model** validated by the runner.
- **Simpler?** Yes — one agent, one tool, no streaming. Chosen.
- **Validated by:** `test_supplier_agent.py`, `test_runner_is_transport_independent`.

### D2 — Authentication → **Source B concept, new implementation, fail closed**
- **Evidence:** A `verify_bearer` returns early when `AUTH_SECRET` is unset (fail open) and is a
  single shared secret, not an identity. B uses JWTs with `sub` and session ownership
  (`app/utils/auth.py`, `get_current_session`).
- **Weakness addressed:** B uses `python-jose`; IAT uses **PyJWT** with an explicit algorithm
  allowlist, required `exp/iat/sub/iss/aud`, issuer + audience checks. Startup **fails** without a
  ≥32-char secret — there is no unauthenticated mode.
- **Simpler?** B's user registration/login/session tables are an identity platform; the intent
  forbids building one. IAT verifies tokens only and ships a CLI issuer for local use.
- **Validated by:** `test_security.py` (9 invalid-token variants, startup fail-closed tests).

### D3 — Authorization & conversation ownership → **new, closes Source A gap**
- **Evidence:** A `_handle_input` takes `user_id` and `thread_id` from the request body
  (`user_input.user_id or str(uuid4())`), so any caller can address any thread.
- **Decision:** identity only from verified `sub`; request models use `extra="forbid"` so a
  `user_id` field is rejected; conversation ids are server-generated; another user's
  conversation returns the same 404 as a nonexistent one. Scopes (`agents:invoke`,
  `conversations:read`) gate each route.
- **Validated by:** `test_cross_user_conversation_isolation`, `test_caller_cannot_assert_a_user_id`, scope tests.

### D4 — Agent graph style → **Source C pattern**
- **Evidence:** C `7-langgraph-agent/runnable.py` — explicit `StateGraph`, named nodes,
  `add_conditional_edges`. Clearest minimal form of the three.
- **Weakness addressed:** C has no tests, and its examples call live models. IAT's graph is
  deterministic, compiled once, with per-run dependencies passed via `RunnableConfig`.
- **Validated by:** extraction, ambiguity, not-found and tool-failure tests.

### D5 — Decisions by rules, not by a model → **new (intent: deterministic enforcement)**
- Readiness criteria are business rules, so they are code (`rules.py`). The `Narrator` port can
  only describe a decision. Unknown statuses and unreadable dates are *missing*, never satisfied.

### D6 — Tools → **new, MCP-shaped**
- **Evidence:** A and B bind LangChain tools directly to the model; neither has a deny path for
  unregistered tools or per-agent permissions; C's tools are example functions.
- **Decision:** `Tool` (name, description, read_only, Pydantic input/output) + `ToolExecutor`
  enforcing registered → allowed → input-valid → output-valid, recording every attempt.
  `Tool.spec()` emits MCP-compatible JSON Schema.
- **Validated by:** `test_tools.py`.

### D7 — Persistence → **deferred; seam kept**
- B's Postgres + migrations + pgvector memory, and A's SQLite/Postgres/Mongo checkpointers, solve
  problems V1 does not have. `ConversationRepository` protocol + in-memory implementation.
  LangGraph checkpointing not used — the conversation store is the source of truth.

### D8 — Observability → **Source B concept, stdlib implementation**
- **Evidence:** B uses structlog + `asgi-correlation-id` + Langfuse + Prometheus/Grafana.
- **Decision:** JSON logs via stdlib, request-id middleware with header validation, redaction
  of tokens/secret keys, identity hashed. Langfuse/Prometheus deferred (no infrastructure).
- **Validated by:** `test_logs_exclude_secrets_and_message_content`, formatter tests.

### D9 — Health → **new, honest readiness**
- **Evidence:** the intent records B's health endpoints as misleading.
- **Decision:** `/health` = liveness only; `/health/ready` reports the agent's real
  dependencies and returns 503 when any is missing.
- **Validated by:** `test_readiness_is_503_when_dependency_missing`.

### D10 — Error handling → **new**
- Single envelope `{error:{code,message,request_id,execution_id}}`. Validation errors list
  field names only (no input echo). Agent failures return `execution_id` for correlation, never
  exception text.

### D11 — Testing & CI → **Source A pattern**
- A's pytest layout, fake models and GitHub Actions are the strongest of the three (B and C have
  no tests). IAT CI runs lint, mypy --strict, bandit, pip-audit, pytest, intent gate and the demo.

### D12 — Container → **Source A pattern, slimmed**
- Multi-stage uv build, non-root user. Not built in this environment (no Docker daemon).

## Deliberately not adopted

| Capability | Source | Reason |
|---|---|---|
| Streamlit UI, voice, AG-UI | A | Not required; adds surface area |
| Multi-agent supervisors | A | Intent: no multi-agent without demonstrated benefit |
| LlamaGuard safeguard | A | Fails open in source; no model in V1 |
| User registration/login | B | Enterprise identity platform out of scope |
| Rate limiting (slowapi) | B | Deployment-dependent in source; gateway concern → see SECURITY.md |
| Model retries/fallback | B | No live model in V1 |
| Long-term memory (mem0/pgvector) | B | No requirement |
| n8n, RAG, local-LLM examples | C | Educational, not toolkit capabilities |
