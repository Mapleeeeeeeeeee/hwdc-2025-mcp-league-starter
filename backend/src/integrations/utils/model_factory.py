"""Factory utilities for creating preconfigured Agno model instances."""

from __future__ import annotations

from typing import Any

from agno.models.anthropic import Claude
from agno.models.base import Model
from agno.models.google import Gemini
from agno.models.message import Message
from agno.models.openai import OpenAIChat
from anthropic.lib.vertex import AnthropicVertex, AsyncAnthropicVertex

from src.config import settings
from src.core.logging import get_logger

logger = get_logger(__name__)


def _build_vertex_kwargs(overrides: dict[str, Any] | None = None) -> dict[str, Any]:
    project_id = settings.get_secret("GOOGLE_CLOUD_PROJECT")
    region = settings.get_secret("GOOGLE_CLOUD_REGION")

    if not project_id or not region:
        raise ValueError(
            "GOOGLE_CLOUD_PROJECT and GOOGLE_CLOUD_REGION must be configured "
            "for Vertex AI models",
        )

    kwargs = overrides.copy() if overrides else {}
    kwargs.setdefault("project_id", project_id)
    kwargs.setdefault("location", region)
    return kwargs


def get_agno_model_instance(
    provider: str,
    model_name: str,
    *,
    max_tokens: int | None = None,
    temperature: float | None = None,
    top_p: float | None = None,
) -> Model:
    provider_lower = provider.lower()
    common_kwargs: dict[str, Any] = {}

    if max_tokens is not None:
        common_kwargs["max_tokens"] = max_tokens
    if temperature is not None:
        common_kwargs["temperature"] = temperature
    if top_p is not None:
        common_kwargs["top_p"] = top_p

    if provider_lower == "openai":
        return OpenAIChat(id=model_name, **common_kwargs)

    if provider_lower == "google":
        return Gemini(
            id=model_name,
            max_output_tokens=max_tokens,
            temperature=temperature,
            top_p=top_p,
        )

    if provider_lower == "vertexai":
        vertex_kwargs = _build_vertex_kwargs(
            {
                "max_output_tokens": max_tokens,
                "temperature": temperature,
                "top_p": top_p,
            }
        )
        vertex_kwargs["vertexai"] = True
        return Gemini(id=model_name, **vertex_kwargs)

    if provider_lower == "anthropic":
        vertex_kwargs = _build_vertex_kwargs()
        vertex_client = AnthropicVertex(**vertex_kwargs)
        async_vertex_client = AsyncAnthropicVertex(**vertex_kwargs)

        claude_kwargs: dict[str, Any] = {
            "id": model_name,
            "client": vertex_client,
            "async_client": async_vertex_client,
        }
        claude_kwargs.update(common_kwargs)
        return Claude(**claude_kwargs)

    logger.warning("Unsupported provider '%s'. Falling back to gpt-4.1", provider)
    return OpenAIChat(id="gpt-4.1")


def demo_conversation() -> str:
    model = get_agno_model_instance(
        provider="openai",
        model_name="gpt-4o",
        max_tokens=150,
        temperature=0.7,
        top_p=0.9,
    )

    messages = [
        Message(
            role="system",
            content="You are a humorous and knowledgeable assistant.",
        ),
        Message(role="user", content="List three productivity tips."),
    ]
    response = model.invoke(messages)
    return response.choices[0].message.content  # type: ignore[return-value]


__all__ = ["get_agno_model_instance", "demo_conversation"]
