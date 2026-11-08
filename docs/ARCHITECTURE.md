# Architecture — Intent Agent Toolkit v0.1

## Shape

```
HTTP client
   │  Authorization: Bearer <JWT>     X-Request-ID (optional)
   ▼
┌──────────────────────────── api/ (FastAPI) ─────────────────────────────┐
│ request_context middleware → request id, log correlation                │
│ get_identity dependency    → TokenVerifier.verify() → Identity(sub,scope)│
│ routes: /health, /health/ready, /v1/agents, /v1/agents/{key}/invoke,     │
│         /v1/conversations, /v1/conversations/{id}                       │
│ exception handlers         → one error envelope, no internals leaked    │
└──────────────────────────────┬──────────────────────────────────────────┘
                               │ identity, message, request_id
                               ▼
┌──────────────────── services/runner.py  (AgentRunner) ──────────────────┐
│ transport-independent: no FastAPI imports                               │
│ resolves agent → checks conversation ownership → invokes graph →        │
│ validates output model → writes ExecutionRecord → stores turns          │
└──────────────┬───────────────────────────────────────────┬──────────────┘
               ▼                                           ▼
┌──── agents/ (LangGraph) ───────────────┐   ┌── services/conversations ───┐
│ supplier-readiness StateGraph          │   │ owner-scoped repository     │
│ identify → lookup → assess → explain   │   │ (in-memory in V1)           │
│ rules.py: deterministic decisions      │   └─────────────────────────────┘
│ narrator.py: prose only, can't decide  │
└──────────────┬─────────────────────────┘
               │ executor.invoke(agent, allowlist, tool, args, recorder)
               ▼
┌──── tools/ ────────────────────────────┐
│ ToolExecutor: registered? allowed?     │
│ input valid? output valid? → record    │
│ supplier_evidence_lookup (read-only)   │
└──────────────┬─────────────────────────┘
               ▼
     services/supplier_repository → data/suppliers.json (synthetic)
```

## Layers and rules

| Layer | Owns | May depend on |
|---|---|---|
| `api` | HTTP, auth extraction, error envelope, request ids | services, security, schemas |
| `services/runner` | executing an agent with identity + evidence | agents, tools, conversations |
| `agents` | LangGraph graphs and domain rules | tools (via executor), schemas |
| `tools` | tool contract, registry, governed execution | services (data access) |
| `security` | token verification, identity, scopes | core |
| `schemas` | Pydantic contracts for I/O and evidence | — |
| `core` | settings, logging, error taxonomy | — |

Agents never read data directly — they call tools through the executor, so every data access
is authorized and recorded. The runner is the only path to an agent.

## Reference agent: Supplier Readiness

1. **identify** — deterministic extraction of a supplier id (`SUP-001`) or capitalised name after
   the word "supplier". No guess when nothing is found.
2. **lookup** — calls `supplier_evidence_lookup` through the governed executor.
3. **assess** — `rules.evaluate_evidence` applies five required checks. Failed → `NOT_READY`;
   otherwise missing/unrecognised → `INSUFFICIENT_EVIDENCE`; otherwise `READY`. Not-found,
   ambiguous and tool-failure paths all fail closed to `INSUFFICIENT_EVIDENCE`.
4. **explain** — `Narrator` writes the explanation from the finished result. It receives the
   decision as input and returns text only, so a future LLM narrator cannot change outcomes.

Why LangGraph for a deterministic flow? The graph is the extension point: an LLM node (e.g. a
model-backed reference extractor or narrator) slots in as a node without changing the runner,
API, security or evidence model. V1 proves that wiring with zero model dependencies.

## Evidence per execution

`ExecutionRecord`: request id, execution id, agent, caller identity *hash*, every tool attempt
(tool, status, duration, error class), overall status, duration, error class. It is returned in
the API response and logged as one JSON line (`event: agent_execution`). Message content, raw
identity, tokens and secrets are never logged.

## Extension seams (deliberately unimplemented)

| Seam | V1 implementation | Future |
|---|---|---|
| `TokenVerifier` | `JwtVerifier` (HMAC, local issuer) | OIDC/JWKS, AgentCore Identity |
| `ConversationRepository` | in-memory | Postgres (Source B pattern) |
| `Tool.spec()` | JSON-Schema spec per tool | MCP adapter / governed registry (INTENT-002) |
| `Narrator` | `TemplateNarrator` | model-backed narrator behind a gateway |
| `AgentRunner.run` | called by FastAPI routes | AgentCore Runtime `/invocations` entrypoint |
