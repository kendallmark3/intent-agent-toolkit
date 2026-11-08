# INTENT-003 — Run It: Web Console, Workflow Evidence, and Runtime Proof

Project: Intent Agent Toolkit · Progression: 3 · Baseline: INTENT-002 (`cc01f2a`)
Assessment at baseline: Radius 3/5, partial Radius 4 (docs/assessments/INTENT-002-REPOINTENT.md)
Source: Mark's request, 2026-11-08 (captured below in his words, then structured).

## Human request (verbatim summary)

> The next step is to run this thing in Visual Studio Code. I see the curls, but I want a little
> website where I can call it: whatever inputs it needs on a simple form, call the agents, and show
> evidence and output on screen when it's finished so I know how it's doing. Get it close to
> production ready. This becomes the template for the next agents (onboarding, credit card). Move
> it closer to 4 out of 5. Regression testing, then AWS later.

## Outcome

A person can open the toolkit in VS Code, start it with one command, open a web console in the
browser, sign in with a token, run the supplier-readiness agent from a form, and see the decision,
the evidence, the workflow path the agent took, and the execution record. The same console runs the
agent's regression cases and lets the evidence be downloaded. The container image is built and
smoke-tested in CI with the same regression cases, so runtime behaviour is evidenced, not claimed.

## Inputs

- The INTENT-002 codebase and its v0.2 assessment.
- Synthetic supplier data only.

## Outputs

- Web console served by the service at `/ui/` (form, workflow trace, evidence, regression panel,
  evidence download).
- Workflow step trace in every execution record (node order and timing).
- Agent metadata for UIs: example inputs and workflow nodes.
- Regression cases owned by each agent definition, runnable through the API.
- A dependency-free smoke script that checks any running deployment (local, container, later AWS).
- CI job: build the container, run it, smoke-test it.
- VS Code launch, tasks, and recommended extensions.
- `docs/ADDING_AN_AGENT.md`: the template path for the next agent.
- `docs/INTENT-003-RESULTS.md` with real evidence.

## Success / Evidence

- The console works against a live server; a screenshot or recorded run proves it.
- Every regression case passes through the console, the API, the smoke script, and in CI against
  the built container.
- Security is unchanged or stronger: the console cannot bypass authentication; it renders untrusted
  output as text only; strict CSP on the console; security headers on all responses.
- Full gate passes (lint, strict types, scans, tests, intent gate, demo).

## Constraints / Boundaries

- No authentication bypass, no login endpoint that mints tokens, no "dev mode" without auth.
- No new frameworks or build tooling for the UI (plain HTML/CSS/JS served by FastAPI).
- No new agents in this progression; the template guide prepares for them.
- No AWS deployment yet.
- A higher Radius score is not a goal; runtime evidence is.
