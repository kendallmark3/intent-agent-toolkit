# Security Model — v0.2

## Guarantees (each backed by tests)

| Guarantee | Mechanism | Test |
|---|---|---|
| No unauthenticated mode | `IAT_JWT_SECRET` required, ≥32 chars; startup fails otherwise | `test_startup_fails_closed_without_secret`, `test_startup_rejects_weak_secret` |
| Protected endpoints require a valid token | router-level `get_identity` dependency on `/v1/*` | `test_protected_endpoints_require_authentication` |
| Tokens are strictly verified | PyJWT, algorithm allowlist (HMAC only), required `exp iat sub iss aud`, issuer + audience match | `test_invalid_tokens_are_rejected` (wrong key, expired, wrong aud/iss, missing claims, `alg=none`, garbage) |
| Identity comes only from the token | request models forbid extra fields; no `user_id` input | `test_caller_cannot_assert_a_user_id` |
| Authorization from identity | scopes `agents:invoke` (invoke and list agents), `conversations:read` | scope tests, `test_listing_agents_requires_invoke_scope` |
| Cross-user isolation | conversations keyed to `sub`; foreign ids → identical 404 | `test_cross_user_conversation_isolation` |
| Tool authorization | `ToolPolicy` built from agent registrations and frozen at startup; agents get a runner-bound gateway and cannot supply permissions; denied calls never execute | `test_unregistered_tool_is_denied`, `test_agent_cannot_call_tool_outside_its_registration`, `test_changing_agent_constant_at_runtime_grants_nothing`, `test_policy_rejects_grants_for_unregistered_tools` |
| Tool input validation | Pydantic, `extra="forbid"`, length + character pattern | `test_tool_inputs_are_validated` |
| No secrets/content in logs | redacting JSON formatter; identity as keyed HMAC pseudonym; messages never logged | `test_logs_exclude_secrets_and_message_content`, `test_dictionary_attack_without_key_finds_no_match`, `test_logs_and_response_carry_keyed_pseudonym_only` |
| Bounded memory | conversation count, per-caller count, turns, message size, idle TTL | `tests/test_conversation_bounds.py` |
| No internals in errors | uniform envelope; validation errors list field names only | `test_agent_failure_returns_safe_envelope`, `test_validation_errors_do_not_echo_input` |
| Header injection safe | `X-Request-ID` accepted only if `[A-Za-z0-9._-]{8,64}` | `test_unsafe_request_id_is_replaced` |
| Fail closed on dependency failure | tool error → `INSUFFICIENT_EVIDENCE`, never `READY` | `test_agent_fails_closed_when_tool_fails` |

## Secrets

- No credentials are committed. `.env` is git-ignored; `.env.example` has empty values.
- Tests use a test-only constant; the demo generates an ephemeral secret at runtime.
- Static checks: `bandit` (no findings) and `pip-audit` (no known vulnerabilities) — see
  `docs/evidence/check-output.txt`.

## Enterprise identity integration boundary

`iat.security.identity.TokenVerifier` is the only seam:

```python
class TokenVerifier(Protocol):
    def verify(self, token: str) -> Identity: ...
```

To use an enterprise IdP (Entra ID, Okta, Cognito, AgentCore Identity), implement an
`OidcVerifier` that fetches JWKS from the issuer, verifies RS256/ES256 signatures, and maps the
provider's subject and scope/role claims to `Identity`. Pass it to `create_app(verifier=...)`.
Routes, runner, agents and tools do not change.

## Known limitations (accepted for v0.1)

- **Symmetric local tokens.** HMAC suits a single service; it is not a multi-party trust model.
  `iat-token` is a developer tool, not an issuer — do not expose it.
- **No token revocation** beyond expiry (default 60 minutes).
- **No rate limiting.** Intended to sit behind an API gateway / AgentCore, which enforces quotas
  per caller. Source B's in-process limiter was not adopted because its effectiveness depends on
  deployment topology.
- **In-memory conversations** are lost on restart and are per-process (not shared across workers).
  They are bounded (see ARCHITECTURE.md); at capacity the least recently active conversation is
  evicted, so under sustained load from many callers a quiet user's history can be evicted early.
  The per-caller cap stops one caller from evicting everyone else by itself, but many callers
  together still can.
- **Caller pseudonyms** are HMAC-SHA256 truncated to 128 bits. They resist dictionary hashing
  without the key, but anyone holding `IAT_SUBJECT_PSEUDONYM_KEY` (or, when it is unset, the JWT
  secret it is derived from) can recompute them. Rotating that key breaks correlation with older
  logs. This is pseudonymisation, not anonymisation.
- **Tool policy** protects against agent-controlled inputs. In-process code is trusted; the
  gateway is not a sandbox.
- **No TLS termination** in-process; deploy behind a TLS-terminating proxy.
- **Prompt injection** is not yet relevant (no LLM in the decision path). When an LLM node is
  added, keep it out of the decision path (see `Narrator`) and treat tool results as data.
