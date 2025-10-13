"""Store and load Agno tools configurations."""

from __future__ import annotations

import importlib
import json
from pathlib import Path
from typing import Any

from src.core import get_logger
from src.shared.exceptions.agno import ToolkitLoadError, ToolkitNotFoundError

from .tools_config import AgnoToolsConfig, ToolkitConfig

logger = get_logger(__name__)


class ToolsConfigStore:
    """Manages loading and instantiation of Agno tools from configuration."""

    def __init__(self, config_path: Path | None = None) -> None:
        """Initialize the tools config store.

        Args:
            config_path: Path to agno_tools.json.
                If None, uses default config directory.
        """
        if config_path is None:
            # Try to find config relative to project root
            cwd = Path.cwd()
            # Check if we're in backend directory
            if cwd.name == "backend":
                default_path = cwd / "config" / "agno_tools.json"
            else:
                # We're in project root
                default_path = cwd / "backend" / "config" / "agno_tools.json"
        else:
            default_path = config_path

        self._config_path = default_path
        self._config: AgnoToolsConfig | None = None

    def _load_config(self) -> AgnoToolsConfig:
        """Load tools configuration from JSON file."""
        if self._config is None:
            if not self._config_path.exists():
                # Load default configuration
                default_path = (
                    Path(__file__).parent.parent.parent.parent
                    / "defaults"
                    / "default_agno_tools.json"
                )
                if default_path.exists():
                    with default_path.open("r", encoding="utf-8") as f:
                        data = json.load(f)
                        self._config = AgnoToolsConfig.model_validate(data)
                    # Copy default to config location
                    self._config_path.parent.mkdir(parents=True, exist_ok=True)
                    with self._config_path.open("w", encoding="utf-8") as f:
                        json.dump(data, f, indent=2)
                else:
                    self._config = AgnoToolsConfig()
            else:
                with self._config_path.open("r", encoding="utf-8") as f:
                    data = json.load(f)
                    self._config = AgnoToolsConfig.model_validate(data)
        return self._config

    def get_enabled_toolkits(self) -> list[ToolkitConfig]:
        """Get list of enabled toolkit configurations."""
        config = self._load_config()
        return [tk for tk in config.toolkits if tk.enabled]

    def load_toolkit_instances(self, *, strict: bool = False) -> list[Any]:
        """Dynamically load and instantiate enabled toolkits.

        Args:
            strict: If True, raise exception on first load failure.
                   If False, log warnings and continue loading other toolkits.

        Returns:
            List of instantiated toolkit objects ready to pass to Agent.

        Raises:
            ToolkitLoadError: If strict=True and a toolkit fails to load.
        """
        instances = []
        errors = []

        for tk_config in self.get_enabled_toolkits():
            try:
                logger.debug(
                    "Loading toolkit",
                    extra={
                        "toolkit_key": tk_config.key,
                        "toolkit_class": tk_config.toolkit_class,
                    },
                )

                # Parse the toolkit class path
                # e.g., "agno.tools.duckduckgo.DuckDuckGoTools"
                module_path, class_name = tk_config.toolkit_class.rsplit(".", 1)

                # Dynamically import the module
                module = importlib.import_module(module_path)

                # Get the class from the module
                toolkit_class = getattr(module, class_name)

                # Instantiate with config parameters
                instance = toolkit_class(**tk_config.config)
                instances.append(instance)

                logger.info(
                    "✓ Successfully loaded toolkit",
                    extra={
                        "toolkit_key": tk_config.key,
                        "toolkit_class": tk_config.toolkit_class,
                    },
                )

            except ImportError as e:
                error_msg = f"Module not found: {e}"
                errors.append((tk_config.key, error_msg))

                logger.warning(
                    "Failed to load toolkit: module import error",
                    extra={
                        "toolkit_key": tk_config.key,
                        "toolkit_class": tk_config.toolkit_class,
                        "error": error_msg,
                    },
                )

                if strict:
                    raise ToolkitLoadError(
                        toolkit_key=tk_config.key,
                        reason=error_msg,
                    ) from e

            except AttributeError as e:
                error_msg = f"Class not found in module: {e}"
                errors.append((tk_config.key, error_msg))

                logger.warning(
                    "Failed to load toolkit: class not found",
                    extra={
                        "toolkit_key": tk_config.key,
                        "toolkit_class": tk_config.toolkit_class,
                        "error": error_msg,
                    },
                )

                if strict:
                    raise ToolkitLoadError(
                        toolkit_key=tk_config.key,
                        reason=error_msg,
                    ) from e

            except Exception as e:
                error_msg = f"Unexpected error: {type(e).__name__}: {e}"
                errors.append((tk_config.key, error_msg))

                logger.error(
                    "Failed to load toolkit: unexpected error",
                    extra={
                        "toolkit_key": tk_config.key,
                        "toolkit_class": tk_config.toolkit_class,
                        "error": error_msg,
                    },
                    exc_info=True,
                )

                if strict:
                    raise ToolkitLoadError(
                        toolkit_key=tk_config.key,
                        reason=error_msg,
                    ) from e

        # Log summary
        if errors:
            logger.warning(
                "Toolkit loading completed with errors",
                extra={
                    "loaded_count": len(instances),
                    "failed_count": len(errors),
                    "failed_toolkits": [key for key, _ in errors],
                },
            )
        else:
            logger.info(
                "All toolkits loaded successfully",
                extra={"loaded_count": len(instances)},
            )

        return instances

    def get_toolkit_config(self, key: str) -> ToolkitConfig:
        """Get configuration for a specific toolkit by key.

        Args:
            key: The toolkit configuration key.

        Returns:
            The toolkit configuration.

        Raises:
            ToolkitNotFoundError: If the toolkit configuration is not found.
        """
        config = self._load_config()
        for tk in config.toolkits:
            if tk.key == key:
                return tk

        raise ToolkitNotFoundError(toolkit_key=key)

    def update_toolkit_enabled(self, key: str, enabled: bool) -> None:
        """Enable or disable a specific toolkit.

        Args:
            key: The toolkit key to update
            enabled: Whether to enable or disable the toolkit

        Raises:
            ToolkitNotFoundError: If the toolkit key is not found
        """
        config = self._load_config()
        toolkit_found = False

        for tk in config.toolkits:
            if tk.key == key:
                tk.enabled = enabled
                toolkit_found = True
                break

        if not toolkit_found:
            raise ToolkitNotFoundError(toolkit_key=key)

        # Save updated config
        with self._config_path.open("w", encoding="utf-8") as f:
            json.dump(config.model_dump(), f, indent=2)
