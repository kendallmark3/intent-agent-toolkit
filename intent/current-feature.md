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

---

# Delta 1 — INTENT-002: Evidence-Driven Hardening
<!-- Full text: intent/INTENT-002.md. Baseline assessment: docs/assessments/INTENT-001-BASELINE.md -->

## Observation
RepoIntent self-assessment of INTENT-001 (Radius 3/5, partial 4) found: agents supply their own tool allowlist to the
executor; logged user identifiers are unsalted truncated SHA-256 (dictionary-reversible); in-memory conversations are
unbounded; `/v1/agents` has no scope check; the intent gate does not run during local editing; project intent is blank.

## Keep
FastAPI + LangGraph architecture, public API behaviour, fail-closed auth, owner isolation, deterministic rules, tests.

## Change
- Tool permissions derive from the agent registry, bound to the executing agent by the runner — not from agent code.
- Logged user identifiers become keyed pseudonyms.
- Conversations are bounded by count, per-owner count, turns, message size and idle lifetime (configurable).
- Listing agents requires a scope; intent gate wired for local Claude Code sessions; project intent filled in.

## New Boundary
No new infrastructure (no Redis/Postgres), no new agents, no cloud. Baseline assessment preserved unmodified.

## Evidence
Regression test per finding; full suite, lint, mypy strict, security scans and demo pass; results with real command
output in docs/INTENT-002-RESULTS.md.

---

# Delta 2 — INTENT-003: Run It (web console, workflow evidence, runtime proof)
<!-- Full text: intent/INTENT-003.md. Assessment at start: docs/assessments/INTENT-002-REPOINTENT.md -->

## Observation
v0.2 is hardened but only exercised through tests and curl. The container has never run; runtime
claims rest on recorded artifacts. The owner wants to run and see the agent from VS Code.

## Keep
Everything from INTENT-001/002: fail-closed auth, registration-derived tool policy, pseudonyms,
bounded memory, deterministic rules, tests.

## Change
- Web console at `/ui/` with form, workflow trace, evidence, regression panel and evidence download.
- Execution records include workflow steps; agents publish examples, workflow nodes, regression cases.
- Smoke script for any running deployment; CI builds, runs, and smoke-tests the container.
- VS Code setup; template guide for the next agent; README test-count drift fixed.

## New Boundary
No auth bypass or token-minting endpoint; console renders output as text only under a strict CSP.

## Evidence
Console exercised against a live server; regression cases pass via console/API/smoke/CI container;
full gate passes; results in docs/INTENT-003-RESULTS.md.

## Delta 2a — independent assessment input (docs/assessments/INTENT-002-INDEPENDENT.md)

### Observation
A fresh-session RepoIntent run of v0.2 (merged as PR #3 during this progression) agrees on Radius 3,
partial 4, and adds: HTTP output typed to one agent (C-026/027); docs on by default in the image
(C-033); base images tag-pinned (C-034); doc drift (C-029, C-038).

### Change
Agent-neutral invoke response proven with a second minimal agent over HTTP; docs off by default in
the container; Dependabot for Docker, Actions and uv; drift corrected.

### New Boundary
Digest pinning of base images is deferred (registry not reachable from the build environment).
