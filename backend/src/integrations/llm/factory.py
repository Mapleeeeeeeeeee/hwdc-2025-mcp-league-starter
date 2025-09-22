"""Factory helpers for creating conversation agents."""

from __future__ import annotations

from typing import Any

from agno.agent import Agent

from .config_store import ModelConfigStore
from .providers import build_model


class ConversationAgentFactory:
    """Creates Agno agents using runtime model configuration."""

    def __init__(self, store: ModelConfigStore | None = None) -> None:
        self._store = store or ModelConfigStore()

    def create_agent(
        self,
        *,
        model_key: str | None = None,
        session_id: str | None = None,
        overrides: dict[str, Any] | None = None,
    ) -> Agent:
        key = model_key or self._store.get_active_model_key()
        config = self._store.get_config(key)
        model = build_model(config, overrides or {})
        metadata = config.metadata or {}
        agent = Agent(
            session_id=session_id,
            name=metadata.get("name", config.key),
            description=metadata.get("description"),
            model=model,
            markdown=True,
            debug_mode=bool(metadata.get("debug", False)),
        )
        return agent

    def get_available_models(self) -> list[dict[str, Any]]:
        models = []
        for config in self._store.list_configs():
            models.append(
                {
                    "key": config.key,
                    "provider": config.provider,
                    "modelId": config.model_id,
                    "supportsStreaming": config.supports_streaming,
                    "metadata": config.metadata,
                }
            )
        return models

    def get_active_model_key(self) -> str:
        return self._store.get_active_model_key()

    def set_active_model_key(self, key: str) -> None:
        self._store.set_active_model_key(key)


__all__ = ["ConversationAgentFactory"]
