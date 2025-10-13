"""Store and load Agno prompts configurations."""

from __future__ import annotations

import json
from pathlib import Path

from src.core import get_logger
from src.shared.exceptions.agno import PromptNotFoundError

from .prompts_config import AgnoPromptsConfig, PromptConfig

logger = get_logger(__name__)


class PromptsConfigStore:
    """Manages loading and retrieval of Agno prompts from configuration."""

    def __init__(self, config_path: Path | None = None) -> None:
        """Initialize the prompts config store.

        Args:
            config_path: Path to agno_prompts.json.
                If None, uses default config directory.
        """
        if config_path is None:
            # Try to find config relative to project root
            cwd = Path.cwd()
            # Check if we're in backend directory
            if cwd.name == "backend":
                default_path = cwd / "config" / "agno_prompts.json"
            else:
                # We're in project root
                default_path = cwd / "backend" / "config" / "agno_prompts.json"
        else:
            default_path = config_path

        self._config_path = default_path
        self._config: AgnoPromptsConfig | None = None

    def _load_config(self) -> AgnoPromptsConfig:
        """Load prompts configuration from JSON file."""
        if self._config is None:
            if not self._config_path.exists():
                self._config = AgnoPromptsConfig()
            else:
                with self._config_path.open("r", encoding="utf-8") as f:
                    data = json.load(f)
                    self._config = AgnoPromptsConfig.model_validate(data)
        return self._config

    def get_enabled_prompts(self) -> list[PromptConfig]:
        """Get list of enabled prompt configurations."""
        config = self._load_config()
        return [p for p in config.prompts if p.enabled]

    def get_prompt_by_key(self, key: str) -> PromptConfig:
        """Get a specific prompt configuration by key.

        Args:
            key: The prompt configuration key.

        Returns:
            The prompt configuration.

        Raises:
            PromptNotFoundError: If the prompt configuration is not found.
        """
        config = self._load_config()
        for prompt in config.prompts:
            if prompt.key == key:
                return prompt

        raise PromptNotFoundError(prompt_key=key)

    def get_instructions(self, key: str = "default") -> list[str]:
        """Get instructions list for a specific prompt preset.

        Args:
            key: The prompt configuration key. Defaults to "default".

        Returns:
            List of instruction strings.

        Raises:
            PromptNotFoundError: If the prompt configuration is not found or disabled.
        """
        prompt = self.get_prompt_by_key(key)

        if not prompt.enabled:
            logger.warning(
                "Requested prompt is disabled",
                extra={"prompt_key": key},
            )
            raise PromptNotFoundError(prompt_key=key)

        logger.debug(
            "Retrieved instructions for prompt",
            extra={
                "prompt_key": key,
                "instruction_count": len(prompt.instructions),
            },
        )

        return prompt.instructions

    def get_system_message(self) -> str | None:
        """Get the global system message if configured."""
        config = self._load_config()
        return config.system_message

    def list_available_prompts(self) -> list[dict[str, str | bool]]:
        """List all available prompt presets with their metadata.

        Returns:
            List of dicts with 'key', 'name', and 'enabled' status.
        """
        config = self._load_config()
        return [
            {"key": p.key, "name": p.name, "enabled": p.enabled} for p in config.prompts
        ]

    def update_prompt_enabled(self, key: str, enabled: bool) -> None:
        """Enable or disable a specific prompt preset.

        Args:
            key: The prompt key to update
            enabled: Whether to enable or disable the prompt

        Raises:
            PromptNotFoundError: If the prompt key is not found
        """
        config = self._load_config()
        prompt_found = False

        for prompt in config.prompts:
            if prompt.key == key:
                prompt.enabled = enabled
                prompt_found = True
                break

        if not prompt_found:
            raise PromptNotFoundError(prompt_key=key)

        # Save updated config
        with self._config_path.open("w", encoding="utf-8") as f:
            json.dump(config.model_dump(), f, indent=2)
