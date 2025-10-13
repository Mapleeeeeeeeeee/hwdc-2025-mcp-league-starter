"""Unit tests for conversation use cases."""

from __future__ import annotations

from collections.abc import Sequence
from types import SimpleNamespace
from typing import cast

import pytest
from agno.agent import RunContentEvent, RunErrorEvent
from src.integrations.llm import ConversationAgentFactory
from src.models import ConversationMessage, ConversationRequest
from src.shared.exceptions.llm import LLMNoOutputError, LLMStreamError
from src.usecases.conversation import ConversationUsecase

pytestmark = [pytest.mark.unit, pytest.mark.application]


class StubRunOutput:
    def __init__(
        self,
        *,
        content: str | None,
        run_id: str | None = None,
        model: str | None = None,
    ):
        self._content = content
        self.content = content
        self.run_id = run_id
        self.model = model

    def get_content_as_string(self) -> str | None:
        return self._content


class StubAgent:
    def __init__(
        self,
        *,
        run_output: StubRunOutput | None = None,
        stream_events: Sequence[object] | None = None,
        model_id: str = "openai:gpt-5-mini",
    ) -> None:
        self._run_output = run_output
        self._stream_events = list(stream_events or [])
        self.model = SimpleNamespace(id=model_id)
        self.calls: list[dict[str, object]] = []

    def arun(self, *, stream: bool = False, **kwargs):
        self.calls.append({"stream": stream, **kwargs})

        if stream:

            async def iterator():
                for event in self._stream_events:
                    yield event

            return iterator()

        async def runner():
            return self._run_output

        return runner()


class StubAgentFactory:
    def __init__(
        self,
        *,
        agent: StubAgent,
        active_model_key: str = "openai:gpt-5-mini",
    ) -> None:
        self._agent = agent
        self._active_model_key = active_model_key
        self.created_with: list[dict[str, object]] = []

    def create_agent(
        self,
        *,
        model_key: str | None = None,
        session_id: str | None = None,
        prompt_key: str | None = None,
        overrides=None,
    ):
        self.created_with.append(
            {
                "model_key": model_key,
                "session_id": session_id,
                "overrides": overrides,
            }
        )
        return self._agent

    def get_active_model_key(self) -> str:
        return self._active_model_key


@pytest.fixture
def conversation_payload() -> ConversationRequest:
    history = [
        ConversationMessage(role="user", content="Hello"),
        ConversationMessage(role="assistant", content="Hi there"),
    ]
    return ConversationRequest(
        conversation_id="conv-1",
        history=history,
        user_id="user-123",
        model_key=None,
    )


@pytest.mark.asyncio
async def test_generate_reply__valid_output__returns_conversation_reply(
    conversation_payload: ConversationRequest,
) -> None:
    run_output = StubRunOutput(
        content="Answer", run_id="run-456", model="openai:gpt-5-mini"
    )
    agent = StubAgent(run_output=run_output)
    factory = StubAgentFactory(agent=agent)
    usecase = ConversationUsecase(agent_factory=cast(ConversationAgentFactory, factory))

    reply = await usecase.generate_reply(conversation_payload)

    assert reply.conversation_id == "conv-1"
    assert reply.message_id == "run-456"
    assert reply.content == "Answer"
    assert reply.model_key == "openai:gpt-5-mini"
    assert factory.created_with == [
        {"model_key": None, "session_id": "conv-1", "overrides": None}
    ]
    call = agent.calls[-1]
    assert call["stream"] is False
    assert call["session_id"] == "conv-1"
    assert call["user_id"] == "user-123"
    assert call["input"] == [
        {"role": "user", "content": "Hello"},
        {"role": "assistant", "content": "Hi there"},
    ]


@pytest.mark.asyncio
async def test_generate_reply__missing_content__raises_llm_no_output_error(
    conversation_payload: ConversationRequest,
) -> None:
    run_output = StubRunOutput(content=None, run_id=None, model=None)
    agent = StubAgent(run_output=run_output)
    factory = StubAgentFactory(agent=agent)
    usecase = ConversationUsecase(agent_factory=cast(ConversationAgentFactory, factory))

    with pytest.raises(LLMNoOutputError):
        await usecase.generate_reply(conversation_payload)

    assert factory.created_with == [
        {"model_key": None, "session_id": "conv-1", "overrides": None}
    ]
    call = agent.calls[-1]
    assert call["stream"] is False
    assert call["session_id"] == "conv-1"
    assert call["user_id"] == "user-123"


def _make_content_event(content: str, *, run_id: str | None = None) -> RunContentEvent:
    return RunContentEvent(content=content, run_id=run_id)


def _make_error_event(error_message: str) -> RunErrorEvent:
    return RunErrorEvent(content=error_message)


@pytest.mark.asyncio
async def test_stream_reply__content_events__yields_stream_chunks(
    conversation_payload: ConversationRequest,
) -> None:
    events = [
        _make_content_event("partial", run_id="run-1"),
        _make_content_event("answer", run_id="run-1"),
    ]
    agent = StubAgent(stream_events=events)
    factory = StubAgentFactory(agent=agent)
    usecase = ConversationUsecase(agent_factory=cast(ConversationAgentFactory, factory))

    deltas: list[str] = []
    async for chunk in usecase.stream_reply(conversation_payload):
        deltas.append(chunk.delta)

    assert deltas == ["partial", "answer"]
    assert factory.created_with == [
        {"model_key": None, "session_id": "conv-1", "overrides": None}
    ]
    call = agent.calls[-1]
    assert call["stream"] is True
    assert call["session_id"] == "conv-1"
    assert call["user_id"] == "user-123"
    assert call["input"] == [
        {"role": "user", "content": "Hello"},
        {"role": "assistant", "content": "Hi there"},
    ]


@pytest.mark.asyncio
async def test_stream_reply__error_event__raises_llm_stream_error(
    conversation_payload: ConversationRequest,
) -> None:
    events = [_make_error_event("boom")]
    agent = StubAgent(stream_events=events)
    factory = StubAgentFactory(agent=agent)
    usecase = ConversationUsecase(agent_factory=cast(ConversationAgentFactory, factory))

    async def consume() -> None:
        async for _ in usecase.stream_reply(conversation_payload):
            pass

    with pytest.raises(LLMStreamError):
        await consume()

    assert factory.created_with == [
        {"model_key": None, "session_id": "conv-1", "overrides": None}
    ]
    call = agent.calls[-1]
    assert call["stream"] is True
    assert call["session_id"] == "conv-1"
    assert call["user_id"] == "user-123"
