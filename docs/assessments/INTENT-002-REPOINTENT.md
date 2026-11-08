<!--
PRESERVED ASSESSMENT — do not edit findings below this header.
Source: repo-intent/reports/intent-agent-toolkit-v0.2/REPORT.md (RepoIntent @ fce683fe), checker PASS (43 claims, 99 citations, 0 errors).
Assessed commit: 9dc9298a518f6c557b83d05472d38751829ea35d (main after INTENT-002). Citations are valid at that commit only.
Type: SELF-ASSESSMENT by static, read-only inspection, produced in the same session that authored INTENT-001 and INTENT-002. Not independent.
Previous assessment: docs/assessments/INTENT-001-BASELINE.md (8ecc05d).
Added to this repository on 2026-11-08.
SHA-256 of the report body below (original REPORT.md): 437952872dab82ab92684a509e3bf4b7f903f4dd9d74031298628f3f73d84bd5
-->

# Repository Intelligence Report — intent-agent-toolkit (v0.2, after INTENT-002)

## Management Summary

- **Where it is today:** A working, hardened agent toolkit. The four attention areas from the first assessment are closed, each with before-and-after evidence. It runs locally only; nothing is deployed [C-001, C-030, C-040].
- **Current credible radius:** Radius 3 of 5 (Engineering & Integration), with more of Radius 4 in place than before [C-005, C-012, C-021].
- **What's working:** Tool permissions come from registration, not from agents [C-010]. Logged user identifiers are keyed, so names cannot be matched by guessing [C-015]. Stored conversations have firm size and time limits [C-021, C-022].
- **Attention areas:** The README's test count is one behind the recorded results [C-036]. The container is still unbuilt and is not built in automated checks [C-033].
- **Questions to settle before setting direction:** Which deployment target and identity provider come next [C-046]? Will an independent reviewer repeat this assessment [C-047]?

## Architect Brief

- **What it is:** a Python/FastAPI service hosting a deterministic LangGraph supplier-readiness agent; version 0.2.0 after an evidence-driven hardening progression [C-001, C-002, C-003].
- **Shape:** one service; an app factory builds a frozen tool policy from agent registrations, a bounded in-memory conversation store, a keyed pseudonymizer, and a transport-independent runner [C-005, C-010, C-021, C-015].
- **Where the intelligence is:** deterministic rules and templates; no model client was found [C-007, C-008].
- **Implemented vs planned:**
  - *Implemented since v0.1:* registration-derived tool policy with a runner-bound gateway; HMAC pseudonyms; five conversation bounds; scope on agent listing; local intent hook; blank-value config handling [C-010, C-011, C-015, C-021, C-025, C-026, C-028].
  - *Defined, not built:* container image [C-033].
  - *Seams only:* enterprise IdP, durable store, MCP, AgentCore [C-034].
- **Radius position:**

  | Radius | Status | Basis |
  |---|---|---|
  | 1 Intent & Discovery | EVIDENCED | Project intent, INTENT-001, INTENT-002 with deltas [C-027, C-040, C-041] |
  | 2 Prototype & Proof | EVIDENCED | 120 recorded test cases, before/after finding evidence, demo [C-029, C-030, C-031] |
  | 3 Engineering & Integration | EVIDENCED | Layered design, frozen policy, typed contracts, CI [C-005, C-010, C-032]; integrations remain seams [C-034] |
  | 4 Delivery & Production | PARTIAL | Bounded memory, fail-closed auth, readiness, scans [C-021, C-004, C-019, C-032]; container, deployment, durable state, rate limiting not yet evidenced [C-033, C-035, C-046] |
  | 5 Enterprise Operation & Governance | NOT YET EVIDENCED | Assessment loop and preserved baseline [C-039, C-040]; operational governance not found [C-046] |

- **Attention areas:**
  1. README test count (119) differs from recorded results (120) [C-036].
  2. Conversation-limit defaults are defined in two places [C-037].
  3. Default limits allow tens of megabytes of retained message text per process [C-038].
- **Biggest unknowns:**
  1. Whether the Claude Code hook fires in a live session [C-026].
  2. Whether the container builds [C-033].
  3. Independent confirmation of this assessment [C-047].
- **Smallest next step outward (option for the owners):** a CI job that builds and runs the container. Proof: `/health/ready` returns 200 and an unauthenticated invoke returns 401 against the running image [C-033, C-019].

## 1. Repository Identity
- **Repository:** https://github.com/kendallmark3/intent-agent-toolkit
- **Commit SHA:** `9dc9298a518f6c557b83d05472d38751829ea35d` (2026-11-08, "Merge INTENT-002: evidence-driven hardening (#1)")
- **Previous assessment:** `docs/assessments/INTENT-001-BASELINE.md` at `8ecc05d` (Radius 3/5, partial 4).
- **Analysis date:** 2026-11-08
- **Languages/frameworks observed:** Python ≥3.11, FastAPI, LangGraph, Pydantic v2, PyJWT; uv lockfile; GitHub Actions; Dockerfile.
- **Limitations:** Static, read-only inspection; no code was built or run for this report. **Assessor independence:** produced in the same session that authored INTENT-001 and INTENT-002, so this is a self-assessment under RepoIntent rules, not an independent review. Starter-scaffold prompts and templates were not read.

## 2. Executive Orientation
- Version 0.2.0 of a reusable agent toolkit; one deterministic LangGraph agent behind a FastAPI service [C-001, C-003, C-007].
- INTENT-002 targeted the four attention areas of the baseline; each has code, regression tests, and recorded before/after output [C-030, C-040].
- Tool access is now resolved from a frozen, registration-derived policy and bound to the executing agent by the runner [C-010, C-011].
- Caller identifiers in logs are keyed HMAC pseudonyms [C-015, C-016].
- Conversation storage is bounded by count, per-owner count, turns, message size, and idle lifetime [C-021, C-022, C-023].
- Most important uncertainty: all runtime claims rest on recorded artifacts; this assessment did not reproduce them [C-029].

## 3. Coverage & Confidence
- **Read in full:** `src/iat/tools/registry.py`, `src/iat/services/conversations.py`, `src/iat/services/runner.py`, `src/iat/security/pseudonym.py`, `src/iat/api/app.py`, `src/iat/core/config.py`, `.claude/settings.json`, `intent/project-intent.md`.
- **Read in part:** remaining `src/iat/` modules (unchanged areas re-anchored), new and changed tests (names and key assertions), `docs/*.md`, `docs/evidence/intent-002/*`, `intent/INTENT-002.md`, `intent/current-feature.md`.
- **Not inspected:** `uv.lock`, starter skill and agent prompts, `templates/`.
- Confidence is high for code structure; there is no runtime evidence from this assessment.

## 4. System Purpose
- **Documented:** a reusable, evidence-based foundation for building and operating AI agents, assessed after each progression [C-001, C-027].
- **Implemented:** supplier readiness decisions (`READY`, `NOT_READY`, `INSUFFICIENT_EVIDENCE`) from synthetic records [C-007].
- **This progression:** close the baseline's findings without new infrastructure, agents, or cloud work [C-041].
- **Unknowns:** deployment target and users [C-046].

## 5. Entry Points & Execution Paths
| Entry point | How it is started | Evidence |
|---|---|---|
| HTTP service | `iat-serve` → uvicorn factory `create_app` | [C-002] |
| Dev token CLI | `iat-token` | [C-002] |
| Demo | `make demo` | [C-031] |
| CI | GitHub Actions on push and pull request | [C-032] |

**Representative flow — invoke (traced):** bearer JWT verified by router dependency → `agents:invoke` scope → `AgentRunner.run` checks message size against configured limit → checks ownership if continuing → binds `AgentToolGateway` to the registered agent → graph `identify` → `lookup` via gateway (policy check) → `assess` (rules) → `explain` → execution record with keyed pseudonym → bounded append [C-004, C-006, C-010, C-011, C-015, C-021, C-023].

## 6. Component Map
| Component | Responsibility | Key files | Claims |
|---|---|---|---|
| API | routes, auth, error envelope, request ids | `src/iat/api/` | C-004, C-005, C-006, C-019 |
| Runner | size check, gateway binding, evidence | `src/iat/services/runner.py` | C-011, C-015, C-023 |
| Agents | registry (grants source), supplier graph | `src/iat/agents/` | C-007, C-012 |
| Tools | registry, frozen policy, gateway, executor | `src/iat/tools/registry.py` | C-010, C-011, C-013 |
| Security | JWT verifier, scopes, pseudonymizer | `src/iat/security/` | C-004, C-015, C-016 |
| Conversations | owner scoping, five bounds, eviction | `src/iat/services/conversations.py` | C-020, C-021, C-022 |
| Core | settings (blank-as-unset), logging, errors | `src/iat/core/` | C-028, C-017 |

## 7. Data Flow & Persistence
- **Inputs:** message (configured limit, default 2000; schema ceiling 8000) and optional conversation id [C-023].
- **Persistence:** conversations in process memory, least-recently-active order, with an owner index; expiry purged lazily on each operation [C-021, C-022].
- **Retention:** sliding turn window with a `dropped_turns` count; idle conversations removed [C-022].
- **Outputs:** assessment plus execution record; JSON logs with pseudonymized identity [C-015, C-017].
- **Gaps:** state is per-process and lost on restart [C-035].

## 8. External Integrations
| Integration | Evidence | Usage |
|---|---|---|
| Identity provider | `TokenVerifier` protocol, local HMAC verifier | seam [C-034] |
| Model provider | no client found | not integrated [C-008] |
| MCP | MCP-shaped tool spec | seam [C-034] |
| AWS / AgentCore | documentation; excluded by intent | out of scope for INTENT-001/002 [C-041] |

## 9. Interfaces / APIs
- **HTTP:** `/health`, `/health/ready`, `/v1/agents` (now `agents:invoke`), `/v1/agents/{agent_key}/invoke`, `/v1/conversations`, `/v1/conversations/{conversation_id}` (adds `dropped_turns`) [C-006, C-024].
- **Configuration:** five conversation limits and an optional pseudonym key, all `IAT_`-prefixed [C-021, C-016].
- **Library:** `ToolPolicy`, `ToolExecutor.bind`, `AgentToolGateway.invoke(tool_name, args)`; the `allowed_tools` argument was removed [C-010, C-011].

## 10. Build / Test / Deploy / Operate
- **Version:** 0.2.0 in package metadata and module [C-003].
- **Tests:** recorded JUnit shows 120 cases, 0 failures, 0 errors; coverage 97% of 991 statements [C-029].
- **Before/after evidence:** scripts and outputs for findings A–C on both commits [C-030].
- **Gates:** ruff, mypy strict, bandit, pip-audit, intent gate, demo in CI; recorded `make check` exit 0 [C-031, C-032].
- **Deploy:** Dockerfile unchanged and not built; no container step found in CI [C-033].

## 11. Security & Authentication Evidence
- **Authentication:** unchanged from v0.1: PyJWT with algorithm allowlist, issuer and audience, required claims; secret required at startup [C-004].
- **Authorization:** scopes on all `/v1` routes, including agent listing [C-006].
- **Tool authority:** policy built from registrations, validated against registered tools, frozen; agents receive only a bound gateway [C-010, C-011, C-013].
- **Identity in logs:** HMAC-SHA256 pseudonym, 128 bits; key explicit or derived from the JWT secret with a label [C-015, C-016].
- **Resource bounds:** five limits with deterministic tests [C-021, C-022, C-023].
- **Documented limits:** in-process trust for the gateway, pseudonym key custody, coordinated eviction, per-process state [C-018, C-035].
- These describe code behaviour, not the security of any deployment.

## 12. Domain / Business Concepts
- Unchanged from v0.1: five readiness checks; failure outranks missing evidence; a sanctions `potential_match` is a failed check [C-007, C-009].

## 13. Alignment Gaps (Contradictions / Drift)
- **Test count:** README states 119 tests in two places; recorded results show 120 [C-036].
- **Duplicated defaults:** the five limits have defaults both in settings and in `ConversationLimits`; they agree today [C-037].
- **Baseline preserved:** the INTENT-001 report is held verbatim with its SHA-256 and a self-assessment label [C-039].
- **Resolved since baseline:** caller-supplied allowlist, unkeyed identity hash, unbounded memory, unscoped agent listing, plugin-only hook config, empty project intent [C-010, C-015, C-021, C-025, C-026, C-027].

## 14. Important Unknowns
| Unknown | Why the repo cannot establish it | What would resolve it |
|---|---|---|
| Recorded results reproduce [C-029] | static assessment | `make check` at `9dc9298`, or the CI run for the merge commit |
| Hook fires in a live Claude Code session [C-026] | depends on the Claude Code runtime | edit a `.py` file in a session with a blank intent |
| Container builds and runs [C-033] | no build evidence | CI build and smoke run |
| Independent assessment agrees [C-047] | same-session assessor | RepoIntent from a fresh session |
| Deployment target and users [C-046] | no deployment configuration | owner decision |

## 15. Claims Ledger

| ID | Claim | Class | Strength | Confidence | Evidence | Verification | Caveat |
|---|---|---|---|---|---|---|---|
| C-001 | The repository states its purpose as a reusable, evidence-based foundation for developing, evaluating and operating AI agents. | OBSERVED | DIRECT | HIGH | `intent/INTENT-001.md:L15#Build the first working version`; `intent/project-intent.md:L3-L6#Purpose:` | VERIFIED | Documented intent. |
| C-002 | Entry points are the iat-serve and iat-token console scripts. | OBSERVED | DIRECT | HIGH | `pyproject.toml#iat-serve`; `pyproject.toml#iat-token`; `src/iat/main.py#factory=True` | VERIFIED | |
| C-003 | Package metadata and the module both declare version 0.2.0. | OBSERVED | DIRECT | HIGH | `pyproject.toml:L3#0.2.0`; `src/iat/__init__.py:L3#0.2.0` | VERIFIED | |
| C-004 | JWT verification uses PyJWT with a configured HMAC algorithm list, issuer, audience and required claims; the secret is required with a 32-character minimum. | OBSERVED | CORROBORATED | HIGH | `src/iat/security/identity.py:L43-L69#options={"require"`; `src/iat/core/config.py:L36#jwt_secret`; `src/iat/core/config.py:L66#_secret_strength`; `tests/test_security.py:L70#test_invalid_tokens_are_rejected` | VERIFIED | Unchanged since v0.1 apart from line positions. |
| C-005 | create_app builds the tool registry, agent registry, bounded conversation store, frozen tool policy and runner with a pseudonymizer. | OBSERVED | DIRECT | HIGH | `src/iat/api/app.py:L70-L97#ToolPolicy(agent_registry.tool_grants()` | VERIFIED | |
| C-006 | All /v1 routes sit behind the identity dependency, and agent listing now checks the agents:invoke scope. | OBSERVED | CORROBORATED | HIGH | `src/iat/api/routes.py:L29#dependencies=[Depends(get_identity)]`; `src/iat/api/routes.py:L57-L59#SCOPE_INVOKE`; `tests/test_governance.py:L20#test_listing_agents_requires_invoke_scope` | VERIFIED | |
| C-007 | Readiness is decided by five coded checks; the explanation template receives the decision rather than producing it. | OBSERVED | DIRECT | HIGH | `src/iat/agents/supplier_readiness/rules.py:L52#REQUIRED_CHECKS`; `src/iat/agents/supplier_readiness/rules.py:L112#Decision.READY`; `src/iat/agents/supplier_readiness/graph.py:L124#decision=state["decision"]` | VERIFIED | |
| C-008 | No model provider client was found in application source or declared dependencies. | OBSERVED | CORROBORATED | HIGH | `pyproject.toml#dependencies` | VERIFIED | Search scope: case-insensitive grep for openai, anthropic, bedrock, boto3, ChatModel in `src/` and `pyproject.toml` at this commit. |
| C-009 | A sanctions potential_match is treated as a failed check. | OBSERVED | DIRECT | HIGH | `src/iat/agents/supplier_readiness/rules.py:L61#potential_match` | VERIFIED | Domain choice against synthetic data. |
| C-010 | ToolPolicy is built from agent registrations, rejects grants for unregistered tools, and stores grants in a read-only mapping; the executor checks the policy for the executing agent. | OBSERVED | CORROBORATED | HIGH | `src/iat/tools/registry.py:L58-L77#MappingProxyType`; `src/iat/agents/registry.py:L41-L43#def tool_grants`; `tests/test_tool_policy.py:L160#test_policy_rejects_grants_for_unregistered_tools`; `tests/test_tool_policy.py:L165#test_policy_is_immutable` | VERIFIED | |
| C-011 | The runner binds an AgentToolGateway to the registered agent; the gateway's invoke accepts only a tool name and arguments, and the graph calls tools through it. | OBSERVED | CORROBORATED | HIGH | `src/iat/services/runner.py:L96#self._tools.bind(agent.key, recorder)`; `src/iat/tools/registry.py:L93-L107#def invoke(self, tool_name`; `src/iat/agents/supplier_readiness/graph.py:L73-L74#tools.invoke`; `tests/test_tool_policy.py:L127#test_gateway_signature_accepts_no_permission_arguments` | VERIFIED | |
| C-012 | Grants are read once at startup, so a runtime change to the agent module's ALLOWED_TOOLS leaves the executing policy unchanged. | OBSERVED | CORROBORATED | HIGH | `src/iat/agents/supplier_readiness/graph.py:L14#changing it at runtime grants nothing`; `tests/test_tool_policy.py:L134#test_changing_agent_constant_at_runtime_grants_nothing` | VERIFIED | Test read, not run here. |
| C-013 | A registered agent that calls a tool outside its registration receives DENIED, and the tool's call counter stays at zero. | OBSERVED | CORROBORATED | HIGH | `tests/test_tool_policy.py:L95#test_agent_cannot_call_tool_outside_its_registration`; `docs/evidence/intent-002/findings-current.txt:L1#DENIED` | VERIFIED | |
| C-014 | On the baseline commit the same scenarios showed an agent-supplied allowlist returning OK, the logged value matching sha256 of alice, and 20000 stored conversations. | OBSERVED | DIRECT | MEDIUM | `docs/evidence/intent-002/findings-baseline.txt:L1-L3#20000` | QUALIFIED | Recorded output; the script is in the repo and was not re-run here. |
| C-015 | The execution record's subject_hash is an HMAC-SHA256 pseudonym truncated to 32 hex characters. | OBSERVED | CORROBORATED | HIGH | `src/iat/security/pseudonym.py:L41-L51#hmac.new(self._key`; `src/iat/services/runner.py:L79#self._pseudonymize(identity.subject)`; `src/iat/schemas/execution.py:L33-L36#Keyed pseudonym`; `tests/test_pseudonym.py:L36#test_dictionary_attack_without_key_finds_no_match` | VERIFIED | |
| C-016 | The pseudonym key is IAT_SUBJECT_PSEUDONYM_KEY when set, otherwise derived from the JWT secret with a fixed label. | OBSERVED | CORROBORATED | HIGH | `src/iat/security/pseudonym.py:L33-L38#_DERIVATION_LABEL`; `src/iat/core/config.py:L42#subject_pseudonym_key`; `tests/test_pseudonym.py:L56#test_derived_key_is_domain_separated_from_jwt_secret` | VERIFIED | Key custody limits are documented (C-018). |
| C-017 | Logs are JSON with sensitive-key and token-pattern redaction; the runner logs the execution record only. | OBSERVED | CORROBORATED | HIGH | `src/iat/core/logging.py:L19#SENSITIVE_KEYS`; `src/iat/core/logging.py:L46#class JsonFormatter`; `src/iat/services/runner.py:L86#agent_execution`; `tests/test_errors_and_evidence.py:L140#test_logs_exclude_secrets_and_message_content` | VERIFIED | |
| C-018 | The security document states the limits of the new controls: gateway in-process trust, pseudonym key custody and rotation, coordinated eviction. | OBSERVED | DIRECT | HIGH | `docs/SECURITY.md:L50-L60#Tool policy` | VERIFIED | |
| C-019 | Readiness reports dependency checks and returns 503 when one fails; error responses use one envelope. | OBSERVED | CORROBORATED | HIGH | `src/iat/api/routes.py:L43-L52#HTTP_503_SERVICE_UNAVAILABLE`; `src/iat/api/app.py:L126-L154#Internal server error` | VERIFIED | |
| C-020 | Conversation access by another subject raises the same NotFoundError as a missing conversation; ids are server-generated. | OBSERVED | CORROBORATED | HIGH | `src/iat/services/conversations.py:L129-L133#conv.owner != identity.subject`; `src/iat/services/conversations.py:L138#uuid.uuid4().hex`; `tests/test_security.py:L127#test_cross_user_conversation_isolation` | VERIFIED | |
| C-021 | Five configurable bounds exist: total conversations, per-owner conversations, turns per conversation, message characters, idle lifetime; settings flow into the store. | OBSERVED | CORROBORATED | HIGH | `src/iat/services/conversations.py:L42-L56#class ConversationLimits`; `src/iat/core/config.py:L56-L60#conversation_idle_ttl_seconds`; `src/iat/api/app.py:L72-L80#ConversationLimits(`; `tests/test_conversation_bounds.py:L193#test_settings_flow_into_repository_limits` | VERIFIED | |
| C-022 | At capacity the least recently active conversation is evicted (per owner first, then globally); turns beyond the window are dropped and counted; idle conversations are purged oldest first. | OBSERVED | CORROBORATED | HIGH | `src/iat/services/conversations.py:L116-L122#idle_expired`; `src/iat/services/conversations.py:L142-L146#owner_capacity`; `src/iat/services/conversations.py:L191-L195#dropped_turns`; `tests/test_conversation_bounds.py:L82#test_storage_stays_bounded_under_sustained_load` | VERIFIED | Per process. |
| C-023 | The runner rejects messages over the configured limit before agent lookup, execution or storage. | OBSERVED | CORROBORATED | HIGH | `src/iat/services/runner.py:L61-L63#Message exceeds`; `tests/test_conversation_bounds.py:L107#test_runner_enforces_configured_message_size` | VERIFIED | |
| C-024 | The conversation view exposes dropped_turns. | OBSERVED | DIRECT | HIGH | `src/iat/schemas/api.py:L52#dropped_turns`; `tests/test_conversation_bounds.py:L207#test_api_exposes_dropped_turns` | VERIFIED | Additive field. |
| C-025 | Agent listing requires agents:invoke (closes baseline C-010). | OBSERVED | CORROBORATED | HIGH | `src/iat/api/routes.py:L57-L59#SCOPE_INVOKE`; `tests/test_governance.py:L20#test_listing_agents_requires_invoke_scope` | VERIFIED | |
| C-026 | A project hook in .claude/settings.json runs hooks/pre-implement-hook.sh via CLAUDE_PROJECT_DIR before Edit, Write and MultiEdit; a test runs the configured command against a blank and a sufficient intent. | OBSERVED | CORROBORATED | MEDIUM | `.claude/settings.json:L5-L9#CLAUDE_PROJECT_DIR`; `tests/test_governance.py:L61#test_hook_blocks_code_edits_when_intent_is_blank` | QUALIFIED | The test simulates the hook with bash; execution inside a live Claude Code session was not observed. |
| C-027 | The project intent file states purpose, business outcomes, constraints and progressions. | OBSERVED | DIRECT | HIGH | `intent/project-intent.md:L1-L12#Business outcomes:`; `tests/test_governance.py:L78#test_project_intent_sections_are_filled` | VERIFIED | |
| C-028 | Settings treat blank environment values as unset, and a test walks the .env.example setup path. | OBSERVED | CORROBORATED | HIGH | `src/iat/core/config.py:L22-L30#env_ignore_empty=True`; `tests/test_startup_and_health.py:L80#test_documented_env_example_setup_starts` | VERIFIED | |
| C-029 | Recorded JUnit output shows 120 cases with 0 failures and 0 errors; recorded coverage is 97% of 991 statements. | OBSERVED | DIRECT | MEDIUM | `docs/evidence/intent-002/test-results.xml#tests="120"`; `docs/evidence/intent-002/test-results.xml#failures="0"`; `docs/evidence/intent-002/coverage.txt:L33#97%` | QUALIFIED | Recorded artifacts, not reproduced in this assessment. |
| C-030 | Recorded current-code output shows the finding scenarios as DENIED, False and 50 stored conversations. | OBSERVED | DIRECT | MEDIUM | `docs/evidence/intent-002/findings-current.txt:L1-L4#evictions` | QUALIFIED | Recorded output. |
| C-031 | Recorded make check and make demo both exited 0, with 120 tests passed. | OBSERVED | DIRECT | MEDIUM | `docs/evidence/intent-002/check-output.txt:L22#120 passed`; `docs/evidence/intent-002/check-output.txt:L42#make_check_exit=0`; `docs/evidence/intent-002/check-output.txt:L63#make_demo_exit=0` | QUALIFIED | Recorded output. |
| C-032 | CI runs lint, type check, security scan, tests, intent gate and demo on Python 3.11–3.13. | OBSERVED | DIRECT | HIGH | `.github/workflows/ci.yml#make security`; `.github/workflows/ci.yml#make demo`; `Makefile#check:` | VERIFIED | CI outcomes live outside the repository. |
| C-033 | No container build or run step was found in CI; the Dockerfile is present and the results document lists the container build as not executed. | OBSERVED | CORROBORATED | HIGH | `.github/workflows/ci.yml#make demo`; `Dockerfile#USER iat`; `docs/INTENT-002-RESULTS.md:L138#Not executed` | VERIFIED | Search scope: grep for docker in `.github/workflows/ci.yml`. |
| C-034 | Identity provider, durable store, MCP and AgentCore remain protocol seams or documentation. | OBSERVED | CORROBORATED | HIGH | `src/iat/security/identity.py:L39#class TokenVerifier`; `docs/AGENTCORE_FUTURE.md#AgentRunner.run()` | VERIFIED | |
| C-035 | The documentation states conversations are per-process and lost on restart, and that rate limiting is expected upstream. | OBSERVED | DIRECT | HIGH | `docs/SECURITY.md:L47#No rate limiting`; `docs/SECURITY.md:L50#In-memory conversations` | VERIFIED | |
| C-036 | README states 119 tests in two places, while the recorded results show 120. | CONTRADICTED | DIRECT | HIGH | `README.md:L19#119`; `README.md:L95#119 tests`; `docs/evidence/intent-002/test-results.xml#tests="120"` | VERIFIED | Recorded results are the stronger evidence: they are machine output from a test run. |
| C-037 | Default values for the five limits are declared in both Settings and ConversationLimits; they currently agree. | OBSERVED | DIRECT | HIGH | `src/iat/core/config.py:L56-L60#Field(default=1000`; `src/iat/services/conversations.py:L44-L48#max_conversations: int = 1000` | VERIFIED | The app passes settings values explicitly, so only direct users of ConversationLimits see its defaults. |
| C-038 | With default limits, retained user message text can reach roughly 40 million characters per process (1000 conversations × 20 user turns × 2000 characters), plus agent outputs. | INFERRED | INDIRECT | MEDIUM | `src/iat/services/conversations.py:L44-L47#max_message_chars: int = 2000` | QUALIFIED | Derived from C-021 and C-022; actual memory depends on Python object overhead and was not measured. |
| C-039 | The INTENT-001 assessment is preserved with a header naming its commit, its self-assessment status and the SHA-256 of the report body. | OBSERVED | DIRECT | HIGH | `docs/assessments/INTENT-001-BASELINE.md:L2-L9#SHA-256 of the report body` | VERIFIED | Hash match was not recomputed in this assessment. |
| C-040 | INTENT-002 results document each baseline finding with baseline and current outcomes, behaviour changes and remaining risks. | OBSERVED | DIRECT | HIGH | `docs/INTENT-002-RESULTS.md:L141-L149#Per-process state`; `intent/current-feature.md:L33#Delta 1` | VERIFIED | |
| C-041 | INTENT-002 excludes new persistence services, new agents and cloud work. | OBSERVED | DIRECT | HIGH | `intent/INTENT-002.md:L83#Do not introduce Redis`; `intent/INTENT-002.md:L115#Do not add agents`; `intent/current-feature.md:L51#No new infrastructure` | VERIFIED | |
| C-046 | Deployment target, production identity provider and users cannot be established from the repository. | UNKNOWN | INSUFFICIENT | MEDIUM | | QUALIFIED | Resolved by owner decision. |
| C-047 | Whether an independent assessor reaches the same conclusions cannot be established; this report and the baseline were produced by the authoring session. | UNKNOWN | INSUFFICIENT | HIGH | | QUALIFIED | Resolved by a RepoIntent run from a fresh session. |

## 16. Next Inspection Targets
| Target | Uncertainty it resolves | Value |
|---|---|---|
| `make check` at `9dc9298` or its CI run | whether recorded results reproduce [C-029] | turns QUALIFIED claims into verified ones |
| Live Claude Code session with a blank intent | hook behaviour in the real runtime [C-026] | confirms the governance fix end to end |
| Container build in CI | delivery path [C-033] | the cheapest remaining Radius 4 evidence |

## 17. What I would verify before repeating this in an architecture meeting.
1. **"Agents can't grant themselves tools."** [C-010, C-011, C-013] Could change: in-process code can still reach the executor (documented). Cheapest check: run `tests/test_tool_policy.py`.
2. **"Logs can't be matched to user names."** [C-015, C-016] Could change: anyone with the pseudonym key or the JWT secret can recompute. Cheapest check: confirm who holds `IAT_JWT_SECRET` and whether `IAT_SUBJECT_PSEUDONYM_KEY` is set separately.
3. **"Memory is bounded."** [C-021, C-022, C-038] Could change: bounds are per process; the default ceiling is tens of megabytes of text. Cheapest check: run the load test and size the defaults for the deployment.
4. **"120 tests pass."** [C-029, C-036] Could change: recorded artifact; README says 119. Cheapest check: the CI run for `9dc9298`.
5. **"Still Radius 3."** [C-033, C-047] Could change: same-session assessor; container unbuilt. Cheapest check: an independent RepoIntent run and a CI container job.
