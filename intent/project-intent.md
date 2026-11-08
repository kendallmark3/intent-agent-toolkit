# Project Intent — Intent Agent Toolkit (IAT)

Purpose:
A reusable, evidence-based foundation for developing, evaluating and operating AI agents
(Python · FastAPI · LangGraph), built in progressions and suitable for demonstrating AI
architecture principles while evolving toward enterprise deployment.

Business outcomes:
- A working agent service that can be demonstrated, tested, and explained to architects.
- Each progression produces reproducible evidence and is assessed with RepoIntent; findings
  feed the next intent (Intent → Implementation → Evidence → RepoIntent → Findings → Next intent).
- Patterns proven here can be carried into enterprise environments, including AWS Bedrock
  AgentCore, without redesigning agent logic.

Constraints:
- Security by default: authentication cannot be disabled; identity only from verified tokens;
  owner-scoped data; tools denied unless granted by registration; no secrets or message content
  in logs.
- Deterministic enforcement for rules, authorization and resource limits; models may explain,
  never decide, until an intent says otherwise.
- Minimum sufficient architecture: no infrastructure, agents or orchestration without
  demonstrated need. A higher Radius score is not a goal in itself.
- Synthetic data only until an intent introduces real data with its own controls.
- Source attribution preserved for adapted patterns (see THIRD_PARTY_NOTICES.md).

Progressions:
- INTENT-001 — Foundation and working reference (intent/INTENT-001.md).
- INTENT-002 — Evidence-driven hardening from the first RepoIntent assessment (intent/INTENT-002.md).
