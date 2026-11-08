"""Tool contract.

A tool declares a name, a description, a Pydantic input model and an output model. That is
exactly the information an MCP ``tools/list`` entry needs (name, description, JSON Schema for
input), so an MCP adapter can wrap any registered tool — or expose a remote MCP tool as an IAT
tool — without changing agents. See ``Tool.spec()``.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, ClassVar, Generic, TypeVar

from pydantic import BaseModel

from iat.schemas.execution import ToolStatus

InputT = TypeVar("InputT", bound=BaseModel)
OutputT = TypeVar("OutputT", bound=BaseModel)


class ToolSpec(BaseModel):
    name: str
    description: str
    read_only: bool
    input_schema: dict[str, Any]


class Tool(ABC, Generic[InputT, OutputT]):
    name: ClassVar[str]
    description: ClassVar[str]
    read_only: ClassVar[bool]
    input_model: ClassVar[type[BaseModel]]
    output_model: ClassVar[type[BaseModel]]

    @abstractmethod
    def run(self, args: InputT) -> OutputT: ...

    @classmethod
    def spec(cls) -> ToolSpec:
        return ToolSpec(
            name=cls.name,
            description=cls.description,
            read_only=cls.read_only,
            input_schema=cls.input_model.model_json_schema(),
        )


class ToolResult(BaseModel):
    tool: str
    status: ToolStatus
    output: dict[str, Any] | None = None
    error: str | None = None

    @property
    def ok(self) -> bool:
        return self.status is ToolStatus.OK
