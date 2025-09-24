"""Use case for managing available LLM model configurations."""

from __future__ import annotations

from dataclasses import dataclass

from src.integrations.llm import ConversationAgentFactory, LLMModelConfig
from src.models import (
    ListModelsResponse,
    LLMModelDescriptor,
    UpsertLLMModelRequest,
)


@dataclass(frozen=True)
class ModelManagementUsecase:
    """Coordinates model management operations for conversation agents."""

    agent_factory: ConversationAgentFactory

    async def list_models(self) -> ListModelsResponse:
        configs = self.agent_factory.get_available_models()
        descriptors = [self._to_descriptor(item) for item in configs]
        active_key = self.agent_factory.get_active_model_key()
        return ListModelsResponse(active_model_key=active_key, models=descriptors)

    async def set_active_model(self, model_key: str) -> None:
        self.agent_factory.set_active_model_key(model_key)

    async def upsert_model(self, payload: UpsertLLMModelRequest) -> LLMModelDescriptor:
        config = LLMModelConfig(
            key=payload.key,
            provider=payload.provider,
            model_id=payload.model_id,
            api_key_env=payload.api_key_env,
            base_url=payload.base_url,
            default_params=dict(payload.default_params or {}),
            supports_streaming=payload.supports_streaming,
            metadata=dict(payload.metadata or {}),
        )
        self.agent_factory.register_model(config)
        if payload.set_active:
            self.agent_factory.set_active_model_key(config.key)
        return self._to_descriptor(config)

    def _to_descriptor(self, config: LLMModelConfig) -> LLMModelDescriptor:
        return LLMModelDescriptor(
            key=config.key,
            provider=config.provider,
            model_id=config.model_id,
            supports_streaming=config.supports_streaming,
            metadata=config.metadata or None,
            base_url=config.base_url,
        )
