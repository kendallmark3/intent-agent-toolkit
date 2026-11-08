INTENT-001: Intent Agent Toolkit — Foundation

Project: Intent Agent Toolkit (IAT)
Version: 0.1
Progression: 1 — Foundation and Working Reference
Methodology: Intent-Driven Engineering (IDE)
Architecture: Python / FastAPI / LangGraph
Future Platform: AWS Bedrock AgentCore
Status: Ready for Implementation

⸻

1. INTENT

Build the first working version of the Intent Agent Toolkit, a reusable, evidence-based foundation for developing, evaluating, and operating AI agents.

The toolkit will be constructed by evaluating and selectively incorporating the strongest engineering patterns from three previously assessed open-source repositories.

This is not an exercise in copying three repositories into one.

The objective is to produce a coherent, independently maintainable toolkit that demonstrates:

* Sound software engineering.
* Clean architecture.
* Reusable agent capabilities.
* Secure execution boundaries.
* Measurable agent behavior.
* Evidence-based validation.
* Progressive enterprise readiness.

The resulting toolkit should be suitable for demonstrating AI architecture principles and evolving toward enterprise deployment.

Success means having a working system that can be demonstrated, tested, analyzed with RepoIntent, and progressively improved.

⸻

2. SOURCE REPOSITORIES

Three repositories were previously evaluated using the RepoIntent architectural assessment workflow.

Use these assessments as initial evidence, not unquestionable conclusions.

SOURCE A — Primary Engineering Foundation

Repository:

https://github.com/JoshuaC215/agent-service-toolkit

Assessment:

Radius 3 of 5, with substantial Radius 4 capabilities.

Observed strengths:

* Python and FastAPI.
* LangGraph agent execution.
* Approximately 184 automated tests.
* GitHub Actions CI/CD.
* Container support.
* Multiple model providers.
* Configurable persistence.
* API client.
* Streamlit interface.
* MCP integration.

Known concerns:

* Authentication is optional.
* Shared API-key authentication is insufficient for enterprise authorization.
* User-supplied identifiers may permit cross-user conversation access.
* Some safety controls fail open.

Instruction:

Use this repository as the primary candidate for the toolkit’s foundational architecture.

Preserve its engineering strengths, but do not inherit known security weaknesses.

SOURCE B — Security and Operational Architecture Reference

Repository:

https://github.com/wassim249/fastapi-langgraph-agent-production-ready-template

Assessment:

Radius 3 of 5, with partial Radius 4 capabilities.

Observed strengths:

* JWT authentication.
* User accounts and session management.
* PostgreSQL persistence.
* Database migrations.
* Structured service layers.
* Model retries and fallback.
* Langfuse tracing.
* Prometheus/Grafana monitoring.
* Long-term memory.
* Rate limiting.

Known concerns:

* No automated tests identified.
* Some operational health endpoints are misleading.
* Rate limiting has deployment-dependent limitations.
* Multiple infrastructure dependencies increase complexity.

Instruction:

Study and selectively adopt useful patterns for authentication, authorization, persistence, observability, and service resilience.

Do not import the entire infrastructure stack without justification.

Every adopted capability must have automated validation.

SOURCE C — Agent Learning and Pattern Reference

Repository:

https://github.com/coleam00/ai-agents-masterclass

Assessment:

Radius 2 of 5.

Observed strengths:

* Simple agent examples.
* LangGraph orchestration patterns.
* Tool integrations.
* Multiple agent configurations.
* Educational reference implementations.

Known concerns:

* Independent examples rather than one coherent system.
* No automated tests identified.
* Some unsecured endpoints.
* Evaluation examples do not establish a complete automated scoring framework.

Instruction:

Use this repository to identify simple, understandable agent patterns.

Prefer its minimal examples when they provide equivalent capability with less complexity.

Do not adopt unverified code or instructional shortcuts as production architecture.

⸻

3. EXISTING EVIDENCE

The following RepoIntent reports may be available in the working environment:

repo-intent/reports/ai-agents-masterclass/REPORT.md
repo-intent/reports/agent-service-toolkit/REPORT.md
repo-intent/reports/fastapi-langgraph-template/REPORT.md

Locate and examine these reports before implementation.

Do not assume these relative paths exist in every environment.

If unavailable, inspect the upstream repositories directly and record the missing evidence.

The previous assessments produced:

* 72 architectural claims.
* 145 supporting citations.
* Zero citation-checker errors.

These results establish a useful starting point, not proof that the repositories are secure or production-ready.

Record the actual source commits examined during implementation.

Preserve source attribution and comply with applicable open-source licenses.

⸻

4. REQUIRED OUTPUT

Create a new project named:

intent-agent-toolkit

The first progression must produce a functioning, independently maintainable application.

At minimum, deliver the following capabilities.

A. Working Agent Service

A Python/FastAPI application capable of executing at least one LangGraph-based agent.

The service must support:

* Structured requests.
* Structured responses.
* Basic conversation handling.
* Error handling.
* Request identification.
* Health reporting.
* OpenAPI documentation.

The implementation must be runnable locally.

A real external LLM must not be required for automated tests.

B. Reference Agent

Implement one useful reference agent.

Reference use case: Supplier Readiness Assessment

The agent receives a supplier-onboarding question and examines available synthetic evidence.

Example:

“Can Supplier Acme be approved for onboarding?”

The agent should produce a structured assessment containing:

* Supplier identifier.
* Decision.
* Supporting evidence.
* Missing evidence.
* Explanation.
* Execution identifier.

Supported decisions:

* READY
* NOT_READY
* INSUFFICIENT_EVIDENCE

The agent must not fabricate missing information.

Use synthetic supplier data only.

A deterministic evaluator or mock model is acceptable for local demonstration.

The purpose is to demonstrate the toolkit’s engineering capabilities, not to create a complex supplier application.

C. Secure Execution Boundary

Implement a minimal but meaningful security model.

Requirements:

* Authentication enabled by default for protected endpoints.
* Authorization derived from validated identity.
* No trust in arbitrary caller-supplied user identifiers.
* Conversation access restricted to the authorized owner.
* Unauthorized access denied.
* No credentials committed to the repository.
* Sensitive data excluded from application logs.

Select the simplest appropriate implementation that can be tested.

Do not build an enterprise identity platform in this progression.

Document the integration boundary for future enterprise identity providers.

D. Agent Execution and Tools

Provide a clean mechanism for registering and invoking approved tools.

At minimum:

* Define a tool interface.
* Implement one read-only tool.
* Validate tool inputs.
* Return structured tool results.
* Record tool execution outcomes.
* Deny unregistered tools.

Design the interface so that a future MCP adapter can be introduced without redesigning the agent.

A full MCP server or enterprise capability registry is not required in V1.

E. Evidence and Observability

Each execution should generate useful diagnostic evidence.

Capture:

* Request ID.
* Agent execution ID.
* Selected agent.
* Tools invoked.
* Execution status.
* Duration.
* Error classification when applicable.

Provide structured logging.

Avoid recording secrets or unnecessary sensitive content.

Advanced distributed tracing is optional.

F. Automated Testing

Establish a meaningful test suite.

At minimum, test:

* Application startup.
* Health endpoint behavior.
* Authenticated requests.
* Unauthorized access.
* Cross-user conversation isolation.
* Agent execution.
* Tool authorization.
* Structured output validation.
* Missing evidence handling.
* Error handling.

Tests must be deterministic.

Use fake models and controlled synthetic data.

Do not depend on live paid model APIs for routine CI execution.

G. Developer Experience

Provide:

* Clear README.
* Installation instructions.
* Configuration example.
* Local startup command.
* Test command.
* API usage examples.
* Architecture overview.
* Known limitations.

A developer unfamiliar with the project should be able to run the reference application using the documented steps.

Prefer a simple local setup.

Docker support is desirable if it improves reproducibility, but unnecessary infrastructure must not be introduced solely to demonstrate sophistication.

⸻

5. ARCHITECTURAL BOUNDARIES

The toolkit must follow Intent-Driven Engineering and the Bitter Lesson.

The human defines outcomes, boundaries, and success criteria.

The implementation agent determines the most effective engineering approach.

Required principles

Minimum sufficient architecture

Implement only the components necessary to satisfy this progression.

Reuse before reinvention

Adapt well-designed patterns rather than unnecessarily rebuilding everything.

One coherent system

Do not concatenate three unrelated architectures.

Evidence before adoption

Validate borrowed functionality through tests and observable behavior.

Security by default

Do not expose unsafe endpoints for developer convenience.

Progressive enhancement

Keep extension points clear without prematurely implementing future capabilities.

Framework independence where practical

Avoid unnecessary coupling between business intent, agent logic, and infrastructure.

Deterministic enforcement

Use ordinary software validation for rules that do not require model reasoning.

No unnecessary agents

Do not introduce multiagent orchestration unless it provides a demonstrated benefit.

⸻

6. AGENTCORE COMPATIBILITY

AWS Bedrock AgentCore is a future deployment and governance consideration.

The toolkit should be designed to permit future integration with:

* AgentCore Runtime.
* Enterprise model gateways.
* Governed tool access.
* Identity and policy enforcement.
* Production observability.

However:

Do not deploy to AWS in this progression.

Do not introduce AWS dependencies solely for anticipated future requirements.

Keep agent execution reasonably isolated from the HTTP transport and deployment environment.

Document the future AgentCore integration boundary.

⸻

7. SOURCE SELECTION AND REUSE

Before implementing major components, compare the three repositories.

For each major architectural decision, determine:

1. Which source offers the strongest implementation?
2. What evidence supports that conclusion?
3. What weaknesses must be addressed?
4. Can a simpler implementation achieve the same outcome?
5. How will the selected implementation be validated?

Create:

docs/SOURCE_DECISIONS.md

Document significant source decisions and their rationale.

Do not import code merely because it exists in one of the repositories.

Prefer a cohesive design over maximizing code reuse.

Preserve required attribution and licenses.

⸻

8. VALIDATION AND SUCCESS CRITERIA

The first progression is complete when the following conditions are satisfied.

Functional

* The application starts successfully.
* The reference agent can be invoked.
* Supplier readiness assessment produces valid structured results.
* Missing evidence is reported rather than invented.
* Approved tools execute successfully.
* Unauthorized tool operations are denied.

Security

* Protected endpoints require authentication.
* Authorization is enforced.
* Cross-user access is denied.
* Sensitive configuration is externalized.
* Security tests pass.

Engineering

* Automated tests pass.
* Linting and static checks pass.
* Dependencies are reproducible.
* The codebase has a coherent architecture.
* Installation and execution are documented.

Evidence

* Source-selection decisions are recorded.
* Test results are available.
* Known limitations are documented.
* An implementation summary is produced.
* The application is ready for an independent RepoIntent assessment.

Important: A Radius 4 score is a desired future outcome, not permission to claim maturity that has not been demonstrated.

The next RepoIntent assessment determines the actual score.

⸻

9. EXPECTED PROJECT ARTIFACTS

The finished project should contain a coherent equivalent of:

intent-agent-toolkit/
│
├── README.md
├── pyproject.toml
├── .env.example
├── .gitignore
│
├── app/
│   ├── api/
│   ├── agents/
│   ├── tools/
│   ├── security/
│   ├── services/
│   ├── schemas/
│   └── core/
│
├── tests/
│
├── docs/
│   ├── ARCHITECTURE.md
│   ├── SOURCE_DECISIONS.md
│   ├── SECURITY.md
│   ├── AGENTCORE_FUTURE.md
│   └── IMPLEMENTATION_REPORT.md
│
├── examples/
│   └── supplier_readiness/
│
└── .github/
    └── workflows/

This is a suggested structure, not a mandatory design.

Modify it when a better architecture is justified.

⸻

10. IMPLEMENTATION REPORT

At completion, generate:

docs/IMPLEMENTATION_REPORT.md

Include:

What was built

A concise explanation of the functioning toolkit.

What was reused

Identify significant reused patterns and their source repositories.

What was deliberately excluded

Explain which capabilities were deferred and why.

Evidence

Report:

* Tests executed.
* Tests passed.
* Tests failed.
* Security checks performed.
* Build results.
* Known limitations.

Do not claim that tests passed unless they were actually executed.

How to run it

Provide exact commands.

Demonstration

Provide one reproducible supplier-readiness example with an expected result.

Next progression

Recommend the smallest useful improvement for INTENT-002.

Do not automatically implement INTENT-002.

⸻

11. STOP CONDITIONS

Stop and report clearly if:

* Required source repositories cannot be accessed.
* Licensing prevents intended reuse.
* A critical security weakness cannot be resolved.
* Required dependencies cannot be installed.
* Tests cannot run in the available environment.
* Implementation would require unapproved external credentials or infrastructure.

Do not bypass security requirements to make the demonstration work.

Do not fabricate successful execution evidence.

When a noncritical issue occurs, continue with the smallest safe alternative and document the deviation.

⸻

12. EXECUTION INSTRUCTION

You are responsible for producing the working first progression of the Intent Agent Toolkit.

Begin by examining the source repositories and available RepoIntent assessments.

Select the strongest reusable implementation patterns.

Then build the smallest coherent toolkit that satisfies the required outcomes.

Use existing working code where appropriate, but validate what you adopt.

Make reasonable engineering decisions independently.

Do not stop after creating an architectural plan.

Proceed through implementation, testing, documentation, and validation.

Do not build unnecessary capabilities merely to achieve a higher architectural maturity score.

Deliver working software, reproducible evidence, and a clear foundation for progressive improvement.

⸻

13. FINAL OBJECTIVE

Create something we can confidently demonstrate, explain, inspect, and extend.

It must be our own coherent engineering toolkit, grounded in three previously evaluated reference implementations.

Its value must come from demonstrated functionality and engineering quality, not architectural complexity.

Build the foundation. Prove it works. Document the evidence. Stop.

End of INTENT-001 — Progression 1
