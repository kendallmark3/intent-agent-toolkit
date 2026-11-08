"""INTENT-002 finding C: conversation storage has demonstrable, configurable resource bounds.

All time-based tests use a fake clock, so they are deterministic and instantaneous.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from pydantic import SecretStr, ValidationError

from iat.api.app import create_app
from iat.core.config import Settings
from iat.core.errors import InputValidationError, NotFoundError
from iat.security.identity import Identity
from iat.services.conversations import ConversationLimits, InMemoryConversationRepository, turn
from iat.services.supplier_repository import SupplierRepository
from iat.tools.registry import ToolRegistry
from iat.tools.supplier_evidence import SupplierEvidenceLookupTool
from tests.conftest import AS_OF, INVOKE, TEST_SECRET, TokenFactory, build_runner

ALICE, BOB = Identity("alice"), Identity("bob")
AGENT = "supplier-readiness"


class FakeClock:
    def __init__(self) -> None:
        self.now = 1000.0

    def __call__(self) -> float:
        return self.now

    def advance(self, seconds: float) -> None:
        self.now += seconds


@pytest.fixture
def clock() -> FakeClock:
    return FakeClock()


def _repo(clock: FakeClock, **limits: float) -> InMemoryConversationRepository:
    return InMemoryConversationRepository(ConversationLimits(**limits), clock=clock)  # type: ignore[arg-type]


def _exchange(n: int) -> list:  # type: ignore[type-arg]
    return [turn("user", f"q{n}"), turn("agent", f"a{n}")]


# --- conversation count -------------------------------------------------------------------


def test_global_capacity_evicts_least_recently_active(clock: FakeClock) -> None:
    repo = _repo(clock, max_conversations=3, max_conversations_per_owner=10)
    first = repo.create(ALICE, AGENT)
    clock.advance(1)
    second = repo.create(BOB, AGENT)
    clock.advance(1)
    repo.create(ALICE, AGENT)
    clock.advance(1)
    repo.ensure(ALICE, first, AGENT)  # activity makes "first" most recent
    clock.advance(1)
    repo.create(BOB, AGENT)  # at capacity: evicts "second", the least recently active
    assert len(repo) == 3
    assert repo.get(ALICE, first).conversation_id == first
    with pytest.raises(NotFoundError):
        repo.get(BOB, second)
    assert repo.evictions["global_capacity"] == 1


def test_per_owner_capacity_protects_other_owners(clock: FakeClock) -> None:
    repo = _repo(clock, max_conversations=100, max_conversations_per_owner=2)
    bobs = repo.create(BOB, AGENT)
    for _ in range(10):  # alice floods
        clock.advance(1)
        repo.create(ALICE, AGENT)
    assert len(repo.list_for(ALICE)) == 2
    assert repo.get(BOB, bobs).conversation_id == bobs
    assert repo.evictions["owner_capacity"] == 8


def test_storage_stays_bounded_under_sustained_load(clock: FakeClock) -> None:
    repo = _repo(clock, max_conversations=100, max_conversations_per_owner=100)
    for i in range(5000):
        repo.create(Identity(f"user-{i % 250}"), AGENT)
        assert len(repo._items) <= 100
    assert len(repo) == 100
    assert sum(len(v) for v in repo._by_owner.values()) == 100  # owner index stays consistent


# --- messages retained per conversation ---------------------------------------------------


def test_turn_window_keeps_newest_and_counts_dropped(clock: FakeClock) -> None:
    repo = _repo(clock, max_turns_per_conversation=4)
    cid = repo.create(ALICE, AGENT)
    for n in range(3):
        repo.append(ALICE, cid, AGENT, _exchange(n))
    view = repo.get(ALICE, cid)
    assert [t.content for t in view.turns] == ["q1", "a1", "q2", "a2"]
    assert view.dropped_turns == 2


# --- message size -------------------------------------------------------------------------


def test_runner_enforces_configured_message_size(clock: FakeClock) -> None:
    repo = _repo(clock, max_message_chars=50)
    tools = ToolRegistry([SupplierEvidenceLookupTool(SupplierRepository([]))])
    runner = build_runner(tools, conversations=repo)
    with pytest.raises(InputValidationError, match="exceeds 50"):
        runner.run(agent_key=AGENT, message="x" * 51, identity=ALICE, request_id=None)
    assert len(repo) == 0  # rejected before any work or storage
    ok = runner.run(agent_key=AGENT, message="y" * 50, identity=ALICE, request_id=None)
    assert ok.conversation_id


def test_api_rejects_message_over_configured_limit(make_token: TokenFactory) -> None:
    settings = Settings(
        jwt_secret=SecretStr(TEST_SECRET),
        assessment_date=AS_OF,
        max_message_chars=100,
        _env_file=None,  # type: ignore[call-arg]
    )
    headers = {"Authorization": f"Bearer {make_token('alice')}"}
    with TestClient(create_app(settings)) as client:
        too_long = client.post(INVOKE, json={"message": "z" * 101}, headers=headers)
        at_limit = client.post(INVOKE, json={"message": "z" * 100}, headers=headers)
    assert too_long.status_code == 422
    assert too_long.json()["error"]["code"] == "VALIDATION_ERROR"
    assert "zzzz" not in too_long.text
    assert at_limit.status_code == 200


def test_message_limit_cannot_exceed_hard_ceiling() -> None:
    with pytest.raises(ValidationError):
        Settings(jwt_secret=SecretStr(TEST_SECRET), max_message_chars=8001, _env_file=None)  # type: ignore[call-arg]


# --- idle lifetime ------------------------------------------------------------------------


def test_idle_conversation_expires(clock: FakeClock) -> None:
    repo = _repo(clock, idle_ttl_seconds=60)
    cid = repo.create(ALICE, AGENT)
    clock.advance(59.9)
    assert repo.get(ALICE, cid).conversation_id == cid
    clock.advance(0.1)
    with pytest.raises(NotFoundError):
        repo.get(ALICE, cid)
    assert repo.list_for(ALICE) == []
    assert repo.evictions["idle_expired"] == 1


def test_activity_refreshes_idle_lifetime_but_reads_do_not(clock: FakeClock) -> None:
    repo = _repo(clock, idle_ttl_seconds=60)
    cid = repo.create(ALICE, AGENT)
    clock.advance(50)
    repo.append(ALICE, cid, AGENT, _exchange(0))  # activity
    clock.advance(50)
    repo.get(ALICE, cid)  # read: does not extend
    clock.advance(10)
    with pytest.raises(NotFoundError):
        repo.ensure(ALICE, cid, AGENT)


def test_expired_conversation_cannot_be_continued(clock: FakeClock) -> None:
    repo = _repo(clock, idle_ttl_seconds=60)
    cid = repo.create(ALICE, AGENT)
    clock.advance(61)
    with pytest.raises(NotFoundError):
        repo.append(ALICE, cid, AGENT, _exchange(0))


# --- configuration ------------------------------------------------------------------------


@pytest.mark.parametrize(
    "bad",
    [
        {"max_conversations": 0},
        {"max_conversations_per_owner": 0},
        {"max_turns_per_conversation": 1},
        {"max_message_chars": 0},
        {"idle_ttl_seconds": 0},
    ],
)
def test_invalid_limits_are_rejected(bad: dict[str, float]) -> None:
    with pytest.raises(ValueError):
        ConversationLimits(**bad)  # type: ignore[arg-type]


def test_settings_flow_into_repository_limits() -> None:
    settings = Settings(
        jwt_secret=SecretStr(TEST_SECRET),
        max_conversations=7,
        max_conversations_per_owner=3,
        max_turns_per_conversation=6,
        max_message_chars=500,
        conversation_idle_ttl_seconds=90,
        _env_file=None,  # type: ignore[call-arg]
    )
    limits = create_app(settings).state.container.conversations.limits
    assert limits == ConversationLimits(7, 3, 6, 500, 90)


def test_api_exposes_dropped_turns(make_token: TokenFactory) -> None:
    settings = Settings(
        jwt_secret=SecretStr(TEST_SECRET),
        assessment_date=AS_OF,
        max_turns_per_conversation=2,
        _env_file=None,  # type: ignore[call-arg]
    )
    headers = {"Authorization": f"Bearer {make_token('alice')}"}
    with TestClient(create_app(settings)) as client:
        cid = client.post(
            INVOKE, json={"message": "Can Supplier Acme be approved?"}, headers=headers
        ).json()["conversation_id"]
        client.post(
            INVOKE,
            json={"message": "What about Supplier Lumen?", "conversation_id": cid},
            headers=headers,
        )
        view = client.get(f"/v1/conversations/{cid}", headers=headers).json()
    assert view["turns"][0]["content"] == "What about Supplier Lumen?"
    assert view["dropped_turns"] == 2
