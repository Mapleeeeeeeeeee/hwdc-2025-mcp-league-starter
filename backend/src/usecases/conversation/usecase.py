"""Conversation use case leveraging Agno agents."""

from __future__ import annotations

from collections.abc import AsyncIterator
from uuid import uuid4

from agno.agent import RunContentEvent, RunErrorEvent, RunOutput

from src.core.exceptions import ServiceUnavailableError

from ...integrations.llm import ConversationAgentFactory
from ...models.conversation import (
    ConversationReply,
    ConversationRequest,
    ConversationStreamChunk,
)


class ConversationUsecase:
    """Coordinates LLM interactions for conversation endpoints."""

    def __init__(self, agent_factory: ConversationAgentFactory) -> None:
        self._agent_factory = agent_factory

    async def generate_reply(self, payload: ConversationRequest) -> ConversationReply:
        agent = self._agent_factory.create_agent(
            model_key=payload.model_key,
            session_id=payload.conversation_id,
        )
        messages = [message.model_dump(mode="python") for message in payload.history]
        run_output: RunOutput = await agent.arun(
            input=messages,
            session_id=payload.conversation_id,
            user_id=payload.user_id,
        )

        content = run_output.get_content_as_string() or run_output.content
        if content is None:
            raise ServiceUnavailableError(
                detail="LLM did not return output",
                i18n_key="errors.llm.no_output",
                context={"conversation_id": payload.conversation_id},
            )

        model_key = payload.model_key or self._agent_factory.get_active_model_key()
        model_identifier = (
            run_output.model or getattr(agent.model, "id", None) or model_key
        )
        message_id = run_output.run_id or str(uuid4())
        content_text = content if isinstance(content, str) else str(content)

        reply = ConversationReply(
            conversation_id=payload.conversation_id,
            message_id=message_id,
            content=content_text,
            model_key=model_identifier,
        )

        return reply

    async def stream_reply(
        self,
        payload: ConversationRequest,
    ) -> AsyncIterator[ConversationStreamChunk]:
        agent = self._agent_factory.create_agent(
            model_key=payload.model_key,
            session_id=payload.conversation_id,
        )
        messages = [message.model_dump(mode="python") for message in payload.history]
        stream = agent.arun(
            input=messages,
            stream=True,
            session_id=payload.conversation_id,
            user_id=payload.user_id,
            yield_run_response=False,
        )

        model_key = payload.model_key or self._agent_factory.get_active_model_key()
        model_identifier = getattr(agent.model, "id", None) or model_key

        async for event in stream:
            if isinstance(event, RunContentEvent) and event.content:
                message_id = event.run_id or str(uuid4())
                if isinstance(event.content, str):
                    delta = event.content
                else:
                    delta = str(event.content)
                yield ConversationStreamChunk(
                    conversation_id=payload.conversation_id,
                    message_id=message_id,
                    delta=delta,
                    model_key=model_identifier,
                )

            if isinstance(event, RunErrorEvent):
                raise ServiceUnavailableError(
                    detail="LLM streaming output ended unexpectedly",
                    i18n_key="errors.llm.stream_incomplete",
                    context={"conversation_id": payload.conversation_id},
                )
