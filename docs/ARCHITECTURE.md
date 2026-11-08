# Architecture — Intent Agent Toolkit v0.2

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
│ identify → lookup → assess → explain   │   │ in-memory, bounded (INT-002)│
│ rules.py: deterministic decisions      │   └─────────────────────────────┘
│ narrator.py: prose only, can't decide  │
└──────────────┬─────────────────────────┘
               │ gateway.invoke(tool, args)   (gateway bound to this agent by the runner)
               ▼
┌──── tools/ ────────────────────────────┐
│ ToolExecutor: registered? policy       │
│ permits agent? (from registrations)    │
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

Agents never read data directly — they call tools through an `AgentToolGateway` the runner binds
to the agent it resolved from the registry, so every data access is authorized and recorded. The
runner is the only path to an agent.

## Authority for tool access (INTENT-002)

`ToolPolicy` is built once at startup from `AgentDefinition.allowed_tools` (the registration),
validated against the tool registry (an unknown tool fails startup), and frozen. The gateway's
`invoke(tool_name, args)` takes no agent name and no permission list, so nothing an agent passes
at run time can widen its access. Scope: this protects against agent-controlled *inputs*
(arguments, state, future model output); it is not a sandbox against arbitrary Python running in
the same process.

## Conversation bounds (INTENT-002)

| Limit | Setting (`IAT_…`) | Default | At the limit |
|---|---|---|---|
| Total conversations | `MAX_CONVERSATIONS` | 1000 | evict least recently active |
| Per caller | `MAX_CONVERSATIONS_PER_OWNER` | 50 | evict that caller's least recently active |
| Turns per conversation | `MAX_TURNS_PER_CONVERSATION` | 40 | drop oldest turns, count in `dropped_turns` |
| Message size (chars) | `MAX_MESSAGE_CHARS` | 2000 (ceiling 8000) | 422, before any work |
| Idle lifetime (s) | `CONVERSATION_IDLE_TTL_SECONDS` | 3600 | removed; behaves as 404 |

Writes (`ensure`, `append`) refresh idle time; reads do not. Expiry is purged lazily, oldest first,
on every operation.

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

`ExecutionRecord`: request id, execution id, agent, caller *keyed pseudonym* (HMAC), every tool attempt
(tool, status, duration, error class), overall status, duration, error class. It is returned in
the API response and logged as one JSON line (`event: agent_execution`). Message content, raw
identity, tokens and secrets are never logged.

## Extension seams (deliberately unimplemented)

| Seam | V1 implementation | Future |
|---|---|---|
| `TokenVerifier` | `JwtVerifier` (HMAC, local issuer) | OIDC/JWKS, AgentCore Identity |
| `ConversationRepository` | in-memory, bounded by `ConversationLimits` | Postgres (Source B pattern) |
| `Tool.spec()` | JSON-Schema spec per tool | MCP adapter / governed registry (INTENT-002) |
| `Narrator` | `TemplateNarrator` | model-backed narrator behind a gateway |
| `AgentRunner.run` | called by FastAPI routes | AgentCore Runtime `/invocations` entrypoint |
