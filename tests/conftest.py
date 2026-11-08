"""Shared fixtures. Everything is deterministic: fixed evaluation date, synthetic data, no LLM."""

from __future__ import annotations

import datetime as dt
from collections.abc import Callable, Iterator

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from pydantic import SecretStr

from iat.agents.registry import AgentDefinition, AgentRegistry, default_agents
from iat.api.app import create_app
from iat.core.config import Settings
from iat.security.dev_tokens import DEFAULT_SCOPES, issue_token
from iat.security.pseudonym import SubjectPseudonymizer
from iat.services.conversations import InMemoryConversationRepository
from iat.services.runner import AgentRunner
from iat.tools.registry import ToolExecutor, ToolPolicy, ToolRegistry

TEST_SECRET = "test-secret-" + "x" * 40  # test-only value, never used outside this suite
AS_OF = dt.date(2026, 11, 8)
INVOKE = "/v1/agents/supplier-readiness/invoke"


@pytest.fixture
def settings() -> Settings:
    return Settings(jwt_secret=SecretStr(TEST_SECRET), assessment_date=AS_OF, _env_file=None)  # type: ignore[call-arg]


@pytest.fixture
def app(settings: Settings) -> FastAPI:
    return create_app(settings)


@pytest.fixture
def client(app: FastAPI) -> Iterator[TestClient]:
    with TestClient(app) as test_client:
        yield test_client


def build_runner(
    tools: ToolRegistry,
    agents: list[AgentDefinition] | None = None,
    conversations: InMemoryConversationRepository | None = None,
) -> AgentRunner:
    """Runner wired exactly as the app factory wires it: policy from agent registrations."""
    registry = AgentRegistry(agents if agents is not None else default_agents())
    executor = ToolExecutor(tools, ToolPolicy(registry.tool_grants(), tools))
    return AgentRunner(
        registry,
        executor,
        conversations if conversations is not None else InMemoryConversationRepository(),
        lambda: AS_OF,
        SubjectPseudonymizer(b"k" * 32),
    )


TokenFactory = Callable[..., str]


@pytest.fixture
def make_token(settings: Settings) -> TokenFactory:
    def _make(subject: str = "alice", scopes: str = DEFAULT_SCOPES, **kwargs: object) -> str:
        return issue_token(settings, subject, scopes, **kwargs)  # type: ignore[arg-type]

    return _make


@pytest.fixture
def auth(make_token: TokenFactory) -> Callable[[str], dict[str, str]]:
    def _auth(subject: str = "alice") -> dict[str, str]:
        return {"Authorization": f"Bearer {make_token(subject)}"}

    return _auth
