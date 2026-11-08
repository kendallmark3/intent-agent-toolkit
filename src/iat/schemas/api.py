"""HTTP request/response models."""

from __future__ import annotations

import datetime as dt
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from iat.schemas.assessment import SupplierAssessment
from iat.schemas.execution import ExecutionRecord


class InvokeRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    message: str = Field(min_length=1, max_length=2000, examples=["Can Supplier Acme be approved?"])
    conversation_id: str | None = Field(
        default=None,
        pattern=r"^[0-9a-f]{32}$",
        description="Continue an existing conversation you own. Omit to start a new one.",
    )


class InvokeResponse(BaseModel):
    conversation_id: str
    request_id: str | None
    output: SupplierAssessment
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


class ConversationSummary(BaseModel):
    conversation_id: str
    agent: str
    created_at: dt.datetime
    turn_count: int


class AgentInfo(BaseModel):
    key: str
    description: str
    allowed_tools: list[str]


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
