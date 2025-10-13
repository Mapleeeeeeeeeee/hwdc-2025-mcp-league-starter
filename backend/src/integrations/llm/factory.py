"""Factory helpers for creating conversation agents."""

from __future__ import annotations

from typing import Any

from agno.agent import Agent

from .config_store import ModelConfigStore
from .model_config import LLMModelConfig
from .providers import build_model


class ConversationAgentFactory:
    """Creates Agno agents using runtime model configuration."""

    _instance: ConversationAgentFactory | None = None
    _class_initialized = False

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, store: ModelConfigStore | None = None) -> None:
        if ConversationAgentFactory._class_initialized:
            return

        self._store = store or ModelConfigStore()
        ConversationAgentFactory._class_initialized = True

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
            model=model,
            debug_mode=bool(metadata.get("debug", False)),
        )
        return agent

    def get_available_models(self) -> list[LLMModelConfig]:
        return self._store.list_configs()

    def get_active_model_key(self) -> str:
        return self._store.get_active_model_key()

    def set_active_model_key(self, key: str) -> None:
        self._store.set_active_model_key(key)

    def register_model(self, config: LLMModelConfig) -> None:
        self._store.upsert_config(config)
