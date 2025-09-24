"""Unit tests for provider factory helpers."""

from __future__ import annotations

from unittest.mock import patch

import pytest
from src.integrations.llm import LLMModelConfig
from src.integrations.llm.providers import build_model
from src.shared.exceptions import (
    LLMProviderNotConfiguredError,
    LLMProviderUnsupportedError,
)


def test_build_model__unsupported_provider__raises_error() -> None:
    config = LLMModelConfig(key="custom", provider="unsupported", model_id="model")

    with pytest.raises(LLMProviderUnsupportedError):
        build_model(config)


@patch("src.integrations.llm.providers.settings")
def test_build_model__openai_missing_secret__raises_error(mock_settings) -> None:
    config = LLMModelConfig(
        key="openai:gpt-5-mini",
        provider="openai",
        model_id="gpt-5-mini",
        api_key_env="CUSTOM_SECRET",
    )

    # Mock the get_secret method to return None
    mock_settings.get_secret.return_value = None

    with pytest.raises(LLMProviderNotConfiguredError):
        build_model(config)


@patch("src.integrations.llm.providers.settings")
def test_build_model__openai_includes_overrides(mock_settings) -> None:
    config = LLMModelConfig(
        key="openai:gpt-5-mini",
        provider="openai",
        model_id="gpt-5-mini",
        api_key_env="CUSTOM_SECRET",
        base_url="https://api.test",
        default_params={"temperature": 0.2},
    )

    # Mock the get_secret method to return fake key
    mock_settings.get_secret.return_value = "fake-key"

    model = build_model(config, overrides={"max_tokens": 42})

    assert model.id == "gpt-5-mini"
    assert model.api_key == "fake-key"
    assert getattr(model, "base_url", None) == "https://api.test"
    assert model.temperature == 0.2
    assert model.max_tokens == 42


def test_build_model__ollama_sets_host_and_overrides() -> None:
    config = LLMModelConfig(
        key="ollama:llama3.1",
        provider="ollama",
        model_id="llama3.1",
        base_url="http://ollama.local",
        default_params={"temperature": 0.1},
    )

    model = build_model(config, overrides={"top_p": 0.5})

    assert model.id == "llama3.1"
    assert getattr(model, "host", None) == "http://ollama.local"

    # Ollama stores parameters in options dict
    options = getattr(model, "options", {})
    assert options.get("temperature") == 0.1
    assert options.get("top_p") == 0.5
