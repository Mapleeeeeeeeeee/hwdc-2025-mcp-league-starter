"""Unit tests for conversation API models."""

from __future__ import annotations

import pytest
from pydantic import ValidationError
from src.models import (
    ConversationMessage,
    ConversationReply,
    ConversationRequest,
    ConversationStreamChunk,
)

pytestmark = [pytest.mark.unit, pytest.mark.api]


def test_conversation_request__empty_history__raises_validation_error() -> None:
    with pytest.raises(ValidationError):
        ConversationRequest(
            conversation_id="conv-1",
            history=[],
            user_id="user-1",
        )


def test_conversation_message__invalid_role__raises_validation_error() -> None:
    with pytest.raises(ValidationError):
        ConversationMessage(role="moderator", content="Hello")  # type: ignore[arg-type]


def test_conversation_reply__model_dump_uses_camel_case() -> None:
    reply = ConversationReply(
        conversation_id="conv-1",
        message_id="msg-1",
        content="Hello",
        model_key="openai:gpt-5-mini",
    )

    dumped = reply.model_dump(by_alias=True)

    assert dumped == {
        "conversationId": "conv-1",
        "messageId": "msg-1",
        "content": "Hello",
        "modelKey": "openai:gpt-5-mini",
    }


def test_conversation_stream_chunk__keeps_delta_text() -> None:
    chunk = ConversationStreamChunk(
        conversation_id="conv-1",
        message_id="msg-1",
        delta="partial",
        model_key="openai:gpt-5-mini",
    )

    dumped = chunk.model_dump(by_alias=True)

    assert dumped["delta"] == "partial"
