"""Agent registry.

Pattern credit: the keyed agent registry with descriptions comes from agent-service-toolkit
(``src/agents/agents.py``). IAT adds a per-agent tool allowlist and a declared output model so
every agent's result is validated structurally before it leaves the runner.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from langgraph.graph.state import CompiledStateGraph
from pydantic import BaseModel

from iat.agents.supplier_readiness import graph as supplier
from iat.agents.supplier_readiness.narrator import Narrator, TemplateNarrator
from iat.schemas.api import AgentInfo
from iat.schemas.assessment import SupplierAssessment


@dataclass(frozen=True)
class AgentDefinition:
    key: str
    description: str
    allowed_tools: frozenset[str]
    graph: CompiledStateGraph[Any, Any, Any, Any]
    output_key: str
    output_model: type[BaseModel]

    def info(self) -> AgentInfo:
        return AgentInfo(
            key=self.key, description=self.description, allowed_tools=sorted(self.allowed_tools)
        )


class AgentRegistry:
    def __init__(self, agents: list[AgentDefinition]) -> None:
        self._agents = {a.key: a for a in agents}

    def get(self, key: str) -> AgentDefinition | None:
        return self._agents.get(key)

    def all(self) -> list[AgentDefinition]:
        return [self._agents[k] for k in sorted(self._agents)]


def default_agents(narrator: Narrator | None = None) -> list[AgentDefinition]:
    return [
        AgentDefinition(
            key=supplier.AGENT_KEY,
            description=(
                "Assesses whether a supplier is ready for onboarding using only the evidence on "
                "file. Decisions: READY, NOT_READY, INSUFFICIENT_EVIDENCE."
            ),
            allowed_tools=supplier.ALLOWED_TOOLS,
            graph=supplier.build_graph(narrator or TemplateNarrator()),
            output_key="assessment",
            output_model=SupplierAssessment,
        )
    ]
