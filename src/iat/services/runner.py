"""Transport-independent agent execution.

``AgentRunner.run`` is the single entry point for executing an agent. It knows nothing about
HTTP: FastAPI routes call it today, and an AWS Bedrock AgentCore Runtime entrypoint (or a CLI,
queue worker, or test) can call it tomorrow with the same identity and evidence guarantees.
See docs/AGENTCORE_FUTURE.md.
"""

from __future__ import annotations

import datetime as dt
import logging
import time
import uuid
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, cast

from pydantic import BaseModel, ValidationError

from iat.agents.registry import AgentRegistry
from iat.core.errors import AgentExecutionError, InputValidationError, NotFoundError
from iat.schemas.execution import ExecutionRecord, ExecutionStatus, StepRecord
from iat.security.identity import Identity
from iat.services.conversations import ConversationRepository, turn
from iat.tools.registry import ExecutionRecorder, ToolExecutor

logger = logging.getLogger("iat.runner")


@dataclass(frozen=True)
class RunOutcome:
    conversation_id: str
    output: BaseModel
    execution: ExecutionRecord


class AgentRunner:
    def __init__(
        self,
        agents: AgentRegistry,
        tools: ToolExecutor,
        conversations: ConversationRepository,
        clock: Callable[[], dt.date],
        pseudonymize: Callable[[str], str],
    ) -> None:
        self._pseudonymize = pseudonymize
        self._agents = agents
        self._tools = tools
        self._conversations = conversations
        self._clock = clock

    def run(
        self,
        *,
        agent_key: str,
        message: str,
        identity: Identity,
        request_id: str | None,
        conversation_id: str | None = None,
    ) -> RunOutcome:
        limit = self._conversations.limits.max_message_chars
        if len(message) > limit:
            raise InputValidationError(f"Message exceeds {limit} characters")
        agent = self._agents.get(agent_key)
        if agent is None:
            raise NotFoundError(f"Unknown agent: {agent_key}")
        if conversation_id is not None:
            self._conversations.ensure(identity, conversation_id, agent.key)

        execution_id = uuid.uuid4().hex
        recorder = ExecutionRecorder()
        started = time.perf_counter()

        steps: list[StepRecord] = []

        def record(status: ExecutionStatus, error_class: str | None = None) -> ExecutionRecord:
            evidence = ExecutionRecord(
                request_id=request_id,
                execution_id=execution_id,
                agent=agent.key,
                subject_hash=self._pseudonymize(identity.subject),
                steps=list(steps),
                tools_invoked=list(recorder.records),
                status=status,
                duration_ms=round((time.perf_counter() - started) * 1000, 3),
                error_class=error_class,
            )
            # Evidence only: no message content, no raw identity, no secrets.
            logger.info("agent_execution", extra={"execution": evidence.model_dump(mode="json")})
            return evidence

        try:
            state: dict[str, Any] = {}
            mark = time.perf_counter()
            # "updates" yields each node as it finishes (the workflow trace); "values" yields the
            # full state after each step, so the last one is the final state.
            for mode, chunk in agent.graph.stream(
                {"message": message},
                config={
                    "configurable": {
                        # The agent gets a gateway bound to the agent resolved from the registry;
                        # it never sees the executor, the policy or the recorder directly.
                        "tools": self._tools.bind(agent.key, recorder),
                        "execution_id": execution_id,
                        "as_of": self._clock(),
                    }
                },
                stream_mode=["updates", "values"],
            ):
                if mode == "updates":
                    now = time.perf_counter()
                    for node in chunk:
                        steps.append(
                            StepRecord(node=node, duration_ms=round((now - mark) * 1000, 3))
                        )
                    mark = now
                elif mode == "values":
                    state = cast(dict[str, Any], chunk)
            output = agent.output_model.model_validate(state[agent.output_key])
        except (ValidationError, KeyError) as exc:
            record(ExecutionStatus.FAILED, f"InvalidAgentOutput:{type(exc).__name__}")
            raise AgentExecutionError(
                "Agent produced an invalid result", execution_id=execution_id
            ) from exc
        except Exception as exc:
            record(ExecutionStatus.FAILED, type(exc).__name__)
            raise AgentExecutionError("Agent execution failed", execution_id=execution_id) from exc

        execution = record(ExecutionStatus.COMPLETED)
        if conversation_id is None:
            conversation_id = self._conversations.create(identity, agent.key)
        self._conversations.append(
            identity,
            conversation_id,
            agent.key,
            [
                turn("user", message),
                turn(
                    "agent",
                    getattr(output, "explanation", ""),
                    execution_id=execution_id,
                    output=output.model_dump(mode="json"),
                ),
            ],
        )
        return RunOutcome(conversation_id=conversation_id, output=output, execution=execution)
