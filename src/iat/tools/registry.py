"""Tool registry, authoritative tool policy, and governed executor.

Every tool call goes through ``ToolExecutor``, which enforces, in order:

1. the tool is registered (unregistered tools are denied),
2. the *registered* policy for the executing agent permits it,
3. the arguments validate against the tool's input model,
4. the output validates against the tool's output model.

Permissions come from ``ToolPolicy``, built once at startup from agent registrations and frozen.
Agents never pass an allowlist or their own name: the runner binds an ``AgentToolGateway`` to the
agent it resolved from the registry, and the gateway's ``invoke`` accepts only a tool name and
arguments. (INTENT-002 finding A: in INTENT-001 the caller supplied ``allowed_tools``.)

Each attempt — allowed or denied — is recorded as execution evidence. Failures never raise into
the agent; they come back as a structured ``ToolResult`` so the agent can fail closed.
"""

from __future__ import annotations

import logging
import time
from collections.abc import Iterable, Mapping
from types import MappingProxyType
from typing import Any

from pydantic import BaseModel, ValidationError

from iat.schemas.execution import ToolInvocationRecord, ToolStatus
from iat.tools.base import Tool, ToolResult, ToolSpec

logger = logging.getLogger("iat.tools")

AnyTool = Tool[Any, Any]


class ToolRegistry:
    def __init__(self, tools: Iterable[AnyTool] = ()) -> None:
        self._tools: dict[str, AnyTool] = {}
        for tool in tools:
            self.register(tool)

    def register(self, tool: AnyTool) -> None:
        if tool.name in self._tools:
            raise ValueError(f"Tool already registered: {tool.name}")
        self._tools[tool.name] = tool

    def get(self, name: str) -> AnyTool | None:
        return self._tools.get(name)

    def names(self) -> list[str]:
        return sorted(self._tools)

    def specs(self) -> list[ToolSpec]:
        return [self._tools[n].spec() for n in self.names()]


class ToolPolicy:
    """Authoritative, immutable map of agent key -> permitted tool names.

    Built from registrations at startup. Every permitted tool must be registered, so a typo or a
    missing tool fails at startup rather than at call time.
    """

    def __init__(self, grants: Mapping[str, Iterable[str]], registry: ToolRegistry) -> None:
        frozen = {agent: frozenset(tools) for agent, tools in grants.items()}
        for agent, tools in frozen.items():
            unknown = sorted(t for t in tools if registry.get(t) is None)
            if unknown:
                raise ValueError(f"Agent '{agent}' is granted unregistered tools: {unknown}")
        self._grants: Mapping[str, frozenset[str]] = MappingProxyType(frozen)

    def permits(self, agent: str, tool_name: str) -> bool:
        return tool_name in self._grants.get(agent, frozenset())

    def granted(self, agent: str) -> frozenset[str]:
        return self._grants.get(agent, frozenset())


class ExecutionRecorder:
    """Collects tool invocation evidence for one agent execution."""

    def __init__(self) -> None:
        self.records: list[ToolInvocationRecord] = []

    def add(self, record: ToolInvocationRecord) -> None:
        self.records.append(record)


class AgentToolGateway:
    """The only tool interface an agent receives. Bound by the runner to one agent and one run."""

    __slots__ = ("_agent", "_executor", "_recorder")

    def __init__(self, executor: ToolExecutor, agent: str, recorder: ExecutionRecorder) -> None:
        self._executor = executor
        self._agent = agent
        self._recorder = recorder

    @property
    def agent(self) -> str:
        return self._agent

    def invoke(self, tool_name: str, args: Mapping[str, Any]) -> ToolResult:
        return self._executor.invoke(
            agent=self._agent, tool_name=tool_name, args=args, recorder=self._recorder
        )


class ToolExecutor:
    def __init__(self, registry: ToolRegistry, policy: ToolPolicy) -> None:
        self._registry = registry
        self._policy = policy

    def bind(self, agent: str, recorder: ExecutionRecorder) -> AgentToolGateway:
        return AgentToolGateway(self, agent, recorder)

    def invoke(
        self,
        *,
        agent: str,
        tool_name: str,
        args: Mapping[str, Any],
        recorder: ExecutionRecorder,
    ) -> ToolResult:
        started = time.perf_counter()
        result, error_class = self._invoke(agent, tool_name, args)
        duration_ms = round((time.perf_counter() - started) * 1000, 3)
        recorder.add(
            ToolInvocationRecord(
                tool=tool_name,
                status=result.status,
                duration_ms=duration_ms,
                error_class=error_class,
            )
        )
        logger.info(
            "tool_invocation",
            extra={
                "agent": agent,
                "tool": tool_name,
                "tool_status": result.status.value,
                "duration_ms": duration_ms,
            },
        )
        return result

    def _invoke(
        self, agent: str, tool_name: str, args: Mapping[str, Any]
    ) -> tuple[ToolResult, str | None]:
        tool = self._registry.get(tool_name)
        if tool is None:
            return self._denied(tool_name, "Tool is not registered"), "UnregisteredTool"
        if not self._policy.permits(agent, tool_name):
            return (
                self._denied(tool_name, f"Agent '{agent}' is not authorized for this tool"),
                "ToolNotAllowed",
            )
        try:
            parsed = tool.input_model.model_validate(dict(args))
        except ValidationError as exc:
            fields = sorted({".".join(str(p) for p in e["loc"]) for e in exc.errors()})
            return (
                ToolResult(
                    tool=tool_name,
                    status=ToolStatus.INVALID_INPUT,
                    error=f"Invalid input for fields: {', '.join(fields)}",
                ),
                "ValidationError",
            )
        try:
            output: BaseModel = tool.run(parsed)
            validated = tool.output_model.model_validate(output.model_dump())
        except Exception as exc:  # tool failures are contained, classified and recorded
            logger.warning(
                "tool_failed", extra={"tool": tool_name, "error_class": type(exc).__name__}
            )
            return (
                ToolResult(tool=tool_name, status=ToolStatus.ERROR, error="Tool execution failed"),
                type(exc).__name__,
            )
        return ToolResult(tool=tool_name, status=ToolStatus.OK, output=validated.model_dump()), None

    @staticmethod
    def _denied(tool_name: str, reason: str) -> ToolResult:
        return ToolResult(tool=tool_name, status=ToolStatus.DENIED, error=reason)
