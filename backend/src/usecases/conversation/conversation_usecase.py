"""Conversation use case leveraging Agno agents."""

from __future__ import annotations

from collections.abc import AsyncIterator
from uuid import uuid4

from agno.agent import RunContentEvent, RunErrorEvent, RunOutput

from src.core import get_logger
from src.integrations.mcp import get_mcp_toolkit
from src.models import MCPToolSelection
from src.shared.exceptions.llm import LLMNoOutputError, LLMStreamError

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
        self._logger = get_logger(self.__class__.__name__)

    async def generate_reply(self, payload: ConversationRequest) -> ConversationReply:
        agent = self._agent_factory.create_agent(
            model_key=payload.model_key,
            session_id=payload.conversation_id,
        )
        self._attach_requested_tools(agent, payload.tools)
        messages = [message.model_dump(mode="python") for message in payload.history]
        run_output: RunOutput = await agent.arun(
            input=messages,
            session_id=payload.conversation_id,
            user_id=payload.user_id,
        )

        content = run_output.get_content_as_string() or run_output.content
        if content is None:
            raise LLMNoOutputError(context={"conversation_id": payload.conversation_id})

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
        self._attach_requested_tools(agent, payload.tools)
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
                raise LLMStreamError(
                    context={"conversation_id": payload.conversation_id}
                )

    def _attach_requested_tools(
        self,
        agent,
        selections: list[MCPToolSelection] | None,
    ) -> None:
        if not selections:
            return

        seen: set[str] = set()
        for selection in selections:
            server_name = selection.server.strip()
            if not server_name or server_name in seen:
                continue

            seen.add(server_name)
            functions = None
            if selection.functions:
                cleaned = [str(name).strip() for name in selection.functions]
                functions = [name for name in cleaned if name]
                if not functions:
                    functions = None

            toolkit = get_mcp_toolkit(
                server_name,
                allowed_functions=functions,
            )
            if toolkit is None or not toolkit.functions:
                self._logger.debug(
                    "Skipping MCP server '%s' – toolkit unavailable or empty",
                    server_name,
                )
                continue

            agent.add_tool(toolkit)
