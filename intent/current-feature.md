# Current Feature — INTENT-001: Foundation and Working Reference
<!-- Full intent text: intent/INTENT-001.md. Append deltas below; do not rewrite this intent. -->

## Outcome
A working, independently maintainable Intent Agent Toolkit (Python / FastAPI / LangGraph) that runs one
reference agent — Supplier Readiness Assessment — behind an authenticated, owner-scoped API, with
registered read-only tools, structured execution evidence, and deterministic tests.

## Inputs
- Three MIT-licensed source repositories (agent-service-toolkit, fastapi-langgraph-agent-production-ready-template,
  ai-agents-masterclass) used as engineering evidence, not code to merge.
- Synthetic supplier data only.

## Outputs
- Runnable service with OpenAPI docs, health reporting, structured requests/responses.
- Supplier assessment: supplier id, decision (READY / NOT_READY / INSUFFICIENT_EVIDENCE), supporting evidence,
  missing evidence, explanation, execution id.
- docs/ARCHITECTURE.md, SOURCE_DECISIONS.md, SECURITY.md, AGENTCORE_FUTURE.md, IMPLEMENTATION_REPORT.md.

## Success / Evidence
- Automated tests pass without a live LLM; lint and static checks pass.
- Protected endpoints reject unauthenticated calls; cross-user conversation access is denied.
- Missing evidence is reported, never invented; unregistered tools are denied.
- Implementation report records only checks that were actually executed.

## Constraints / Boundaries
- No AWS deployment or AWS dependencies in this progression.
- No credentials in the repository; no secrets or message content in logs.
- No multi-agent orchestration; minimum sufficient architecture.
