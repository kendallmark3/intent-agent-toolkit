"""HTTP request/response models."""

from __future__ import annotations

import datetime as dt
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from iat.core.config import MESSAGE_HARD_CEILING
from iat.schemas.execution import ExecutionRecord


class InvokeRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    message: str = Field(
        min_length=1,
        max_length=MESSAGE_HARD_CEILING,
        description="The configured limit (IAT_MAX_MESSAGE_CHARS, default 2000) is enforced "
        "by the runner; this is the absolute ceiling.",
        examples=["Can Supplier Acme be approved?"],
    )
    conversation_id: str | None = Field(
        default=None,
        pattern=r"^[0-9a-f]{32}$",
        description="Continue an existing conversation you own. Omit to start a new one.",
    )


class InvokeResponse(BaseModel):
    """Agent-neutral envelope. ``output`` is the invoked agent's own output model, already
    validated by the runner against ``AgentDefinition.output_model`` (independent finding C-026)."""

    conversation_id: str
    request_id: str | None
    output: dict[str, Any] = Field(
        description="The agent's structured output; its schema depends on the agent "
        "(supplier-readiness returns a SupplierAssessment)."
    )
    execution: ExecutionRecord


class Turn(BaseModel):
    role: Literal["user", "agent"]
    content: str
    execution_id: str | None = None
    output: dict[str, Any] | None = None
    at: dt.datetime


class ConversationView(BaseModel):
    conversation_id: str
    agent: str
    created_at: dt.datetime
    turns: list[Turn]
    dropped_turns: int = Field(
        default=0, description="Older turns removed by the per-conversation retention window."
    )


class ConversationSummary(BaseModel):
    conversation_id: str
    agent: str
    created_at: dt.datetime
    turn_count: int


class AgentInfo(BaseModel):
    key: str
    description: str
    allowed_tools: list[str]
    workflow: list[str] = Field(
        default_factory=list, description="Graph nodes, in definition order."
    )
    examples: list[str] = Field(default_factory=list, description="Example inputs for UIs.")
    regression_cases: int = 0


class RegressionCaseResult(BaseModel):
    name: str
    message: str
    passed: bool
    expected: dict[str, Any]
    actual: dict[str, Any]
    execution_id: str | None = None
    duration_ms: float
    error: str | None = None


class RegressionReport(BaseModel):
    agent: str
    version: str
    request_id: str | None
    started_at: dt.datetime
    total: int
    passed: int
    failed: int
    cases: list[RegressionCaseResult]


class HealthResponse(BaseModel):
    status: Literal["ok", "degraded"]
    version: str
    checks: dict[str, bool] = Field(default_factory=dict)


class ErrorBody(BaseModel):
    code: str
    message: str
    request_id: str | None = None
    execution_id: str | None = None


class ErrorEnvelope(BaseModel):
    error: ErrorBody
