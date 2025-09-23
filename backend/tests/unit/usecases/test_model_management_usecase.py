"""Unit tests for model management use case."""

from __future__ import annotations

from dataclasses import dataclass
from typing import cast

import pytest
from src.integrations.llm import ConversationAgentFactory, LLMModelConfig
from src.models import UpsertLLMModelRequest
from src.usecases.conversation import ModelManagementUsecase

pytestmark = [pytest.mark.unit, pytest.mark.application]


@dataclass
class FakeAgentFactory:
    available: list[LLMModelConfig]
    active_key: str

    def __post_init__(self) -> None:
        self.set_calls: list[str] = []
        self.registered: list[LLMModelConfig] = []

    def get_available_models(self) -> list[LLMModelConfig]:
        return list(self.available)

    def get_active_model_key(self) -> str:
        return self.active_key

    def set_active_model_key(self, key: str) -> None:
        self.set_calls.append(key)
        self.active_key = key

    def register_model(self, config: LLMModelConfig) -> None:
        self.registered.append(config)


EXISTING_CONFIG = LLMModelConfig(
    key="openai:gpt-5-mini",
    provider="openai",
    model_id="gpt-5-mini",
    supports_streaming=True,
    metadata={"display_name": "OpenAI GPT-5 mini"},
)


@pytest.mark.asyncio
async def test_list_models__returns_active_key_and_descriptors() -> None:
    factory = FakeAgentFactory(
        available=[EXISTING_CONFIG], active_key="openai:gpt-5-mini"
    )
    usecase = ModelManagementUsecase(cast(ConversationAgentFactory, factory))

    response = await usecase.list_models()

    assert response.active_model_key == "openai:gpt-5-mini"
    assert len(response.models) == 1
    descriptor = response.models[0]
    assert descriptor.key == EXISTING_CONFIG.key
    assert descriptor.metadata == EXISTING_CONFIG.metadata
    assert factory.set_calls == []
    assert factory.registered == []


@pytest.mark.asyncio
async def test_set_active_model__delegates_to_factory() -> None:
    factory = FakeAgentFactory(
        available=[EXISTING_CONFIG], active_key="openai:gpt-5-mini"
    )
    usecase = ModelManagementUsecase(cast(ConversationAgentFactory, factory))

    await usecase.set_active_model("ollama:llama3.1")

    assert factory.set_calls == ["ollama:llama3.1"]
    assert factory.active_key == "ollama:llama3.1"
    assert factory.registered == []


@pytest.mark.asyncio
async def test_upsert_model__registers_config_and_sets_active() -> None:
    factory = FakeAgentFactory(
        available=[EXISTING_CONFIG], active_key="openai:gpt-5-mini"
    )
    usecase = ModelManagementUsecase(cast(ConversationAgentFactory, factory))

    payload = UpsertLLMModelRequest(
        key="ollama:llama3.1",
        provider="ollama",
        model_id="llama3.1",
        supports_streaming=False,
        metadata={"display_name": "Llama"},
        set_active=True,
    )

    descriptor = await usecase.upsert_model(payload)

    assert factory.registered[0].key == "ollama:llama3.1"
    assert factory.set_calls[-1] == "ollama:llama3.1"
    assert descriptor.key == "ollama:llama3.1"
    assert descriptor.supports_streaming is False
