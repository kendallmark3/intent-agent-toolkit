# INTENT-002 Results — Evidence-Driven Hardening

**Date:** 2026-11-08 · **Version:** 0.2.0 · **Baseline:** `8ecc05d` (INTENT-001)
**Environment:** Linux x86_64, Python 3.13.18, uv 0.11.32
**Input:** [docs/assessments/INTENT-001-BASELINE.md](assessments/INTENT-001-BASELINE.md) — RepoIntent self-assessment, preserved verbatim (SHA-256 recorded in its header)

Every result below comes from a command executed in this environment. Raw output is in
[`docs/evidence/intent-002/`](evidence/intent-002/).

## Step 0 — Baseline numbers reproduced

The assessment reported 75 tests, 97% coverage and a 5/5 demo, and flagged them as not re-run.
They were re-run at `8ecc05d` before any change:

| Check | Result |
|---|---|
| `make check` (ruff, format, mypy strict, bandit, pip-audit, pytest, intent gate) | exit 0 |
| `pytest` | **75 passed** |
| Coverage | **97%** (850 statements) |
| `make demo` | **5/5** |

Source: `evidence/intent-002/baseline-reproduction.txt`. The INTENT-001 numbers are now reproduced,
not only recorded.

## Findings addressed

Each finding was first reproduced on the baseline commit, then the same scenario was run on the
new code (`evidence/intent-002/findings-baseline.txt`, `findings-current.txt`):

| Finding | Baseline (`8ecc05d`) | Now |
|---|---|---|
| **A** Agent supplies its own tool permissions | agent-supplied allowlist → `delete_supplier` **OK** | registered agent → **DENIED**; passing `allowed_tools` → `TypeError` (parameter no longer exists) |
| **B** Logged identifier is dictionary-reversible | `sha256("alice")[:16]` == logged value → **True** | → **False** (keyed HMAC) |
| **C** Unbounded conversation memory | 20,000 creates → **20,000** stored | → **50** stored, 19,950 evicted (per-owner cap) |
| **D1** `/v1/agents` has no scope check | any valid token | `agents:invoke` required (403 otherwise) |
| **D2** Intent gate not run during local editing | plugin-only `hooks/hooks.json` (`CLAUDE_PLUGIN_ROOT`) | `.claude/settings.json` project hook runs `hooks/pre-implement-hook.sh` before code edits |
| **D3** Project intent is an empty template | blank | purpose, outcomes, constraints, progressions filled |
| **E** Found during validation (not in the assessment): `.env.example` setup fails at startup | blank `IAT_ASSESSMENT_DATE=` → validation error | blank values treated as unset; README path tested end to end |

### A — Registered permissions are authoritative

- `ToolPolicy` is built once at startup from `AgentDefinition.allowed_tools` (registration),
  checked against the tool registry (granting an unregistered tool fails startup), and frozen
  (`MappingProxyType`).
- The runner binds an `AgentToolGateway` to the agent it resolved from the registry. The gateway's
  only method is `invoke(tool_name, args)`. Agents no longer receive the executor, policy, or
  recorder, and cannot pass an agent name or permission list.
- Scope: this protects against agent-controlled **inputs** (arguments, graph state, future model
  output). It is not a sandbox against arbitrary Python running in the same process.

### B — Keyed pseudonyms

- `subject_hash` is now `HMAC-SHA256(key, subject)` truncated to 128 bits (32 hex characters).
- The key is `IAT_SUBJECT_PSEUDONYM_KEY` when set (minimum 32 characters). Otherwise it is derived
  from the JWT secret with a domain-separation label (`iat/subject-pseudonym/v1`), so no new
  required setting was added.
- The unkeyed `Identity.subject_hash` property was removed, so the old scheme cannot be used by
  accident.

### C — Bounded conversation memory

| Limit | Setting (`IAT_…`) | Default | At the limit |
|---|---|---|---|
| Total conversations | `MAX_CONVERSATIONS` | 1000 | evict least recently active |
| Per caller | `MAX_CONVERSATIONS_PER_OWNER` | 50 | evict that caller's least recently active |
| Turns per conversation | `MAX_TURNS_PER_CONVERSATION` | 40 | drop oldest, count in `dropped_turns` |
| Message size | `MAX_MESSAGE_CHARS` | 2000 (ceiling 8000) | 422 before any work or storage |
| Idle lifetime | `CONVERSATION_IDLE_TTL_SECONDS` | 3600 | removed; behaves as 404 |

The message limit is enforced in `AgentRunner`, so a future non-HTTP entry point (for example
AgentCore) inherits it. The clock is injectable, so the time-based tests are deterministic.

### D — Governance

- `GET /v1/agents` requires `agents:invoke`, because discovering agents is part of invoking them.
- `.claude/settings.json` wires the starter's existing hook for local Claude Code sessions. It only
  blocks non-Markdown edits while `intent/current-feature.md` is insufficient; with a sufficient
  intent there is no friction. `make check` and CI still run the gate. The plugin-only
  `hooks/hooks.json` was removed.
- `intent/project-intent.md` filled in from INTENT-001 and INTENT-002.

## Architectural decisions

1. **Policy from registration, enforced by binding.** Moving permission lookup into the executor
   alone would still have trusted the caller's `agent` name. Binding the agent identity in the
   runner removes both inputs from agent control.
2. **HMAC derived from the existing secret by default.** This avoids a new mandatory setting, and
   the explicit key lets operators rotate the JWT secret without breaking log correlation.
3. **Evict rather than reject at capacity, with a per-caller cap.** Rejecting new conversations
   would let one caller block everyone. Evicting least-recently-active with a per-owner cap keeps
   the service available and stops a single caller from flushing others. A coordinated multi-caller
   flood can still evict quiet users (see remaining risks).
4. **No new infrastructure.** No Redis or Postgres; the bounds are in the existing in-memory store.

## Public behaviour changes

| Change | Why |
|---|---|
| `GET /v1/agents` needs `agents:invoke` (403 for tokens with only `conversations:read`) | Finding D1 |
| `execution.subject_hash` is 32 hex characters and its values differ from v0.1 | Finding B |
| `ConversationView` gains `dropped_turns` (additive) | Finding C |
| Conversations idle for more than 1 hour now return 404 | Finding C |
| Oversized message error text is now "Message exceeds N characters" (still 422 `VALIDATION_ERROR`) | Configurable limit enforced in runner |
| Library API: `ToolExecutor(registry, policy)`, `executor.bind(agent, recorder)`; `allowed_tools` argument and `Identity.subject_hash` removed | Finding A, B |

## Tests added (45 cases; suite 75 → 120)

| File | Functions / cases | Covers |
|---|---|---|
| `tests/test_tool_policy.py` | 10 / 10 | out-of-registration call denied and never executed; registered grant works; per-agent binding; agent sees only the gateway; gateway rejects permission arguments; runtime change to the agent constant grants nothing; unknown agent has no grants; startup rejects unregistered grants; policy immutable |
| `tests/test_pseudonym.py` | 9 / 9 | differs from the INTENT-001 hash; dictionary attack (sha256/sha1/md5/sha512, truncations, wrong key) finds no match; correlation; key separation; derivation; explicit key; short key rejected; key never rendered; log and response carry only the pseudonym |
| `tests/test_conversation_bounds.py` | 13 / 17 | global LRU eviction; per-owner cap protects others; 5,000-create load stays at cap with a consistent owner index; turn window; message size in runner and API; hard ceiling; idle expiry boundary; writes refresh TTL, reads do not; expired conversation cannot be continued; invalid limits rejected; settings reach the repository; `dropped_turns` over HTTP |
| `tests/test_governance.py` | 6 / 8 | agent listing scope; project hook wired with `CLAUDE_PROJECT_DIR`; hook passes with current intent; hook blocks code (not Markdown) with a blank intent; plugin-only config removed; project intent sections filled |
| `tests/test_startup_and_health.py` | +1 | `.env.example` → `.env` → start (verified to **fail** without the fix and pass with it) |

Existing tests were migrated to the new tool API through one helper (`tests/conftest.py::build_runner`)
that wires policy exactly as the app factory does.

## Actual results

| Check | Command | Result |
|---|---|---|
| Lint + format | `ruff check .`, `ruff format --check .` | pass; 76 files formatted |
| Types | `mypy` (strict) | pass; 33 source files |
| Static security | `bandit -r src` | no issues (0 medium, 0 high), 1,563 lines |
| Dependencies | `pip-audit` (runtime lock) | no known vulnerabilities |
| Tests | `pytest` | **120 passed, 0 failed, 0 errors** (`test-results.xml`) |
| Coverage | `pytest --cov=iat` | **97%** of 991 statements |
| Intent gate | `make intent` | sufficient; 15/15 shell tests |
| Demo | `make demo` | **5/5**, same decisions as INTENT-001 |
| Full gate | `make check` | exit 0 |
| Live server | `iat-serve` + curl, `IAT_MAX_MESSAGE_CHARS=200`, `IAT_MAX_TURNS_PER_CONVERSATION=2` | ready 200; unauthenticated 401; list agents 403 (read scope) / 200 (invoke); Acme READY with 32-character pseudonym; 201-character message 422; window 2 → 2 turns kept, 2 dropped; bob reading alice's conversation 404; `sha256("alice")[:16]`, raw `alice`, and the token each appear **0** times in the server log |

Validation requirements from INTENT-002 §5: 1 unauthorized tools denied ✔ · 2 authorized tools work ✔ ·
3 identifiers protected ✔ · 4 memory bounded ✔ · 5 supplier examples unchanged ✔ ·
6 authentication and isolation intact ✔ · 7 lint and types pass ✔.

**Not executed:** container build (no Docker daemon in this environment); CI on GitHub for these
changes (not pushed); a fresh RepoIntent assessment (deliberately left for an independent session).

## Remaining risks

1. **Coordinated eviction.** Many callers together can push a quiet user's conversations out at
   global capacity. Mitigation options: per-caller rate limiting at a gateway, or a durable store.
2. **Pseudonym key custody.** Anyone with the key (or the JWT secret, when derived) can recompute
   pseudonyms. Rotation breaks correlation with older logs.
3. **In-process trust.** The tool gateway stops agent-controlled inputs, not malicious code in the
   same process.
4. **Per-process state.** Bounds apply per worker; N workers hold up to N × the configured limits.
5. **Evict-after-run race.** A conversation evicted while an agent runs (only possible under extreme
   churn, since `ensure` refreshes it first) returns 404 after the run is recorded.

## Known limitations

Unchanged from INTENT-001 unless noted: local HMAC tokens only (no IdP); no rate limiting;
in-memory conversations (now bounded) lost on restart; no LLM in the decision path; supplier
extraction needs "supplier" plus a capitalised name or an id; Docker image not built; no
deployment.

## Recommended next progression

As agreed in INTENT-002's closing notes, and in this order:

1. **Independent RepoIntent run** from a fresh session against the INTENT-002 commit. It resolves
   the self-assessment caveat, and should confirm findings A–D are closed and look for new ones.
2. **Container build and run in CI** (build the image, start it, check `/health/ready` 200 and
   unauthenticated 401). This converts the last unverified INTENT-001 claim into runtime evidence.

INTENT-003 has not been started.
