"""HTTP routes. Health is public; everything under /v1 requires a verified identity."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Path, Request, Response, status

from iat import __version__
from iat.api.dependencies import ContainerDep, IdentityDep, get_identity
from iat.schemas.api import (
    AgentInfo,
    ConversationSummary,
    ConversationView,
    ErrorEnvelope,
    HealthResponse,
    InvokeRequest,
    InvokeResponse,
)
from iat.security.identity import SCOPE_INVOKE, SCOPE_READ_CONVERSATIONS

health_router = APIRouter(tags=["health"])

_ERRORS: dict[int | str, dict[str, object]] = {
    401: {"model": ErrorEnvelope, "description": "Missing or invalid token"},
    403: {"model": ErrorEnvelope, "description": "Token lacks the required scope"},
    404: {"model": ErrorEnvelope, "description": "Not found (or not owned by caller)"},
    422: {"model": ErrorEnvelope, "description": "Request validation failed"},
}

api_router = APIRouter(prefix="/v1", dependencies=[Depends(get_identity)], responses=_ERRORS)


@health_router.get("/health", response_model=HealthResponse)
def liveness() -> HealthResponse:
    """Liveness: the process is up and serving requests."""
    return HealthResponse(status="ok", version=__version__)


@health_router.get(
    "/health/ready",
    response_model=HealthResponse,
    responses={503: {"model": HealthResponse, "description": "Not ready"}},
)
def readiness(container: ContainerDep, response: Response) -> HealthResponse:
    """Readiness: reports the dependencies the reference agent actually needs."""
    checks = {
        "supplier_data_loaded": len(container.suppliers) > 0,
        "agents_registered": bool(container.agents.all()),
        "tools_registered": bool(container.tools.names()),
    }
    ok = all(checks.values())
    if not ok:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    return HealthResponse(status="ok" if ok else "degraded", version=__version__, checks=checks)


@api_router.get("/agents", response_model=list[AgentInfo], tags=["agents"])
def list_agents(container: ContainerDep) -> list[AgentInfo]:
    return [a.info() for a in container.agents.all()]


@api_router.post(
    "/agents/{agent_key}/invoke",
    response_model=InvokeResponse,
    tags=["agents"],
    responses={500: {"model": ErrorEnvelope, "description": "Agent execution failed"}},
)
def invoke_agent(
    body: InvokeRequest,
    request: Request,
    identity: IdentityDep,
    container: ContainerDep,
    agent_key: str = Path(pattern=r"^[a-z0-9\-]{1,64}$"),
) -> InvokeResponse:
    identity.require_scope(SCOPE_INVOKE)
    outcome = container.runner.run(
        agent_key=agent_key,
        message=body.message,
        identity=identity,
        request_id=getattr(request.state, "request_id", None),
        conversation_id=body.conversation_id,
    )
    return InvokeResponse.model_validate(
        {
            "conversation_id": outcome.conversation_id,
            "request_id": outcome.execution.request_id,
            "output": outcome.output.model_dump(),
            "execution": outcome.execution,
        }
    )


@api_router.get("/conversations", response_model=list[ConversationSummary], tags=["conversations"])
def list_conversations(identity: IdentityDep, container: ContainerDep) -> list[ConversationSummary]:
    identity.require_scope(SCOPE_READ_CONVERSATIONS)
    return container.conversations.list_for(identity)


@api_router.get(
    "/conversations/{conversation_id}", response_model=ConversationView, tags=["conversations"]
)
def get_conversation(
    identity: IdentityDep,
    container: ContainerDep,
    conversation_id: str = Path(pattern=r"^[0-9a-f]{32}$"),
) -> ConversationView:
    identity.require_scope(SCOPE_READ_CONVERSATIONS)
    return container.conversations.get(identity, conversation_id)
