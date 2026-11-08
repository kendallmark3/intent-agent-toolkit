"""Error taxonomy. Every API error is returned in one envelope with a stable code."""

from __future__ import annotations

from enum import StrEnum


class ErrorCode(StrEnum):
    UNAUTHENTICATED = "UNAUTHENTICATED"
    FORBIDDEN = "FORBIDDEN"
    NOT_FOUND = "NOT_FOUND"
    VALIDATION_ERROR = "VALIDATION_ERROR"
    AGENT_EXECUTION_FAILED = "AGENT_EXECUTION_FAILED"
    INTERNAL_ERROR = "INTERNAL_ERROR"


class IATError(Exception):
    status_code = 500
    code = ErrorCode.INTERNAL_ERROR

    def __init__(self, message: str, *, execution_id: str | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.execution_id = execution_id


class AuthenticationError(IATError):
    status_code = 401
    code = ErrorCode.UNAUTHENTICATED


class AuthorizationError(IATError):
    status_code = 403
    code = ErrorCode.FORBIDDEN


class NotFoundError(IATError):
    status_code = 404
    code = ErrorCode.NOT_FOUND


class InputValidationError(IATError):
    status_code = 422
    code = ErrorCode.VALIDATION_ERROR


class AgentExecutionError(IATError):
    status_code = 500
    code = ErrorCode.AGENT_EXECUTION_FAILED
