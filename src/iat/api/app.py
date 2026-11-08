"""Application factory: wires settings, security, tools, agents and routes."""

from __future__ import annotations

import logging
import re
import uuid
from collections.abc import Awaitable, Callable

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.responses import Response

from iat import __version__
from iat.agents.registry import AgentDefinition, AgentRegistry, default_agents
from iat.api.dependencies import Container
from iat.api.routes import api_router, health_router
from iat.core.config import Settings, get_settings
from iat.core.errors import ErrorCode, IATError
from iat.core.logging import configure_logging, request_id_var
from iat.schemas.api import ErrorBody, ErrorEnvelope
from iat.security.identity import JwtVerifier, TokenVerifier
from iat.security.pseudonym import SubjectPseudonymizer, derive_key
from iat.services.conversations import ConversationLimits, InMemoryConversationRepository
from iat.services.runner import AgentRunner
from iat.services.supplier_repository import SupplierRepository
from iat.tools.registry import AnyTool, ToolExecutor, ToolPolicy, ToolRegistry
from iat.tools.supplier_evidence import SupplierEvidenceLookupTool

logger = logging.getLogger("iat.api")

REQUEST_ID_HEADER = "X-Request-ID"
_SAFE_REQUEST_ID = re.compile(r"^[A-Za-z0-9._\-]{8,64}$")


def _error(
    status_code: int,
    code: str,
    message: str,
    request: Request,
    execution_id: str | None = None,
    headers: dict[str, str] | None = None,
) -> JSONResponse:
    body = ErrorEnvelope(
        error=ErrorBody(
            code=code,
            message=message,
            request_id=getattr(request.state, "request_id", None),
            execution_id=execution_id,
        )
    )
    return JSONResponse(
        body.model_dump(exclude_none=True), status_code=status_code, headers=headers
    )


def create_app(
    settings: Settings | None = None,
    *,
    verifier: TokenVerifier | None = None,
    agents: list[AgentDefinition] | None = None,
    extra_tools: list[AnyTool] | None = None,
) -> FastAPI:
    settings = settings or get_settings()
    configure_logging(settings.log_level)

    suppliers = SupplierRepository.from_json(settings.supplier_data_path)
    tool_registry = ToolRegistry([SupplierEvidenceLookupTool(suppliers), *(extra_tools or [])])
    agent_registry = AgentRegistry(agents if agents is not None else default_agents())
    conversations = InMemoryConversationRepository(
        ConversationLimits(
            max_conversations=settings.max_conversations,
            max_conversations_per_owner=settings.max_conversations_per_owner,
            max_turns_per_conversation=settings.max_turns_per_conversation,
            max_message_chars=settings.max_message_chars,
            idle_ttl_seconds=settings.conversation_idle_ttl_seconds,
        )
    )
    # Tool permissions come only from agent registrations (INTENT-002 finding A).
    executor = ToolExecutor(tool_registry, ToolPolicy(agent_registry.tool_grants(), tool_registry))
    container = Container(
        settings=settings,
        verifier=verifier or JwtVerifier(settings),
        agents=agent_registry,
        tools=tool_registry,
        suppliers=suppliers,
        conversations=conversations,
        runner=AgentRunner(
            agent_registry,
            executor,
            conversations,
            settings.as_of,
            SubjectPseudonymizer(derive_key(settings.jwt_secret, settings.subject_pseudonym_key)),
        ),
    )

    app = FastAPI(
        title=settings.app_name,
        version=__version__,
        description="Intent Agent Toolkit — secure, evidence-producing agent service.",
        docs_url="/docs" if settings.docs_enabled else None,
        redoc_url=None,
        openapi_url="/openapi.json" if settings.docs_enabled else None,
    )
    app.state.container = container
    app.include_router(health_router)
    app.include_router(api_router)

    @app.middleware("http")
    async def request_context(
        request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        supplied = request.headers.get(REQUEST_ID_HEADER, "")
        request_id = supplied if _SAFE_REQUEST_ID.match(supplied) else uuid.uuid4().hex
        request.state.request_id = request_id
        token = request_id_var.set(request_id)
        try:
            response = await call_next(request)
        finally:
            request_id_var.reset(token)
        response.headers[REQUEST_ID_HEADER] = request_id
        return response

    @app.exception_handler(IATError)
    async def handle_iat_error(request: Request, exc: IATError) -> JSONResponse:
        headers = {"WWW-Authenticate": "Bearer"} if exc.status_code == 401 else None
        if exc.status_code >= 500:
            logger.error(
                "request_failed",
                extra={"error_code": exc.code.value, "execution_id": exc.execution_id},
            )
        return _error(
            exc.status_code, exc.code.value, exc.message, request, exc.execution_id, headers
        )

    @app.exception_handler(RequestValidationError)
    async def handle_validation(request: Request, exc: RequestValidationError) -> JSONResponse:
        # Report which fields failed, never the submitted values.
        fields = sorted({".".join(str(p) for p in e["loc"]) for e in exc.errors()})
        return _error(
            422, ErrorCode.VALIDATION_ERROR.value, f"Invalid fields: {', '.join(fields)}", request
        )

    @app.exception_handler(StarletteHTTPException)
    async def handle_http(request: Request, exc: StarletteHTTPException) -> JSONResponse:
        code = ErrorCode.NOT_FOUND if exc.status_code == 404 else ErrorCode.INTERNAL_ERROR
        return _error(exc.status_code, code.value, str(exc.detail), request)

    @app.exception_handler(Exception)
    async def handle_unexpected(request: Request, exc: Exception) -> JSONResponse:
        logger.error("unhandled_exception", extra={"error_class": type(exc).__name__})
        return _error(500, ErrorCode.INTERNAL_ERROR.value, "Internal server error", request)

    return app
