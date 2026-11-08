<!--
PRESERVED ASSESSMENT — do not edit findings below this header.
Source: repo-intent/reports/intent-agent-toolkit/REPORT.md (RepoIntent @ fce683fe), checker PASS (55 claims, 126 citations, 0 errors).
Assessed commit: 8ecc05db90a7a3a47ee7be11497ed5dd763ba3ba. Citations are valid at that commit only; INTENT-002 changes line numbers.
Type: SELF-ASSESSMENT by static, read-only inspection, produced in the same session that authored the code. Not independent.
Tests, coverage and demo were not re-run during the assessment. They were reproduced afterwards at the same commit:
see docs/evidence/intent-002/baseline-reproduction.txt (75 passed, 97% coverage, demo 5/5, make check exit 0).
Copied verbatim into this repository on 2026-11-08 as the INTENT-002 baseline.
SHA-256 of the report body below (original REPORT.md): 8a5566167b3a39533fd57e91b0efeb97c0a149f50c793f65e273c57ecd3216e5
-->

# Repository Intelligence Report — intent-agent-toolkit

## Management Summary

- **Where it is today:** A working first version of a reusable agent toolkit, running one supplier-onboarding agent behind a sign-in check, with automated tests. Nothing is deployed; cloud work is deferred by plan [C-001, C-016, C-036, C-044].
- **Current credible radius:** Radius 3 of 5 (Engineering & Integration), with parts of Radius 4 in place [C-005, C-039, C-008].
- **What's working:** Sign-in is required and cannot be switched off [C-008, C-009]. Rules, not a model, decide, and evidence gaps are reported, not filled in [C-017, C-021]. Users see only their own conversations [C-012].
- **Attention areas:** Each agent declares its own tool permissions [C-024]. Conversations are kept in memory with no size limit found [C-014].
- **Questions to settle before setting direction:** Is this a demonstration reference or a path to an Abbott service [C-001]? Which identity provider and database would it use [C-007, C-013]?

## Architect Brief

- **What it is:** a Python/FastAPI service hosting LangGraph agents; the first progression of a toolkit aimed at enterprise deployment [C-001, C-002, C-016].
- **Shape:** one service; an app factory wires a token verifier, tool and agent registries, an in-memory conversation store, and a transport-independent runner [C-002, C-005, C-045].
- **Where the intelligence is:** deterministic: regex extraction, five coded rules, template explanation; no model client was found [C-017, C-018, C-019, C-020].
- **Implemented vs planned:**
  - *Implemented:* fail-closed JWT, scopes, owner-scoped conversations, governed tools, execution records, redacting logs, CI with typing and security scans [C-007, C-008, C-010, C-012, C-023, C-029, C-030, C-039].
  - *Defined, not built:* the container image [C-041].
  - *Seams only:* enterprise IdP, durable persistence, MCP, AgentCore [C-013, C-027, C-028, C-045].
- **Radius position:**

  | Radius | Status | Basis |
  |---|---|---|
  | 1 Intent & Discovery | EVIDENCED | Written intent with success criteria and boundaries [C-001, C-047]; project-level intent file is an empty template [C-049] |
  | 2 Prototype & Proof | EVIDENCED | Working agent, 75 test cases, committed run evidence [C-016, C-017, C-036, C-038] |
  | 3 Engineering & Integration | EVIDENCED | Layered design, typed contracts, CI, governed tools [C-005, C-023, C-039, C-040]; external integrations are seams, deferred by intent [C-044, C-013] |
  | 4 Delivery & Production | PARTIAL | Fail-closed auth, readiness probe, security scans, container definition [C-008, C-034, C-039, C-041]; durable state, rate limiting, built image and deployment not yet evidenced [C-013, C-043, C-052] |
  | 5 Enterprise Operation & Governance | NOT YET EVIDENCED | Governance building blocks present [C-023, C-029, C-046]; operational governance not found; intent frames enterprise use as direction, not exclusion [C-001] |

- **Attention areas:**
  1. Tool permissions come from each agent's code, not the agent registry [C-024, C-025].
  2. Conversation text is kept in memory; no retention bound found [C-013, C-014].
  3. Logged identity is an unsalted truncated hash: pseudonymous, not anonymous [C-057].
- **Biggest unknowns:**
  1. Whether the committed test and demo results reproduce [C-038].
  2. Whether the container builds and starts [C-041].
  3. Behaviour with multiple workers or a real identity provider [C-053].
- **Smallest next step outward (option for the owners):** a CI job that builds and runs the container. Proof: `/health/ready` returns 200 and an unauthenticated invoke returns 401 against the running image [C-041, C-034, C-009].

## 1. Repository Identity
- **Repository:** https://github.com/kendallmark3/intent-agent-toolkit
- **Commit SHA:** `8ecc05db90a7a3a47ee7be11497ed5dd763ba3ba` (2026-11-08, "INTENT-001: Intent Agent Toolkit foundation")
- **Analysis date:** 2026-11-08
- **Languages/frameworks observed:** Python ≥3.11, FastAPI, LangGraph, Pydantic v2, PyJWT; uv lockfile; GitHub Actions; Dockerfile.
- **Limitations:** Static, read-only inspection. No code was installed, built, or executed for this report; tests were read, not run. **Assessor independence:** this assessment was produced in the same session that authored the repository, so it is a self-assessment under RepoIntent rules, not an independent review. Starter-scaffold directories (`skills/`, `agents/`, `templates/`, `hooks/*.md`) were sampled, not read in full.

## 2. Executive Orientation
- A reusable foundation for building and operating AI agents, delivered as Progression 1 of a planned series [C-001].
- Shape: one FastAPI service, one LangGraph agent (`supplier-readiness`), one read-only tool, composed in an app factory [C-002, C-005, C-015].
- All intelligence is deterministic code today; the graph and a `Narrator` port are the stated extension points for model-backed steps [C-017, C-018, C-019].
- Security model fails closed: no secret, no startup; identity only from a verified token; conversations owner-scoped [C-008, C-011, C-012].
- Every run produces an execution record returned to the caller and logged as JSON [C-029, C-030].
- Most important uncertainty: the run evidence in `docs/evidence/` is a recorded artifact; it was not reproduced here [C-038].

## 3. Coverage & Confidence
- **Read in full:** all of `src/iat/` (application code and synthetic data), `pyproject.toml`, `Dockerfile`, `Makefile`, `.github/workflows/ci.yml`, `.gitignore`, `.env.example`, `hooks/hooks.json`, `intent/current-feature.md`, `intent/project-intent.md`.
- **Read in part:** `intent/INTENT-001.md` (purpose, boundaries, success criteria), `README.md`, all `docs/*.md`, test modules (names and key assertions), `docs/evidence/*`.
- **Not inspected:** `uv.lock` contents beyond presence, starter skill and agent prompt files, `templates/`.
- Confidence is high for code structure and control flow. There is no runtime evidence from this assessment.

## 4. System Purpose
- **Documented:** a reusable, evidence-based foundation for developing, evaluating, and operating AI agents, suitable for demonstrating architecture principles and evolving toward enterprise deployment [C-001].
- **Implemented:** a service that answers supplier-onboarding questions with `READY`, `NOT_READY`, or `INSUFFICIENT_EVIDENCE`, built from synthetic records [C-017, C-035].
- **Inferred:** the supplier agent is a reference vehicle for the toolkit's engineering patterns rather than a supplier product; the intent states this directly and the data is labelled synthetic [C-001, C-035].
- **Unknowns:** intended users and deployment target [C-052].

## 5. Entry Points & Execution Paths
| Entry point | How it is started | Evidence |
|---|---|---|
| HTTP service | `iat-serve` → `iat.main:run` → uvicorn factory `create_app` | [C-002] |
| Dev token CLI | `iat-token` console script | [C-003] |
| Demo | `make demo` → `examples/supplier_readiness/demo.py` (in-process app) | [C-038] |
| CI | GitHub Actions on push and pull request | [C-039] |

**Representative flow — invoke (traced):** `POST /v1/agents/{key}/invoke` → router-level `get_identity` verifies the bearer JWT → route checks `agents:invoke` scope → `AgentRunner.run` checks conversation ownership if an id is supplied → graph `identify` (regex) → `lookup` via `ToolExecutor.invoke` → `assess` (rules) → `explain` (template) → runner validates output model, writes execution record, appends turns → JSON response [C-006, C-009, C-010, C-012, C-016, C-023, C-029].

## 6. Component Map
| Component | Responsibility | Key files | Claims |
|---|---|---|---|
| API | routes, auth dependency, error envelope, request ids | `src/iat/api/` | C-005, C-006, C-032, C-033 |
| Runner | transport-independent execution and evidence | `src/iat/services/runner.py` | C-029, C-045 |
| Agents | registry and supplier-readiness graph, rules, narrator | `src/iat/agents/` | C-015, C-016, C-017, C-018 |
| Tools | tool contract, registry, governed executor, lookup tool | `src/iat/tools/` | C-023, C-024, C-026, C-027 |
| Security | token verification, identity, scopes, dev tokens | `src/iat/security/` | C-007, C-008, C-003 |
| Persistence | in-memory owner-scoped conversations; JSON supplier data | `src/iat/services/` | C-012, C-013, C-035 |
| Core | settings, logging, errors | `src/iat/core/` | C-008, C-030 |

## 7. Data Flow & Persistence
- **Inputs:** a message (1–2000 characters) and optional conversation id; a bearer token [C-011].
- **Transformations:** reference extraction, tool lookup, rule evaluation, template explanation [C-016, C-017, C-020].
- **Persistence:** conversations, including user message text and agent output, are held in a process-local dictionary [C-013, C-014]. Supplier data is read from a bundled JSON file at startup [C-035].
- **Outputs:** assessment plus execution record in the response; execution and tool records as JSON log lines [C-029, C-030].
- **Gaps:** no durable store; restart loses conversations, as the security document states [C-013].

## 8. External Integrations
| Integration | Evidence | Usage |
|---|---|---|
| Identity provider | `TokenVerifier` protocol; local HMAC verifier only | seam, not integrated [C-007] |
| Model provider | no client found | not integrated [C-019] |
| MCP | MCP-shaped tool spec; no MCP implementation found | seam [C-027, C-028] |
| AWS / AgentCore | documentation only; excluded by intent | out of scope for this progression [C-044, C-045] |

## 9. Interfaces / APIs
- **HTTP:** `GET /health`, `GET /health/ready`, `GET /v1/agents`, `POST /v1/agents/{agent_key}/invoke`, `GET /v1/conversations`, `GET /v1/conversations/{conversation_id}`; OpenAPI enabled by default [C-006].
- **CLI:** `iat-serve`, `iat-token` [C-002, C-003].
- **Library seams:** `TokenVerifier`, `ConversationRepository`, `Tool`, `Narrator`, `AgentRunner` [C-007, C-013, C-018, C-027, C-045].
- **Data contract:** synthetic `suppliers.json` [C-035].

## 10. Build / Test / Deploy / Operate
- **Build:** uv with a committed lockfile; hatchling package [C-002].
- **Test:** 52 test functions across five modules, 75 cases with parametrization, plus a shell test for the intent gate [C-036, C-037].
- **Quality gates:** ruff (including bandit-derived `S` rules), mypy strict, bandit, pip-audit, all run in CI on Python 3.11–3.13 [C-039, C-040].
- **Deploy:** a non-root multi-stage Dockerfile exists; the repository's own report states it was not built [C-041]. No deployment configuration was found [C-052].
- **Operate:** liveness and readiness endpoints; JSON logs with request correlation [C-030, C-032, C-034].

## 11. Security & Authentication Evidence
- **Authentication:** PyJWT with a configured algorithm allowlist (HMAC only), issuer and audience checks, and required `exp`, `iat`, `sub`, `iss`, `aud` [C-007, C-008].
- **Fail-closed configuration:** the signing secret is a required setting with a 32-character minimum [C-008].
- **Missing token:** 401 with `WWW-Authenticate: Bearer` [C-009].
- **Authorization:** scopes on invoke and conversation routes; `GET /v1/agents` requires authentication but no scope check was found [C-010].
- **Identity source:** request models forbid extra fields, so a caller cannot submit a user id [C-011].
- **Isolation:** another user's conversation returns the same 404 as a nonexistent one [C-012].
- **Tools:** registration, per-agent allowlist, input and output validation, exception containment [C-023, C-026].
- **Logging:** sensitive keys and bearer/JWT patterns redacted; identity logged as a truncated unsalted SHA-256 [C-030, C-057].
- **Not found:** rate limiting [C-043].
- These mechanisms describe what the code does; they do not establish that the system as deployed would be secure.

## 12. Domain / Business Concepts
- Supplier onboarding readiness with five checks: tax registration, sanctions screening, insurance certificate (expiry-aware), bank account verification, code of conduct [C-017].
- Decision precedence: any failed check → `NOT_READY`; otherwise any missing or unrecognized evidence → `INSUFFICIENT_EVIDENCE`; otherwise `READY` [C-017, C-022].
- A sanctions `potential_match` is treated as a failed check; no review or escalation state was found (inferred domain choice, not validated against a real policy) [C-054].

## 13. Alignment Gaps (Contradictions / Drift)
- **Edit-time intent gate:** the README says `hooks/pre-implement.sh` gates implementation. The hook configuration uses `${CLAUDE_PLUGIN_ROOT}`, and no plugin manifest or project hook settings were found, so the gate runs through `make intent` and CI rather than on edits [C-048].
- **Project intent file:** `intent/project-intent.md` is an empty template, while `intent/INTENT-001.md` carries the project purpose [C-049].
- **"Non-reversible" identity hash:** the schema describes the subject hash as non-reversible; an unsalted truncated hash of a predictable subject can be recovered by enumeration [C-057].
- **Tool permission source:** the docs describe a per-agent allowlist enforced by the executor; the executor enforces whatever allowlist the caller passes, and the agent registry's copy is descriptive [C-024, C-025].
- Documented security guarantees map to test functions that exist under the names given [C-055].

## 14. Important Unknowns
| Unknown | Why the repo cannot establish it | What would resolve it |
|---|---|---|
| Committed results reproduce | static assessment; artifacts are recorded output [C-038] | run `make check` and `make demo` at this commit |
| Container builds and runs [C-041] | no build evidence in repo | CI build and smoke run |
| Behaviour under multiple workers or a real IdP [C-053] | in-memory store is per-process; only HMAC verifier exists | multi-worker test; OIDC verifier integration test |
| Deployment and users [C-052] | no deployment config found | owner confirmation |
| Whether starter skills and agent prompts load in this repo [C-050] | depends on Claude Code configuration outside the repo | open a Claude Code session and list skills |

## 15. Claims Ledger

| ID | Claim | Class | Strength | Confidence | Evidence | Verification | Caveat |
|---|---|---|---|---|---|---|---|
| C-001 | The repository states its purpose as a reusable, evidence-based foundation for developing, evaluating and operating AI agents, intended to evolve toward enterprise deployment. | OBSERVED | DIRECT | HIGH | `intent/INTENT-001.md:L15#Build the first working version`; `intent/INTENT-001.md:L31#evolving toward enterprise deployment`; `intent/INTENT-001.md:L33#Success means` | VERIFIED | Documented intent. |
| C-002 | The primary runtime entry is the iat-serve console script, which runs uvicorn with the create_app factory. | OBSERVED | CORROBORATED | HIGH | `pyproject.toml:L29#iat-serve`; `src/iat/main.py:L10-L17#factory=True`; `src/iat/api/app.py:L58#def create_app`; `Dockerfile:L17#iat-serve` | VERIFIED | Re-verified via Dockerfile CMD and Makefile run target. |
| C-003 | A second console script, iat-token, issues locally signed development tokens. | OBSERVED | DIRECT | HIGH | `pyproject.toml:L30#iat-token`; `src/iat/security/dev_tokens.py#def issue_token` | VERIFIED | Developer tool. |
| C-004 | No HTTP route that issues tokens was found. | OBSERVED | CORROBORATED | HIGH | `src/iat/api/routes.py`; `src/iat/api/app.py:L93-L94#include_router` | VERIFIED | Search scope: full read of `src/iat/api/`; only health_router and api_router are included. |
| C-005 | create_app composes settings, verifier, supplier repository, tool registry, agent registry, in-memory conversations and runner into a container on app.state. | OBSERVED | DIRECT | HIGH | `src/iat/api/app.py:L58-L94#app.state.container` | VERIFIED | |
| C-006 | Two public health routes and four routes under /v1 are registered; the /v1 router carries a router-level identity dependency. | OBSERVED | DIRECT | HIGH | `src/iat/api/routes.py:L29#dependencies=[Depends(get_identity)]`; `src/iat/api/routes.py:L32-L53#readiness`; `src/iat/api/routes.py:L56-L107#get_conversation` | VERIFIED | |
| C-007 | Tokens are verified with PyJWT using a configured algorithm list, audience, issuer and required exp, iat, sub, iss, aud claims; the verifier sits behind a TokenVerifier protocol. | OBSERVED | DIRECT | HIGH | `src/iat/security/identity.py:L45-L75#options={"require"`; `pyproject.toml#pyjwt` | VERIFIED | Only an HMAC verifier is implemented. |
| C-008 | The signing secret is a required setting with a 32-character minimum, and only HMAC algorithms are accepted. | OBSERVED | CORROBORATED | HIGH | `src/iat/core/config.py:L30-L58#_secret_strength`; `tests/test_startup_and_health.py:L25#test_startup_fails_closed_without_secret` | VERIFIED | Test read, not run. |
| C-009 | A request whose bearer credential is missing or empty raises AuthenticationError, returned as 401 with a WWW-Authenticate header. | OBSERVED | CORROBORATED | HIGH | `src/iat/api/dependencies.py:L42-L49#Missing bearer token`; `src/iat/api/app.py:L111-L121#WWW-Authenticate`; `tests/test_security.py:L33#test_protected_endpoints_require_authentication` | VERIFIED | |
| C-010 | Invoke and conversation routes check scopes; no scope check was found on GET /v1/agents, which requires authentication only. | OBSERVED | CORROBORATED | HIGH | `src/iat/api/routes.py:L56-L58#list_agents`; `src/iat/api/routes.py:L74#SCOPE_INVOKE`; `src/iat/api/routes.py:L94#SCOPE_READ_CONVERSATIONS`; `src/iat/api/routes.py:L106#SCOPE_READ_CONVERSATIONS` | VERIFIED | Search scope: full read of `src/iat/api/routes.py`. |
| C-011 | The invoke request model forbids extra fields and accepts only message and conversation_id; the runner takes identity from the dependency. | OBSERVED | CORROBORATED | HIGH | `src/iat/schemas/api.py:L14-L23#extra="forbid"`; `src/iat/api/routes.py:L67-L81#identity=identity`; `tests/test_security.py:L120#test_caller_cannot_assert_a_user_id` | VERIFIED | |
| C-012 | Conversation ids are server-generated, and access to a conversation owned by another subject raises the same NotFoundError as a missing one. | OBSERVED | CORROBORATED | HIGH | `src/iat/services/conversations.py:L49#uuid.uuid4().hex`; `src/iat/services/conversations.py:L59-L62#conv.owner != identity.subject`; `tests/test_security.py:L127#test_cross_user_conversation_isolation` | VERIFIED | |
| C-013 | Conversations are held in a process-local dictionary behind a ConversationRepository protocol; the security document states they are lost on restart and per-process. | OBSERVED | CORROBORATED | HIGH | `src/iat/services/conversations.py:L7#V1 keeps conversations in process memory`; `src/iat/services/conversations.py:L43-L45#self._items`; `docs/SECURITY.md:L49#In-memory conversations` | VERIFIED | |
| C-014 | No cap, eviction or retention limit on stored conversations was found; turns store the user message text and agent output. | OBSERVED | CORROBORATED | MEDIUM | `src/iat/services/conversations.py:L43-L62#InMemoryConversationRepository`; `src/iat/services/runner.py:L109-L122#turn("user", message)` | VERIFIED | Search scope: full read of `conversations.py` and `runner.py`; grep for max, limit, evict in `src/`. |
| C-015 | One agent, supplier-readiness, is registered with an allowlist and a declared output model. | OBSERVED | DIRECT | HIGH | `src/iat/agents/registry.py:L48-L61#output_model=SupplierAssessment` | VERIFIED | |
| C-016 | The agent is a LangGraph StateGraph: identify, conditional route to lookup or assess, then assess, explain, END; compiled once. | OBSERVED | DIRECT | HIGH | `src/iat/agents/supplier_readiness/graph.py:L62-L147#add_conditional_edges` | VERIFIED | |
| C-017 | Readiness is decided by five coded checks with precedence FAILED, then missing, then READY. | OBSERVED | DIRECT | HIGH | `src/iat/agents/supplier_readiness/rules.py:L51-L74#REQUIRED_CHECKS`; `src/iat/agents/supplier_readiness/rules.py:L107-L113#Decision.NOT_READY` | VERIFIED | |
| C-018 | The explanation port receives the decision as input and returns text; the assessment's decision field is taken from graph state. | OBSERVED | DIRECT | HIGH | `src/iat/agents/supplier_readiness/narrator.py:L15-L25#class Narrator`; `src/iat/agents/supplier_readiness/graph.py:L121-L135#decision=state["decision"]` | VERIFIED | |
| C-019 | No model provider client or LLM call was found in the application source or declared dependencies. | OBSERVED | CORROBORATED | HIGH | `pyproject.toml:L8-L15#dependencies`; `src/iat/agents/supplier_readiness/narrator.py:L25#class TemplateNarrator` | VERIFIED | Search scope: case-insensitive grep for openai, anthropic, bedrock, boto3, ChatModel, llm across `src/` and `pyproject.toml`; only docstring mentions found. langchain-core is a transitive dependency of langgraph. |
| C-020 | Supplier references are extracted by regular expression: an id like SUP-001, or a capitalised token after the word supplier. | OBSERVED | DIRECT | HIGH | `src/iat/agents/supplier_readiness/graph.py:L33-L55#_SUPPLIER_NAME_RE` | VERIFIED | Lower-case names after "supplier" are not matched; documented as a limitation. |
| C-021 | Missing reference, non-OK lookup, not-found and ambiguous matches all produce INSUFFICIENT_EVIDENCE with a stated missing item. | OBSERVED | CORROBORATED | HIGH | `src/iat/agents/supplier_readiness/graph.py:L86-L111#insufficient`; `tests/test_tools.py:L120#test_agent_fails_closed_when_tool_fails`; `tests/test_supplier_agent.py:L100#test_ambiguous_supplier_is_not_guessed` | VERIFIED | |
| C-022 | Unrecognized statuses and unreadable expiry dates are classified as missing evidence. | OBSERVED | CORROBORATED | HIGH | `src/iat/agents/supplier_readiness/rules.py:L35#unrecognized status`; `src/iat/agents/supplier_readiness/rules.py:L40-L46#unreadable`; `tests/test_supplier_agent.py:L164#test_rules_unknown_status_is_missing_not_satisfied` | VERIFIED | |
| C-023 | ToolExecutor checks registration, allowlist, input model and output model in that order, records every attempt, and contains tool exceptions as a structured ERROR result. | OBSERVED | CORROBORATED | HIGH | `src/iat/tools/registry.py:L66-L135#_invoke`; `tests/test_tools.py:L81#test_unregistered_tool_is_denied`; `tests/test_tools.py:L87#test_registered_but_unauthorized_tool_is_denied` | VERIFIED | |
| C-024 | The allowlist is an argument to ToolExecutor.invoke supplied by the caller; the supplier graph passes its own ALLOWED_TOOLS constant. | OBSERVED | DIRECT | HIGH | `src/iat/tools/registry.py:L66-L76#allowed_tools`; `src/iat/tools/registry.py:L107#if tool_name not in allowed_tools`; `src/iat/agents/supplier_readiness/graph.py:L31#ALLOWED_TOOLS`; `src/iat/agents/supplier_readiness/graph.py:L72-L78#allowed_tools=ALLOWED_TOOLS` | VERIFIED | |
| C-025 | Tool permissions are declared by each agent's code; the registry's allowed_tools is populated from the same constant, so the two agree today; the executor checks the caller-supplied set. | INFERRED | CORROBORATED | MEDIUM | `src/iat/agents/registry.py:L23-L33#allowed_tools`; `src/iat/agents/registry.py:L48-L61#supplier.ALLOWED_TOOLS` | VERIFIED | Derived from C-024. A future agent could pass a broader set without registry change. |
| C-026 | The single tool is read-only and validates input with extra fields forbidden, a length limit and a character pattern; ambiguous matches return candidates. | OBSERVED | DIRECT | HIGH | `src/iat/tools/supplier_evidence.py:L13-L55#ambiguous`; `tests/test_tools.py:L105#test_tool_inputs_are_validated` | VERIFIED | |
| C-027 | Tool.spec emits name, description, read_only and the input JSON Schema, which is the shape an MCP tool listing uses. | OBSERVED | DIRECT | HIGH | `src/iat/tools/base.py:L22-L46#input_schema`; `tests/test_tools.py:L144#test_tool_spec_is_mcp_shaped` | VERIFIED | MCP compatibility is a design claim, not tested against an MCP client. |
| C-028 | No MCP server or client implementation was found. | OBSERVED | CORROBORATED | HIGH | `pyproject.toml:L8-L15#dependencies` | VERIFIED | Search scope: grep for mcp in `src/` and `pyproject.toml`; docstrings only. |
| C-029 | Each run produces an ExecutionRecord (request id, execution id, agent, subject hash, tool attempts, status, duration, error class), logged and returned in the response. | OBSERVED | CORROBORATED | HIGH | `src/iat/schemas/execution.py:L29-L37#class ExecutionRecord`; `src/iat/services/runner.py:L69-L82#agent_execution`; `src/iat/api/routes.py:L82-L89#"execution"` | VERIFIED | |
| C-030 | Logs are JSON; sensitive keys and bearer or JWT patterns are redacted. | OBSERVED | CORROBORATED | HIGH | `src/iat/core/logging.py:L19-L44#redact_value`; `src/iat/core/logging.py:L46#class JsonFormatter`; `tests/test_errors_and_evidence.py:L140#test_logs_exclude_secrets_and_message_content` | VERIFIED | Redaction is pattern-based. |
| C-031 | The runner's execution log line carries the execution record only; message text is not part of it. | OBSERVED | DIRECT | HIGH | `src/iat/services/runner.py:L80-L81#extra={"execution"` | VERIFIED | Applies to runner and executor log calls read; other log calls were not exhaustively traced. |
| C-032 | X-Request-ID is accepted only when it matches a safe pattern; otherwise a new id is generated; it is echoed in the response header. | OBSERVED | CORROBORATED | HIGH | `src/iat/api/app.py:L34#_SAFE_REQUEST_ID`; `src/iat/api/app.py:L96-L109#request_context`; `tests/test_errors_and_evidence.py:L122#test_unsafe_request_id_is_replaced` | VERIFIED | |
| C-033 | Errors use one envelope; validation errors report field names; unexpected exceptions return a generic 500. | OBSERVED | CORROBORATED | HIGH | `src/iat/api/app.py:L111-L139#Internal server error`; `tests/test_errors_and_evidence.py:L63#test_agent_failure_returns_safe_envelope` | VERIFIED | |
| C-034 | /health is a static liveness response; /health/ready reports three checks from startup-loaded state and returns 503 when any fails. | OBSERVED | CORROBORATED | HIGH | `src/iat/api/routes.py:L32-L53#HTTP_503_SERVICE_UNAVAILABLE`; `tests/test_startup_and_health.py:L57#test_readiness_is_503_when_dependency_missing` | VERIFIED | Checks reflect in-process state; there are no external dependencies to probe. |
| C-035 | Supplier data is a bundled JSON file of three records labelled synthetic. | OBSERVED | DIRECT | HIGH | `src/iat/data/suppliers.json:L2#SYNTHETIC DATA`; `src/iat/data/suppliers.json:L29#SUP-003` | VERIFIED | |
| C-036 | The suite has 52 test functions in five modules; the committed JUnit result records 75 cases with 0 failures. | OBSERVED | CORROBORATED | MEDIUM | `tests/test_supplier_agent.py#def test_`; `tests/test_security.py#def test_`; `docs/evidence/test-results.xml#tests="75"`; `docs/evidence/test-results.xml#failures="0"` | QUALIFIED | Count of 75 includes parametrized cases; result is a committed artifact, not reproduced here. |
| C-037 | Tests target the security properties documented: token validation variants, scope checks, cross-user isolation, tool denial and log content. | OBSERVED | CORROBORATED | HIGH | `tests/test_security.py:L70#test_invalid_tokens_are_rejected`; `tests/test_security.py:L108#test_scope_is_enforced_for_invoke`; `tests/test_security.py:L127#test_cross_user_conversation_isolation`; `tests/test_errors_and_evidence.py:L140#test_logs_exclude_secrets_and_message_content` | VERIFIED | Tests read, not run. |
| C-038 | The repository contains recorded output of a make check run (exit 0), a 97% coverage report and a 5/5 demo run. | OBSERVED | DIRECT | MEDIUM | `docs/evidence/check-output.txt:L39#make_check_exit=0`; `docs/evidence/coverage.txt:L40#97%`; `docs/evidence/demo-output.txt:L20#5/5 demo checks passed` | QUALIFIED | Recorded artifacts; this assessment did not reproduce them. |
| C-039 | CI runs on push and pull request with read-only permissions across Python 3.11–3.13: lint, type check, security scan, tests, intent gate and demo. | OBSERVED | DIRECT | HIGH | `.github/workflows/ci.yml:L2#on: [push, pull_request]`; `.github/workflows/ci.yml:L4-L5#contents: read`; `.github/workflows/ci.yml:L12-L30#make demo`; `Makefile:L28#check:` | VERIFIED | CI outcome is outside the repository. |
| C-040 | mypy runs in strict mode and ruff includes bandit-derived S rules. | OBSERVED | DIRECT | HIGH | `pyproject.toml:L55#strict = true`; `pyproject.toml:L48#"S"` | VERIFIED | |
| C-041 | A multi-stage Dockerfile runs as a non-root user on port 8000; the implementation report states the image was not built. | OBSERVED | CORROBORATED | HIGH | `Dockerfile:L1-L17#USER iat`; `docs/IMPLEMENTATION_REPORT.md:L55#not executed` | VERIFIED | Build status is documented, not observed. |
| C-042 | Secrets are externalized: .env is git-ignored and the example file leaves the secret empty. | OBSERVED | CORROBORATED | HIGH | `.gitignore:L5-L7#.env.example`; `.env.example:L4#IAT_JWT_SECRET=`; `src/iat/core/config.py:L23#env_prefix="IAT_"` | VERIFIED | Git history beyond this shallow commit was not inspected. |
| C-043 | No rate limiting was found in the application; the security document lists it as a known limitation. | OBSERVED | CORROBORATED | HIGH | `docs/SECURITY.md:L46#No rate limiting` | VERIFIED | Search scope: grep for rate and limit in `src/` (Python files); a gateway outside the repository could provide it. |
| C-044 | The intent excludes AWS deployment and AWS dependencies from this progression. | OBSERVED | DIRECT | HIGH | `intent/INTENT-001.md:L406-L408#Do not deploy to AWS`; `intent/current-feature.md:L27#No AWS deployment` | VERIFIED | |
| C-045 | No web framework import was found in the runner; a test runs the agent without FastAPI; AgentCore integration is documented as a thin adapter over the runner. | OBSERVED | CORROBORATED | HIGH | `src/iat/services/runner.py:L9-L25#from iat.tools.registry`; `tests/test_supplier_agent.py:L125#test_runner_is_transport_independent`; `docs/AGENTCORE_FUTURE.md:L20#AgentRunner.run()` | VERIFIED | Search scope: import block of `runner.py`; AgentCore adapter not implemented. |
| C-046 | Source attribution is recorded: three MIT license notices and the upstream commit SHAs examined. | OBSERVED | DIRECT | HIGH | `THIRD_PARTY_NOTICES.md:L5-L60#MIT License`; `docs/SOURCE_DECISIONS.md:L7-L9#1879176f4a000026786185841800fe404b9c12cb` | VERIFIED | |
| C-047 | The intent defines functional, security, engineering and evidence success criteria and states that a Radius 4 score is a desired outcome to be demonstrated; the implementation report defers the score to the next RepoIntent assessment. | OBSERVED | DIRECT | HIGH | `intent/INTENT-001.md:L442-L479#A Radius 4 score is a desired`; `docs/IMPLEMENTATION_REPORT.md:L80#decides the Radius` | VERIFIED | |
| C-048 | The hook configuration references CLAUDE_PLUGIN_ROOT; no plugin manifest or project hook settings were found, while the README says the pre-implement script gates implementation. | OBSERVED | CORROBORATED | MEDIUM | `hooks/hooks.json:L9#CLAUDE_PLUGIN_ROOT`; `README.md:L118#gates implementation`; `Makefile#bash hooks/pre-implement.sh` | VERIFIED | Search scope: find for plugin.json and listing of `.claude/` (contains only CLAUDE.md). The gate runs via make intent and CI. |
| C-049 | The project-level intent file is an unfilled template; the project purpose lives in INTENT-001. | OBSERVED | DIRECT | HIGH | `intent/project-intent.md:L1-L4#Purpose:` | VERIFIED | |
| C-050 | Whether the starter skills and agent prompt directories are loaded by Claude Code in this repository cannot be established from the repository. | UNKNOWN | INSUFFICIENT | LOW | | QUALIFIED | Resolved by listing skills in a Claude Code session opened in the repo. |
| C-052 | Whether the service is deployed anywhere, and for whom, cannot be established; no deployment configuration beyond the Dockerfile was found. | UNKNOWN | INSUFFICIENT | MEDIUM | | QUALIFIED | Resolved by owner confirmation. |
| C-053 | Behaviour with multiple worker processes or a production identity provider cannot be established; the store is per-process and only an HMAC verifier exists. | UNKNOWN | INSUFFICIENT | MEDIUM | | QUALIFIED | Resolved by a multi-worker test and an OIDC verifier integration test. |
| C-054 | A sanctions potential_match is treated as a failed check, and no review or escalation decision state was found. | INFERRED | CORROBORATED | MEDIUM | `src/iat/agents/supplier_readiness/rules.py:L58-L62#potential_match`; `src/iat/schemas/assessment.py#class Decision` | QUALIFIED | Search scope: full read of `rules.py`, `graph.py`, `schemas/assessment.py`. Appropriate handling depends on a real onboarding policy, which the synthetic scope does not define. |
| C-055 | The security document's guarantee table names tests that exist in the suite under those names. | OBSERVED | CORROBORATED | HIGH | `docs/SECURITY.md#test_cross_user_conversation_isolation`; `tests/test_security.py:L127#test_cross_user_conversation_isolation`; `docs/SECURITY.md#test_registered_but_unauthorized_tool_is_denied`; `tests/test_tools.py:L87#test_registered_but_unauthorized_tool_is_denied` | VERIFIED | All 14 test names in the guarantee table were found as test functions by grep. |
| C-057 | The caller identity in evidence and logs is the first 16 hex characters of an unsalted SHA-256 of the subject, described in the schema as non-reversible. | CONTRADICTED | DIRECT | HIGH | `src/iat/security/identity.py:L35-L38#hexdigest()[:16]`; `src/iat/schemas/execution.py:L33#Non-reversible hash` | VERIFIED | For predictable subjects (user names, emails) the value can be matched by enumeration; it is pseudonymous rather than anonymous. |

## 16. Next Inspection Targets
| Target | Uncertainty it resolves | Value |
|---|---|---|
| Run `make check` and `make demo` at this commit | whether recorded evidence reproduces [C-038] | converts QUALIFIED claims to runtime-verified |
| Container build and run | Radius 4 container evidence [C-041] | confirms the delivery path |
| Tool executor callers as more agents are added | whether allowlists remain consistent with the registry [C-024, C-025] | prevents silent permission drift |

## 17. What I would verify before repeating this in an architecture meeting.
1. **"There is no way to run it without authentication."** [C-008, C-009, C-006] Could change: static analysis only. Cheapest check: start `iat-serve` with `IAT_JWT_SECRET` unset, then call each `/v1` route without a token.
2. **"Users cannot see each other's conversations."** [C-011, C-012] Could change: a future route that bypasses the repository. Cheapest check: run `tests/test_security.py`.
3. **"No model makes decisions."** [C-017, C-019] Could change: absence claim; a new dependency or node. Cheapest check: `grep -riE "openai|anthropic|bedrock|ChatModel" src pyproject.toml`.
4. **"75 tests pass and coverage is 97%."** [C-036, C-038] Could change: recorded artifacts, not reproduced here. Cheapest check: `uv sync --frozen && make check`, or the latest GitHub Actions run.
5. **"Tool access is governed per agent."** [C-023, C-024, C-025] Could change: the allowlist is supplied by agent code. Cheapest check: read each `executor.invoke` call site against `AgentDefinition.allowed_tools`.
6. **"Logs don't identify users."** [C-057] Could change: hash is unsalted and truncated. Cheapest check: hash a known user name and compare with a log line.
