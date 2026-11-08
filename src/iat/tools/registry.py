"""Tool registry and governed executor.

Every tool call goes through ``ToolExecutor.invoke``, which enforces, in order:

1. the tool is registered (unregistered tools are denied),
2. the calling agent is allowed to use it (per-agent allowlist),
3. the arguments validate against the tool's input model,
4. the output validates against the tool's output model.

Each attempt — allowed or denied — is recorded as execution evidence. Failures never raise
into the agent; they come back as a structured ``ToolResult`` so the agent can fail closed.
"""

from __future__ import annotations

import logging
import time
from collections.abc import Iterable, Mapping
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


class ExecutionRecorder:
    """Collects tool invocation evidence for one agent execution."""

    def __init__(self) -> None:
        self.records: list[ToolInvocationRecord] = []

    def add(self, record: ToolInvocationRecord) -> None:
        self.records.append(record)


class ToolExecutor:
    def __init__(self, registry: ToolRegistry) -> None:
        self._registry = registry

    def invoke(
        self,
        *,
        agent: str,
        allowed_tools: frozenset[str],
        tool_name: str,
        args: Mapping[str, Any],
        recorder: ExecutionRecorder,
    ) -> ToolResult:
        started = time.perf_counter()
        result, error_class = self._invoke(agent, allowed_tools, tool_name, args)
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
        self,
        agent: str,
        allowed_tools: frozenset[str],
        tool_name: str,
        args: Mapping[str, Any],
    ) -> tuple[ToolResult, str | None]:
        tool = self._registry.get(tool_name)
        if tool is None:
            return self._denied(tool_name, "Tool is not registered"), "UnregisteredTool"
        if tool_name not in allowed_tools:
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
