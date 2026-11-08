# AWS Bedrock AgentCore — Future Integration Boundary

LangGraph is IAT's **orchestration framework**. Amazon Bedrock AgentCore is a **managed runtime
and infrastructure platform** for agents. They are complementary: AgentCore would host and
govern IAT agents; it would not replace the graph. Nothing in v0.1 depends on AWS.

## Runtime contract (as documented by AWS, checked 2026-11-08)

AgentCore Runtime's HTTP protocol expects an ARM64 container listening on `0.0.0.0:8080`
exposing `POST /invocations` (JSON in, JSON/SSE out) and `GET /ping` (`Healthy` / `HealthyBusy`),
with the session id supplied in `X-Amzn-Bedrock-AgentCore-Runtime-Session-Id`. Inbound auth is
OAuth bearer (JWT authorizer) or SigV4.
Source: [HTTP protocol contract](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/runtime-http-protocol-contract.html).
Re-verify before INTENT-004; the service is evolving.

## How IAT maps onto it

| AgentCore capability | IAT seam today | Integration work |
|---|---|---|
| Runtime | `AgentRunner.run()` has no HTTP dependency | Thin adapter: `/invocations` → `runner.run(...)`; `/ping` → readiness checks; port 8080; ARM64 build |
| Identity (inbound) | `TokenVerifier` protocol | `OidcVerifier` against the AgentCore/IdP JWKS; map `sub` + scopes to `Identity` |
| Gateway (governed tools) | `Tool.spec()` emits MCP-shaped JSON Schema; `ToolExecutor` enforces the registration-derived `ToolPolicy` | Remote-tool adapter implementing `Tool`; executor policy unchanged |
| Model gateway | `Narrator` port (no model in v0.1) | Model-backed narrator/extractor nodes calling Bedrock via gateway |
| Memory | `ConversationRepository` protocol | AgentCore Memory or Postgres implementation |
| Observability | `ExecutionRecord` JSON logs, request ids | Emit as OpenTelemetry spans/attributes |
| Session | server-generated `conversation_id` | Map AgentCore session id → conversation id under the verified owner |

## Rules for keeping the door open

1. Agents and tools must not import FastAPI, boto3 or AgentCore SDKs.
2. All execution goes through `AgentRunner` so identity and evidence apply on every host.
3. Health must stay honest — AgentCore uses `/ping` for recovery decisions.
4. Add AWS dependencies only in an adapter package when INTENT-004 begins.
