"""API schemas for conversation endpoints."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import Field, field_validator

from .base import APIBaseModel
from .mcp import MCPToolSelection

RoleLiteral = Literal["user", "assistant", "system"]


class ConversationMessage(APIBaseModel):
    role: RoleLiteral = Field(description="Role of the message author")
    content: str = Field(min_length=1, description="Message content")


class ConversationRequest(APIBaseModel):
    conversation_id: str = Field(
        description="Unique identifier for the conversation session",
    )
    history: list[ConversationMessage] = Field(
        description="Ordered conversation history",
    )
    user_id: str | None = Field(
        default=None,
        description="Optional user identifier",
    )
    model_key: str | None = Field(
        default=None,
        description="Requested model key, overrides default",
    )
    prompt_key: str | None = Field(
        default=None,
        description="Requested prompt preset key, defaults to 'default'",
    )
    tools: list[MCPToolSelection] | None = Field(
        default=None,
        description="Optional list of MCP tool selections to register",
    )

    @field_validator("history")
    @classmethod
    def _ensure_history_not_empty(
        cls,
        value: list[ConversationMessage],
    ) -> list[ConversationMessage]:
        if not value:
            raise ValueError("conversation history cannot be empty")
        return value


class ConversationReply(APIBaseModel):
    conversation_id: str
    message_id: str
    content: str
    model_key: str


class ConversationStreamChunk(APIBaseModel):
    conversation_id: str
    message_id: str
    delta: str
    model_key: str


class LLMModelDescriptor(APIBaseModel):
    key: str
    provider: str
    model_id: str
    supports_streaming: bool
    metadata: dict[str, str | int | float | bool | None] | None = None
    base_url: str | None = None


class ListModelsResponse(APIBaseModel):
    active_model_key: str
    models: list[LLMModelDescriptor]


class UpsertLLMModelRequest(APIBaseModel):
    key: str
    provider: str
    model_id: str
    api_key_env: str | None = None
    base_url: str | None = None
    default_params: dict[str, Any] | None = None
    supports_streaming: bool = True
    metadata: dict[str, Any] | None = None
    set_active: bool = False
