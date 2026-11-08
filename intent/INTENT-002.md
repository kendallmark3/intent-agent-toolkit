INTENT-002: Evidence-Driven Hardening

Project: Intent Agent Toolkit
Progression: 2
Baseline: INTENT-001
Current assessment: Radius 3/5, partial Radius 4
Method: Intent-Driven Engineering
Status: Ready for implementation

1. Intent

Improve the existing Intent Agent Toolkit by correcting weaknesses identified through its first RepoIntent assessment.

Preserve the working architecture, existing functionality, and successful engineering practices.

This progression is not an architecture rewrite.

The objective is to close demonstrated gaps, strengthen validation, and produce independently verifiable evidence.

2. Inputs and evidence

Use the existing toolkit repository and the RepoIntent assessment located at:

repo-intent/reports/intent-agent-toolkit/REPORT.md

If the report is unavailable, use the findings provided below as the initial evidence and verify them against the code.

The assessment reported:

* Radius 3/5, partial Radius 4.
* 55 claims.
* 126 citations.
* Zero citation-checker errors.
* 75 tests reported.
* 97% coverage reported.
* Five successful demonstrations reported.

The tests, coverage, and demonstrations were not independently rerun during the assessment.

Treat those numbers as unverified until reproduced.

3. Required outcomes

A. Enforce registered agent permissions

Correct the authorization weakness in which agents supply their own tool permission lists.

The runtime must derive permitted tool access from an authoritative registration or policy mechanism.

An agent must not be able to grant itself additional tool permissions.

Add negative tests demonstrating that unauthorized tool calls fail even when the agent requests elevated permissions.

Success: Authorization is enforced independently of agent-controlled inputs.

B. Protect user identifiers

Examine the existing user-identifier logging mechanism.

Replace predictable, unsalted hashes with a privacy-preserving approach appropriate for operational correlation.

Avoid logging raw usernames or identifying information unnecessarily.

Document the limitations of the selected approach.

Success: Logged identifiers cannot be trivially correlated with known usernames through dictionary hashing.

C. Bound conversation memory

Eliminate unlimited in-memory conversation growth.

Establish configurable limits for:

* Conversation count.
* Messages retained per conversation.
* Message size.
* Idle conversation lifetime.

Ensure limits are enforced consistently.

Use deterministic tests to verify retention and cleanup behavior.

Do not introduce Redis, PostgreSQL, or another persistence service unless necessary to satisfy this progression.

Success: Conversation storage has demonstrable resource bounds.

D. Close minor governance gaps

Evaluate and address:

* Authorization requirements for listing available agents.
* The intent validation gate not executing during normal local development.
* The incomplete project intent template.

Implement minimal improvements appropriate to the existing architecture.

Do not impose unnecessary workflow restrictions.

E. Preserve the assessment

Copy the existing RepoIntent report into the toolkit documentation if accessible.

Suggested location:

docs/assessments/INTENT-001-BASELINE.md

Preserve the original findings and clearly label the assessment as a self-assessment based on static inspection.

Do not silently modify its findings after implementation.

4. Engineering constraints

* Preserve FastAPI and LangGraph.
* Maintain existing public behavior unless required for security.
* Do not add agents.
* Do not introduce unnecessary orchestration.
* Do not add infrastructure without demonstrated need.
* Use deterministic enforcement for authorization and resource limits.
* Preserve relevant source attribution.
* Prefer minimal changes to existing components.

Follow the Bitter Lesson: define outcomes and validation clearly while allowing implementation choices to emerge from evidence.

5. Validation requirements

Run the available automated test suite.

Add regression tests for every corrected weakness.

Verify:

1. Unauthorized agent tools are denied.
2. Authorized tools continue working.
3. User identifiers are protected.
4. Conversation memory remains bounded.
5. Existing supplier-readiness examples still work.
6. Authentication and user isolation remain intact.
7. Lint and type checks pass.

Record actual commands, results, failures, and limitations.

If dependencies or the execution environment prevent testing, report that explicitly.

Do not claim success based solely on code inspection.

6. Delivery evidence

Produce:

docs/INTENT-002-RESULTS.md

Include:

* Findings addressed.
* Files changed.
* Architectural decisions.
* Tests added.
* Actual test results.
* Remaining risks.
* Known limitations.
* Recommended next progression.

Do not automatically implement the next progression.

7. Stop condition

Stop when the identified findings are resolved, regression tests pass, and evidence is documented.

Do not expand the scope to introduce enterprise infrastructure, cloud deployment, or advanced agent capabilities.

Fix what the evidence revealed. Prove the fixes. Stop.
