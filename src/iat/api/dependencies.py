"""FastAPI dependencies: the container and the authenticated identity."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Annotated

from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from iat.agents.registry import AgentRegistry
from iat.core.config import Settings
from iat.core.errors import AuthenticationError
from iat.security.identity import Identity, TokenVerifier
from iat.services.conversations import ConversationRepository
from iat.services.runner import AgentRunner
from iat.services.supplier_repository import SupplierRepository
from iat.tools.registry import ToolRegistry


@dataclass(frozen=True)
class Container:
    settings: Settings
    verifier: TokenVerifier
    agents: AgentRegistry
    tools: ToolRegistry
    suppliers: SupplierRepository
    conversations: ConversationRepository
    runner: AgentRunner


def get_container(request: Request) -> Container:
    container: Container = request.app.state.container
    return container


_bearer = HTTPBearer(
    auto_error=False, description="JWT issued by the configured identity provider."
)


def get_identity(
    container: Annotated[Container, Depends(get_container)],
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)],
) -> Identity:
    # Fail closed: there is no configuration in which a protected route skips this check.
    if credentials is None or not credentials.credentials:
        raise AuthenticationError("Missing bearer token")
    return container.verifier.verify(credentials.credentials)


ContainerDep = Annotated[Container, Depends(get_container)]
IdentityDep = Annotated[Identity, Depends(get_identity)]
