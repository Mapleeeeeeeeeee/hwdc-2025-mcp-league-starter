"""Provider factory implementations for supported LLM vendors."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from typing import Any

from agno.models.ollama import Ollama
from agno.models.openai import OpenAIChat

from src.config import settings
from src.shared.exceptions import (
    LLMProviderNotConfiguredError,
    LLMProviderUnsupportedError,
)

from .model_config import LLMModelConfig

ProviderFactory = Callable[[LLMModelConfig, Mapping[str, Any]], Any]


def _build_openai_model(
    config: LLMModelConfig,
    overrides: Mapping[str, Any],
) -> OpenAIChat:
    secret_name = config.api_key_env or "OPENAI_API_KEY"
    api_key = settings.get_secret(secret_name)
    if not api_key:
        raise LLMProviderNotConfiguredError(
            provider="openai",
            secret_name=secret_name,
        )
    params: dict[str, Any] = {
        "id": config.model_id,
        "api_key": api_key,
    }
    if config.base_url:
        params["base_url"] = config.base_url
    params.update(config.default_params)
    params.update(overrides)
    return OpenAIChat(**params)


def _build_ollama_model(
    config: LLMModelConfig,
    overrides: Mapping[str, Any],
) -> Ollama:
    params: dict[str, Any] = {"id": config.model_id}
    if config.base_url:
        params["host"] = config.base_url
    params.update(config.default_params)
    params.update(overrides)
    return Ollama(**params)


_PROVIDER_FACTORIES: dict[str, ProviderFactory] = {
    "openai": _build_openai_model,
    "ollama": _build_ollama_model,
}


def build_model(
    config: LLMModelConfig,
    overrides: Mapping[str, Any] | None = None,
) -> Any:
    """Create a provider-specific model instance based on configuration."""

    factory = _PROVIDER_FACTORIES.get(config.provider)
    if factory is None:
        raise LLMProviderUnsupportedError(provider=config.provider)
    return factory(config, overrides or {})


__all__ = ["build_model", "ProviderFactory"]
