<!--
PRESERVED ASSESSMENT — do not edit findings below this header.
Source: repo-intent/reports/intent-agent-toolkit/REPORT.md (RepoIntent @ fce683f), checker PASS (46 claims, 101 citations, 0 errors, 0 warnings).
Assessed commit: cc01f2ab236d00aa297c9e355a14b40cad49174a (main after the v0.2 self-assessment; application code identical to 9dc9298). Citations are valid at that commit only.
Type: INDEPENDENT assessment by static, read-only inspection, produced in a fresh session. Code was read and claims formed before the preserved self-assessment was opened.
Previous assessments: docs/assessments/INTENT-001-BASELINE.md (8ecc05d), docs/assessments/INTENT-002-REPOINTENT.md (9dc9298, self-assessment).
Added to this repository on 2026-11-08.
SHA-256 of the report body below (original REPORT.md): d6dc828c67656b7f0224653616e3c6cbaf47725f7596ac70404509918e842b80
-->

# Repository Intelligence Report — intent-agent-toolkit (v0.2, independent run)

## Management Summary

- **Where it is today:** A working, locally run agent toolkit with one reference agent that makes supplier onboarding decisions from synthetic records using fixed rules. Nothing is deployed [C-001, C-007, C-032].
- **Current credible radius:** Radius 3 of 5, with parts of Radius 4 in place [C-005, C-016, C-030].
- **What's working:** Verified tokens are required and cannot be switched off [C-011, C-012]. Agents use only their registered tools [C-017]. Logs hide caller names and tokens [C-020, C-021].
- **Attention areas:** The web response is tied to the reference agent, so a second kind of agent needs a change first [C-026, C-027]. The container is not built in automated checks [C-032]. Some documents lag the code [C-029, C-038].
- **Questions to settle before setting direction:** Where will it run, and behind which identity provider [C-043]? Is a second agent the next proof [C-026]?

## Architect Brief

- **What it is:** a Python/FastAPI service hosting a deterministic LangGraph supplier-readiness agent, version 0.2.0, described as a reusable foundation for building and operating agents [C-001, C-002, C-003, C-006].
- **Shape:** one entry point (`iat-serve` → uvicorn factory) [C-004]; an app factory composes a frozen tool policy, bounded in-memory conversation store, keyed pseudonymizer and a transport-independent runner [C-005, C-016, C-017, C-020].
- **Where the intelligence is:** deterministic rules and a template narrator; no model client found in `src/` [C-007, C-008].
- **Implemented vs planned:**
  - *Implemented:* JWT auth with scopes, owner isolation, governed tool executor, execution records, log redaction, five conversation bounds, readiness checks [C-011, C-013, C-015, C-017, C-019, C-021, C-016, C-025].
  - *Defined, not built in CI:* container image [C-032].
  - *Seams only:* enterprise IdP, durable store, MCP, AgentCore [C-037].
- **Radius position:**

  | Radius | Status | Basis |
  |---|---|---|
  | 1 Intent & Discovery | EVIDENCED | Project intent, progressive deltas, intent gate hook [C-001, C-039] |
  | 2 Prototype & Proof | EVIDENCED | Recorded 120-case suite, demo 5/5, live-server transcript [C-028, C-031, C-046] |
  | 3 Engineering & Integration | EVIDENCED | Layered composition, typed contracts, frozen policy, strict typing, CI matrix [C-005, C-017, C-030]; HTTP contract coupled to one agent [C-026] |
  | 4 Delivery & Production | PARTIAL | Fail-closed auth, readiness, bounded memory, scans [C-012, C-025, C-016, C-030]; container unbuilt, per-process state, no rate limiting found [C-032, C-042, C-036] |
  | 5 Enterprise Operation & Governance | NOT YET EVIDENCED | Assessment loop present [C-039, C-040]; IdP, deployment and operations not found [C-043] |

- **Attention areas:**
  1. `InvokeResponse.output` is typed to `SupplierAssessment` while the runner accepts any output model [C-026, C-027].
  2. API docs are on by default and the image binds `0.0.0.0` [C-033].
  3. Container build unverified; base images pinned by tag [C-032, C-034].
- **Biggest unknowns:**
  1. Deployment target and identity provider [C-043].
  2. Whether the image builds and serves [C-044].
  3. Whether the edit hook fires in a live Claude Code session [C-045].
- **Smallest next step outward (option for the owners):** a CI job that builds and runs the image. Proof: `/health/ready` 200 and unauthenticated invoke 401 against the running container [C-032, C-025]. An alternative step within Radius 3: a second minimal agent invoked over HTTP, proving the response contract is agent-neutral [C-026].

---

## 1. Repository Identity
- **Repository:** https://github.com/kendallmark3/intent-agent-toolkit
- **Commit SHA:** `cc01f2ab236d00aa297c9e355a14b40cad49174a` ("Merge RepoIntent assessment of v0.2 (#2)"); application code is identical to `9dc9298` (the commit after INTENT-002); the newer commit adds the preserved self-assessment.
- **Analysis timestamp:** 2026-11-08T13:46Z
- **Languages/frameworks observed:** Python ≥3.11, FastAPI, LangGraph, Pydantic v2, pydantic-settings, PyJWT, uv lockfile, GitHub Actions, Dockerfile [C-003].
- **Assessor independence:** fresh session; the code was read and the claims formed before the preserved self-assessment was opened. It was then used only for comparison (section 13).
- **Limitations:** static, read-only inspection. No code was built, installed, or run. Runtime statements rest on artifacts committed under `docs/evidence/`.

## 2. Executive Orientation
- A reusable agent toolkit at 0.2.0 with one reference agent, Supplier Readiness [C-001, C-002, C-006].
- One process entry point; the app factory is the composition root [C-004, C-005].
- Decisions come from five deterministic checks; the narrator only writes prose [C-007, C-008].
- Security boundary is a bearer JWT verified on every `/v1` route, with scopes and owner-scoped data [C-011, C-013, C-015].
- Tool access is decided by a frozen, registration-derived policy and a per-run gateway [C-017].
- Each run emits an execution record with a keyed caller pseudonym [C-019, C-020].
- New in this run: the HTTP response schema is specific to the reference agent [C-026, C-027].
- Most important uncertainty: runtime behaviour is from recorded artifacts, not reproduced here [C-028].

## 3. Coverage & Confidence
- **Read in full:** all 30 Python modules under `src/iat/`, `pyproject.toml`, `Makefile`, `Dockerfile`, `.github/workflows/ci.yml`, `.env.example`, `.gitignore`, `.claude/settings.json`, `hooks/pre-implement-hook.sh`, `intent/project-intent.md`, `intent/current-feature.md`, `docs/AGENTCORE_FUTURE.md`, `tests/conftest.py`.
- **Read in part:** `README.md` (full), `docs/INTENT-002-RESULTS.md` (results, risks, next steps), `docs/ARCHITECTURE.md` and `docs/SECURITY.md` (targeted greps), test files (names and selected bodies), `docs/evidence/intent-002/*` (targeted lines), the preserved self-assessment (summary sections).
- **Not inspected:** `uv.lock` beyond one entry, `skills/`, `agents/`, `templates/` (starter scaffold), `intent/INTENT-001.md` body, `docs/SOURCE_DECISIONS.md`, `docs/IMPLEMENTATION_REPORT.md`, INTENT-001 baseline.
- Confidence: high for code structure and request flow; medium for anything runtime.

## 4. System Purpose
- **Documented:** a reusable, evidence-based foundation for developing, evaluating and operating AI agents, built in progressions [C-001].
- **Implemented:** one agent that returns `READY` / `NOT_READY` / `INSUFFICIENT_EVIDENCE` for synthetic suppliers [C-006, C-007, C-010].
- **Inferred:** the supplier agent is a reference that exercises the platform seams (auth, tools, evidence, memory); the generic runner and agent registry support more agents, but the HTTP layer does not yet [C-026, C-027].
- **Unknown:** intended deployment, users and identity provider [C-043].

## 5. Entry Points & Execution Paths
| Entry point | Started by | Claims |
|---|---|---|
| `iat-serve` → `uvicorn.run("iat.api.app:create_app", factory=True)` | `make run`, Docker `CMD` | C-004 |
| `iat-token` (local dev token CLI) | `uv run iat-token` | C-012 |
| `examples/supplier_readiness/demo.py` (in-process TestClient) | `make demo`, CI | C-030, C-031 |
| `pytest` suite | `make test`, CI | C-028, C-030 |
| `hooks/pre-implement-hook.sh` | Claude Code PreToolUse on Edit/Write | C-039 |

**Representative flow (invoke):** middleware sets request id [C-024] → `get_identity` verifies JWT [C-011] → route checks `agents:invoke` [C-013] → `AgentRunner.run` checks message size, resolves agent, validates conversation ownership [C-015, C-016] → LangGraph `identify → lookup → assess → explain` with a bound tool gateway [C-006, C-017] → rules decide, narrator explains [C-007, C-008] → output validated, execution record logged, turns stored [C-019] → `InvokeResponse` validated against `SupplierAssessment` [C-026].

## 6. Component Map
| Component | Responsibility | Key files | Claims |
|---|---|---|---|
| API | app factory, middleware, error envelope, routes | `src/iat/api/` | C-005, C-022, C-024, C-025 |
| Security | JWT verification, scopes, pseudonyms, dev tokens | `src/iat/security/` | C-011, C-012, C-020 |
| Services | runner, conversation store, supplier repository | `src/iat/services/` | C-015, C-016, C-019, C-010 |
| Agents | registry, supplier graph, rules, narrator | `src/iat/agents/` | C-006, C-007, C-008, C-009 |
| Tools | contract, registry, policy, executor, gateway | `src/iat/tools/` | C-017, C-018, C-037 |
| Schemas | API, assessment, execution contracts | `src/iat/schemas/` | C-019, C-026 |
| Core | settings, JSON logging/redaction, error taxonomy | `src/iat/core/` | C-012, C-021, C-022 |

## 7. Data Flow & Persistence
- **Input:** JSON body with `message` and optional `conversation_id`; extra fields rejected [C-014].
- **Reference data:** synthetic `suppliers.json`, loaded once at startup, read-only [C-010].
- **Transformation:** regex extraction of a supplier reference → tool lookup → five-check rule evaluation → template explanation [C-009, C-007, C-008].
- **Persistence:** conversations in process memory only, bounded and lost on restart [C-016, C-042].
- **Output:** assessment plus execution record; execution record also logged as JSON [C-019, C-021].
- **Gap:** no durable store or external sink found [C-037, C-042].

## 8. External Integrations
| Integration | Evidence | Usage |
|---|---|---|
| Identity provider | `TokenVerifier` protocol; local HMAC `JwtVerifier` only | seam; local only [C-011, C-037] |
| LLM / model provider | none found in `src/` | not present [C-008] |
| AWS Bedrock AgentCore | documented mapping; no AWS dependency found | documented future [C-037] |
| MCP | `Tool.spec()` emits name/description/JSON Schema | shape only [C-037] |
| GitHub Actions | CI workflow | direct [C-030] |

## 9. Interfaces / APIs
- HTTP: `GET /health`, `GET /health/ready`, `GET /v1/agents`, `POST /v1/agents/{key}/invoke`, `GET /v1/conversations`, `GET /v1/conversations/{id}`; `/docs` and `/openapi.json` when enabled [C-013, C-025, C-033].
- CLI: `iat-serve`, `iat-token` [C-004, C-012].
- Library: `create_app(settings, verifier=, agents=, extra_tools=)`, `AgentDefinition`, `Tool` [C-005, C-026, C-037].
- Data contract: `suppliers.json` with per-check `status`, `source`, `expires_on` [C-007, C-010].

## 10. Build / Test / Deploy / Operate
- `make check` runs ruff, format check, mypy strict, bandit, pip-audit, pytest and the intent gate; CI runs it on Python 3.11–3.13 plus the demo [C-030].
- Recorded results: 120 tests passed, 97% coverage, `make check` and `make demo` exit 0 [C-028, C-031].
- Dockerfile: multi-stage uv build, non-root user, `IAT_HOST=0.0.0.0`; no image build found in CI [C-032, C-034].
- Operation: single uvicorn process; JSON logs to stdout; readiness reflects startup-loaded dependencies [C-021, C-025, C-042].
- No deployment manifests found; no live environment can be inferred [C-043].

## 11. Security & Authentication Evidence
- Fail-closed startup without a ≥32-char secret; HMAC algorithms only [C-012].
- JWT decode with algorithm allowlist, issuer, audience, and required `exp/iat/sub/iss/aud` [C-011].
- Identity only from token `sub`; request bodies cannot carry a user id [C-014].
- Per-route scopes [C-013]; owner-scoped conversations indistinguishable from missing (404) [C-015].
- Tool calls: registration → policy → input validation → output validation; failures contained [C-017, C-018].
- Logs: keyed pseudonyms, sensitive-key and token-pattern redaction; validation errors name fields only [C-020, C-021, C-022].
- Conditions to note: docs on by default with `0.0.0.0` in the image [C-033]; no rate limiting found (documented as delegated to a gateway) [C-036]; bounds are per process [C-042].
- This describes visible mechanisms; it is not a statement that the system is secure overall.

## 12. Domain / Business Concepts
- Supplier, supplier id (`SUP-nnn`), aliases [C-009, C-010].
- Five onboarding checks: tax registration, sanctions screening, insurance certificate (with expiry), bank account verification, code of conduct [C-007].
- Decisions: `READY`, `NOT_READY` (any failed check), `INSUFFICIENT_EVIDENCE` (missing or unreadable evidence, never assumed) [C-007].
- All supplier data is labeled synthetic [C-010].

## 13. Alignment Gaps (Contradictions / Drift)
- **Toolkit claim vs HTTP contract:** the runner and `AgentDefinition` accept any output model, but `InvokeResponse.output` is `SupplierAssessment` [C-026, C-027].
- **Test count:** README says 119; recorded results say 120 [C-029].
- **Version wording:** `docs/AGENTCORE_FUTURE.md` refers to "v0.1" while the package is 0.2.0 [C-038].
- **"Reproducible runtime image":** Python deps are frozen, but base images are referenced by tag, not digest [C-034].
- **Error taxonomy:** non-404 framework HTTP errors (for example 405) carry code `INTERNAL_ERROR` while keeping their status [C-023].
- **Undeclared direct import:** `langchain_core` is imported directly but declared only transitively [C-035].

**Comparison with the preserved self-assessment (`docs/assessments/INTENT-002-REPOINTENT.md`):** this run independently confirms the four INTENT-002 changes it reported closed: registration-derived tool policy [C-017], keyed pseudonyms [C-020], conversation bounds [C-016], and scope on agent listing [C-013]. It also confirms the README test-count difference [C-029] and the unbuilt container [C-032]. Not raised in the self-assessment, and new here: C-023, C-026, C-027, C-033, C-034, C-035, C-038.

## 14. Important Unknowns
| Unknown | Why the repo cannot establish it | What would resolve it |
|---|---|---|
| Deployment target, IdP, real users [C-043] | no deployment manifests or IdP configuration | owner decision / next intent |
| Whether the image builds and serves [C-044] | build not recorded; CI has no docker step | CI build-and-run job |
| Whether the edit hook fires in a live Claude Code session [C-045] | hook wiring is static config | a recorded blocked edit in a live session |

## 15. Claims Ledger

| ID | Claim | Class | Strength | Confidence | Evidence | Verification | Caveat |
|---|---|---|---|---|---|---|---|
| C-001 | The documented purpose is a reusable, evidence-based foundation for developing, evaluating and operating AI agents, built in progressions. | OBSERVED | CORROBORATED | HIGH | `intent/project-intent.md:L3-L6#reusable`; `README.md:L3-L5` | VERIFIED | Documented intent. |
| C-002 | Package version is 0.2.0. | OBSERVED | CORROBORATED | HIGH | `pyproject.toml:L3#0.2.0`; `src/iat/__init__.py:L3#0.2.0` | VERIFIED | |
| C-003 | Declared runtime stack: Python ≥3.11, FastAPI, uvicorn, Pydantic, pydantic-settings, LangGraph, PyJWT. | OBSERVED | DIRECT | HIGH | `pyproject.toml:L7-L15#langgraph` | VERIFIED | Declaration; usage verified per component in other claims. |
| C-004 | The runtime entry point is `iat-serve`, which starts uvicorn with the `create_app` factory; Makefile and Dockerfile both use it. | OBSERVED | CORROBORATED | HIGH | `pyproject.toml:L29#iat-serve`; `src/iat/main.py:L10-L17#create_app`; `Makefile:L6-L7#iat-serve`; `Dockerfile:L17#iat-serve` | VERIFIED | Two-pass: no other server start found in `src/`. |
| C-005 | `create_app` is the composition root: it loads supplier data and builds tool registry, agent registry, bounded conversation store, tool policy, and runner. | OBSERVED | DIRECT | HIGH | `src/iat/api/app.py:L59-L97#create_app` | VERIFIED | |
| C-006 | One agent is registered by default, `supplier-readiness`, a LangGraph graph of identify → (lookup) → assess → explain. | OBSERVED | CORROBORATED | HIGH | `src/iat/agents/registry.py:L52-L65#default_agents`; `src/iat/agents/supplier_readiness/graph.py:L135-L145#add_conditional_edges` | VERIFIED | |
| C-007 | Decisions are deterministic: five required checks; any failed check yields NOT_READY, otherwise any missing yields INSUFFICIENT_EVIDENCE. | OBSERVED | DIRECT | HIGH | `src/iat/agents/supplier_readiness/rules.py:L52-L74#REQUIRED_CHECKS`; `src/iat/agents/supplier_readiness/rules.py:L107-L113#NOT_READY` | VERIFIED | |
| C-008 | Explanations come from `TemplateNarrator`; no model or LLM client was found in `src/`. | OBSERVED | CORROBORATED | HIGH | `src/iat/agents/supplier_readiness/narrator.py:L25-L47#TemplateNarrator`; `src/iat/agents/registry.py:L61#TemplateNarrator` | VERIFIED | Search scope: grep of `src/` for bedrock, boto3, openai, anthropic, ChatModel, llm (case-insensitive); only docstring mentions found. |
| C-009 | Supplier references are extracted by regex: an `SUP-nnn` id or the word "supplier" followed by a capitalised name. | OBSERVED | DIRECT | HIGH | `src/iat/agents/supplier_readiness/graph.py:L36-L58#extract_supplier_reference` | VERIFIED | |
| C-010 | Supplier data is a synthetic JSON file loaded once at startup into a read-only repository. | OBSERVED | CORROBORATED | HIGH | `src/iat/core/config.py:L18#suppliers.json`; `src/iat/services/supplier_repository.py:L25-L28#from_json`; `src/iat/data/suppliers.json:L2#SYNTHETIC` | VERIFIED | |
| C-011 | All `/v1` routes depend on `get_identity`, which rejects a missing token and verifies JWTs with an algorithm allowlist, issuer, audience and required claims. | OBSERVED | CORROBORATED | HIGH | `src/iat/api/routes.py:L29#get_identity`; `src/iat/api/dependencies.py:L42-L49#Missing bearer token`; `src/iat/security/identity.py:L50-L62#algorithms` | VERIFIED | Two-pass: health router is the only router without the dependency. |
| C-012 | Settings require a JWT secret of at least 32 characters and allow only HMAC algorithms; a test covers fail-closed startup. | OBSERVED | CORROBORATED | HIGH | `src/iat/core/config.py:L36-L38#jwt_secret`; `src/iat/core/config.py:L64-L85#_secret_strength`; `tests/test_startup_and_health.py:L26#test_startup_fails_closed_without_secret` | VERIFIED | |
| C-013 | Invoke and agent listing require `agents:invoke`; conversation routes require `conversations:read`. | OBSERVED | DIRECT | HIGH | `src/iat/api/routes.py:L56-L60#SCOPE_INVOKE`; `src/iat/api/routes.py:L94-L97#SCOPE_READ_CONVERSATIONS` | VERIFIED | |
| C-014 | Caller identity comes only from the verified `sub` claim; the invoke request schema forbids extra fields. | OBSERVED | CORROBORATED | HIGH | `src/iat/security/identity.py:L64-L69#sub`; `src/iat/schemas/api.py:L15-L16#extra="forbid"` | VERIFIED | |
| C-015 | Conversations are owner-scoped; another owner's conversation raises NotFound, and a test covers cross-user isolation. | OBSERVED | CORROBORATED | HIGH | `src/iat/services/conversations.py:L129-L133#_owned`; `tests/test_security.py:L127#test_cross_user_conversation_isolation` | VERIFIED | |
| C-016 | Conversation storage has five configurable bounds (total, per owner, turns, message size, idle TTL) with least-recently-active eviction. | OBSERVED | CORROBORATED | HIGH | `src/iat/services/conversations.py:L42-L56#ConversationLimits`; `src/iat/services/conversations.py:L137-L155#owner_capacity`; `src/iat/core/config.py:L55-L60#max_conversations` | VERIFIED | Bounds are per process (C-042). |
| C-017 | Tool calls pass registration, a frozen registration-derived policy, input validation and output validation; agents receive only a per-run gateway bound by the runner. | OBSERVED | CORROBORATED | HIGH | `src/iat/tools/registry.py:L148-L182#_invoke`; `src/iat/tools/registry.py:L58-L77#MappingProxyType`; `src/iat/api/app.py:L81-L82#tool_grants`; `src/iat/services/runner.py:L96#bind` | VERIFIED | In-process trust only, as the authors note. |
| C-018 | Tool exceptions are contained and returned as an ERROR result with a generic message. | OBSERVED | DIRECT | HIGH | `src/iat/tools/registry.py:L171-L181#Tool execution failed` | VERIFIED | |
| C-019 | Each run produces an `ExecutionRecord` (request id, execution id, agent, pseudonymous subject, tool records, status, duration) that is logged. | OBSERVED | CORROBORATED | HIGH | `src/iat/services/runner.py:L74-L87#ExecutionRecord`; `src/iat/schemas/execution.py:L29-L40#subject_hash` | VERIFIED | |
| C-020 | Caller pseudonyms are HMAC-SHA256 truncated to 128 bits, keyed by an explicit key or a domain-separated derivation from the JWT secret. | OBSERVED | DIRECT | HIGH | `src/iat/security/pseudonym.py:L33-L51#derive_key` | VERIFIED | Pseudonymisation, not anonymisation. |
| C-021 | The JSON log formatter redacts sensitive keys, bearer values and JWT-shaped strings. | OBSERVED | DIRECT | HIGH | `src/iat/core/logging.py:L19-L43#SENSITIVE_KEYS` | VERIFIED | Pattern-based. |
| C-022 | Validation errors report field names, not values; unexpected exceptions return a generic 500 envelope. | OBSERVED | DIRECT | HIGH | `src/iat/api/app.py:L138-L154#Invalid fields` | VERIFIED | |
| C-023 | Framework HTTP errors other than 404 (for example 405) keep their status but are labelled `INTERNAL_ERROR`. | OBSERVED | DIRECT | HIGH | `src/iat/api/app.py:L146-L149#INTERNAL_ERROR` | VERIFIED | Label only; status code preserved. |
| C-024 | A client `X-Request-ID` is accepted only if it matches a safe pattern, otherwise generated, and is echoed on the response. | OBSERVED | DIRECT | HIGH | `src/iat/api/app.py:L35#_SAFE_REQUEST_ID`; `src/iat/api/app.py:L111-L124#request_context` | VERIFIED | |
| C-025 | `/health` is liveness; `/health/ready` checks supplier data, agents and tools and returns 503 when any is missing. | OBSERVED | DIRECT | HIGH | `src/iat/api/routes.py:L32-L53#readiness` | VERIFIED | Checks reflect startup state. |
| C-026 | The HTTP response model types `output` as `SupplierAssessment`, while `AgentDefinition.output_model` accepts any Pydantic model. | OBSERVED | CORROBORATED | HIGH | `src/iat/schemas/api.py:L32-L36#SupplierAssessment`; `src/iat/agents/registry.py:L22-L29#output_model`; `src/iat/api/routes.py:L84-L91#InvokeResponse.model_validate` | VERIFIED | |
| C-027 | An agent registered with a different output model would complete in the runner (record COMPLETED, turns stored) but its HTTP invoke would fail response validation and return the generic 500 envelope. | INFERRED | INDIRECT | MEDIUM | `src/iat/services/runner.py:L112-L129#COMPLETED`; `src/iat/api/app.py:L151-L154#handle_unexpected`; `tests/test_tool_policy.py:L75-L86#Attempt`; `tests/test_errors_and_evidence.py:L38#SupplierAssessment` | QUALIFIED | Derived from C-026 and runner ordering; not executed. Search scope: grep of `tests/` for `output_model`; non-supplier output models appear only in runner-level tests, not HTTP tests. |
| C-028 | Recorded JUnit shows 120 tests with 0 failures; recorded coverage is 97%. | OBSERVED | DIRECT | MEDIUM | `docs/evidence/intent-002/test-results.xml#tests="120"`; `docs/evidence/intent-002/coverage.txt:L33#97%` | QUALIFIED | Recorded artifacts; not reproduced in this run. |
| C-029 | README states 119 tests in two places; recorded results state 120. | CONTRADICTED | DIRECT | HIGH | `README.md:L19#119`; `README.md:L95#119 tests`; `docs/INTENT-002-RESULTS.md:L127#120 passed` | VERIFIED | Recorded artifact is the stronger evidence. |
| C-030 | `make check` runs lint, format, mypy strict, bandit, pip-audit, pytest and the intent gate; CI runs the gate and demo on Python 3.11–3.13. | OBSERVED | CORROBORATED | HIGH | `Makefile:L28#check:`; `pyproject.toml:L54-L56#strict`; `.github/workflows/ci.yml:L10-L30#python-version` | VERIFIED | CI results for this commit not seen. |
| C-031 | Recorded `make check` and `make demo` both exited 0, demo 5/5. | OBSERVED | DIRECT | MEDIUM | `docs/evidence/intent-002/check-output.txt:L42#make_check_exit=0`; `docs/evidence/intent-002/check-output.txt:L62-L63#5/5` | QUALIFIED | Recorded output. |
| C-032 | A multi-stage, non-root Dockerfile exists; no image build step was found in CI, and the authors record the build as not executed. | OBSERVED | CORROBORATED | HIGH | `Dockerfile:L9-L17#USER iat`; `.github/workflows/ci.yml`; `README.md:L113-L115#not yet built in CI`; `docs/INTENT-002-RESULTS.md:L138-L139#container build` | VERIFIED | Search scope: full read of `.github/workflows/ci.yml`; no docker or build-push step. |
| C-033 | API docs default to enabled and the image sets `IAT_HOST=0.0.0.0` while leaving the docs setting at its default, so a container started with defaults would serve `/docs` and `/openapi.json` on all interfaces. | INFERRED | CORROBORATED | MEDIUM | `src/iat/core/config.py:L62#docs_enabled`; `src/iat/api/app.py:L103-L105#docs_url`; `Dockerfile:L13#IAT_HOST=0.0.0.0`; `.env.example:L12#IAT_DOCS_ENABLED=true`; `tests/test_startup_and_health.py:L73#test_docs_can_be_disabled` | QUALIFIED | Configurable; whether this matters depends on deployment. |
| C-034 | The Dockerfile describes a reproducible image; Python deps are frozen, but base images are referenced by tag, not digest. | OBSERVED | DIRECT | HIGH | `Dockerfile:L1-L3#Reproducible`; `Dockerfile:L3#uv:0.5`; `Dockerfile:L9#python:3.12-slim` | VERIFIED | |
| C-035 | `graph.py` imports `langchain_core` directly; no direct declaration was found in `pyproject.toml` (it is present in the lockfile). | OBSERVED | CORROBORATED | HIGH | `src/iat/agents/supplier_readiness/graph.py:L23#langchain_core`; `pyproject.toml:L8-L15#langgraph`; `uv.lock:L767#langchain-core` | VERIFIED | Search scope: grep of `pyproject.toml` for langchain. Arrives transitively via langgraph. |
| C-036 | No rate limiting was found in `src/`; security docs state it is delegated to a gateway. | OBSERVED | CORROBORATED | HIGH | `docs/SECURITY.md:L47#No rate limiting` | VERIFIED | Search scope: grep of `src/` for rate-limit terms; an upstream gateway could provide it. |
| C-037 | Integration seams exist as protocols/contracts (TokenVerifier, ConversationRepository, MCP-shaped Tool.spec, transport-independent runner); AgentCore is documented as future, with no AWS dependency found. | OBSERVED | CORROBORATED | HIGH | `src/iat/security/identity.py:L39-L40#TokenVerifier`; `src/iat/services/conversations.py:L70-L79#ConversationRepository`; `src/iat/tools/base.py:L39-L46#spec`; `docs/AGENTCORE_FUTURE.md:L18-L26#AgentRunner.run` | VERIFIED | Search scope: `pyproject.toml` dependencies and grep of `src/` for boto3/bedrock. |
| C-038 | `docs/AGENTCORE_FUTURE.md` refers to "v0.1" while the package is 0.2.0. | CONTRADICTED | DIRECT | HIGH | `docs/AGENTCORE_FUTURE.md:L5#v0.1`; `pyproject.toml:L3#0.2.0` | VERIFIED | Wording drift; content otherwise consistent. |
| C-039 | The intent loop is wired: project intent lists progressions, current-feature carries an INTENT-002 delta, and a PreToolUse hook blocks non-Markdown edits when intent is insufficient. | OBSERVED | CORROBORATED | HIGH | `intent/project-intent.md:L26-L28#INTENT-002`; `intent/current-feature.md:L33#Delta 1`; `.claude/settings.json:L3-L9#pre-implement-hook.sh`; `hooks/pre-implement-hook.sh:L19-L29#exit 2` | VERIFIED | Live firing not observed (C-045). |
| C-040 | The preserved v0.2 assessment is labelled a self-assessment; INTENT-002 results name an independent RepoIntent run and a container CI build as next steps. | OBSERVED | CORROBORATED | HIGH | `docs/assessments/INTENT-002-REPOINTENT.md:L5#Not independent`; `docs/INTENT-002-RESULTS.md:L160-L169#Independent RepoIntent run` | VERIFIED | |
| C-041 | The authors record remaining risks: coordinated eviction, key custody, in-process trust, per-process state, and an evict-after-run race. | OBSERVED | DIRECT | HIGH | `docs/INTENT-002-RESULTS.md:L141-L151#Coordinated eviction` | VERIFIED | Documented, not re-derived. |
| C-042 | Conversations live in process memory and the server starts a single uvicorn process; bounds apply per worker. | OBSERVED | CORROBORATED | HIGH | `src/iat/services/conversations.py:L18-L20#process memory`; `src/iat/main.py:L10-L17#create_app`; `docs/INTENT-002-RESULTS.md:L149#Per-process state`; `src/iat/services/conversations.py:L93#threading.Lock` | VERIFIED | |
| C-043 | Deployment target, identity provider and user population are unknown. | UNKNOWN | INSUFFICIENT | LOW | Resolved by an owner decision or a deployment intent. | QUALIFIED | No deployment manifests or IdP config found. |
| C-044 | Whether the container image builds and serves is unknown. | UNKNOWN | INSUFFICIENT | LOW | Resolved by a recorded `docker build` and run with health and 401 checks. | QUALIFIED | |
| C-045 | Whether the local edit hook fires in a live Claude Code session is unknown. | UNKNOWN | INSUFFICIENT | LOW | Resolved by a recorded blocked edit in a live session with a blank intent. | QUALIFIED | Tests exercise the script directly. |
| C-046 | A recorded live-server transcript shows unauthenticated invoke 401 and cross-user conversation read 404. | OBSERVED | DIRECT | MEDIUM | `docs/evidence/intent-002/live-server.txt:L3#401`; `docs/evidence/intent-002/live-server.txt:L9#404` | QUALIFIED | Recorded output. |

## 16. Next Inspection Targets
| Target | Uncertainty resolved | Value |
|---|---|---|
| Register a minimal non-supplier agent and invoke it over HTTP | confirms or refutes C-027 | High: tests the "toolkit" claim |
| CI run for `cc01f2a` and a container build | C-028, C-044 | High: converts recorded evidence to current evidence |
| `docs/SOURCE_DECISIONS.md` and starter `skills/`/`agents/` | not inspected | Low–medium |

## 17. What I would verify before repeating this in an architecture meeting.
1. **"It's a reusable toolkit, but today the web API only speaks the supplier agent's format."** [C-026, C-027] Could change: inference, not executed. Cheapest check: a ten-line test registering an agent with a different output model and calling `/invoke`.
2. **"Authentication cannot be turned off."** [C-011, C-012] Could change: static reading. Cheapest check: start without `IAT_JWT_SECRET`, then call `/v1/agents` without a token.
3. **"Tests and the full gate pass."** [C-028, C-031] Could change: recorded artifacts; README count differs [C-029]. Cheapest check: the GitHub Actions run for `cc01f2a`, or `make check`.
4. **"There's no LLM in the decision path."** [C-008] Could change: absence claim. Cheapest check: `grep -rniE "bedrock|openai|anthropic|chatmodel" src/`.
5. **"The container is production-shaped."** [C-032, C-033, C-034] Could change: never built; docs on by default. Cheapest check: `docker build` then `docker run` with `IAT_DOCS_ENABLED=false`, curl `/health/ready` and `/docs`.
