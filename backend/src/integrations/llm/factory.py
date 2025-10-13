"""Factory helpers for creating conversation agents."""

from __future__ import annotations

from typing import Any

from agno.agent import Agent

from src.core import get_logger

from .config_store import ModelConfigStore
from .model_config import LLMModelConfig
from .prompts_store import PromptsConfigStore
from .providers import build_model
from .tools_store import ToolsConfigStore

logger = get_logger(__name__)


class ConversationAgentFactory:
    """Creates Agno agents using runtime model configuration."""

    _instance: ConversationAgentFactory | None = None
    _class_initialized = False

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(
        self,
        store: ModelConfigStore | None = None,
        tools_store: ToolsConfigStore | None = None,
        prompts_store: PromptsConfigStore | None = None,
    ) -> None:
        if ConversationAgentFactory._class_initialized:
            return

        self._store = store or ModelConfigStore()
        self._tools_store = tools_store or ToolsConfigStore()
        self._prompts_store = prompts_store or PromptsConfigStore()
        ConversationAgentFactory._class_initialized = True

    def create_agent(
        self,
        *,
        model_key: str | None = None,
        session_id: str | None = None,
        prompt_key: str | None = None,
        overrides: dict[str, Any] | None = None,
        strict_tools: bool = False,
    ) -> Agent:
        """Create an Agno agent with configured model, tools, and prompts.

        Args:
            model_key: Key of the model to use (defaults to active model)
            session_id: Optional session identifier
            prompt_key: Key of the prompt preset to use (defaults to "default")
            overrides: Optional model parameter overrides
            strict_tools: If True, raise exception if any tool fails to load.
                         If False, log warnings and continue with available tools.

        Returns:
            Configured Agno Agent instance

        Raises:
            NotFoundError: If model_key or prompt_key is not found
            ToolkitLoadError: If strict_tools=True and a toolkit fails to load
            PromptNotFoundError: If the prompt configuration is not found
        """
        # Load model
        key = model_key or self._store.get_active_model_key()
        config = self._store.get_config(key)
        model = build_model(config, overrides or {})

        logger.info(
            "Creating agent",
            extra={
                "model_key": key,
                "prompt_key": prompt_key or "default",
                "session_id": session_id,
            },
        )

        # Load tools
        tools = self._tools_store.load_toolkit_instances(strict=strict_tools)

        # Load prompts
        instructions = self._prompts_store.get_instructions(prompt_key or "default")
        system_message = self._prompts_store.get_system_message()

        # Get metadata
        metadata = config.metadata or {}

        # Build agent
        agent = Agent(
            model=model,
            tools=tools if tools else None,
            instructions=instructions if instructions else None,
            description=system_message,
            debug_mode=bool(metadata.get("debug", False)),
        )

        logger.info(
            "✓ Agent created successfully",
            extra={
                "model_key": key,
                "tool_count": len(tools),
                "instruction_count": len(instructions),
                "debug_mode": bool(metadata.get("debug", False)),
            },
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

    def get_available_prompts(self) -> list[dict[str, str | bool]]:
        """Get list of available prompt presets."""
        return self._prompts_store.list_available_prompts()

    def get_enabled_tools(self) -> list[str]:
        """Get list of enabled tool keys."""
        return [tk.key for tk in self._tools_store.get_enabled_toolkits()]
