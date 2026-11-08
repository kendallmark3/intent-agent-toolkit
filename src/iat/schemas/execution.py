"""Execution evidence captured for every agent run."""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, Field


class ExecutionStatus(StrEnum):
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class ToolStatus(StrEnum):
    OK = "OK"
    DENIED = "DENIED"
    INVALID_INPUT = "INVALID_INPUT"
    ERROR = "ERROR"


class ToolInvocationRecord(BaseModel):
    tool: str
    status: ToolStatus
    duration_ms: float
    error_class: str | None = None


class ExecutionRecord(BaseModel):
    request_id: str | None
    execution_id: str
    agent: str
    subject_hash: str = Field(description="Non-reversible hash of the caller identity.")
    tools_invoked: list[ToolInvocationRecord] = Field(default_factory=list)
    status: ExecutionStatus
    duration_ms: float
    error_class: str | None = None
