"""Registry helpers for orchestrating Agno toolkits and MCP tool access."""

from __future__ import annotations

import importlib
import pkgutil
from pathlib import Path
from typing import Any, ClassVar

import agno.tools as tools_pkg
from agno.tools import Toolkit

from src.config import settings
from src.core.logging import get_logger

from .config import mcp_settings
from .manager import get_mcp_toolkit

logger = get_logger(__name__)


class ToolRegistry:
    """Central registry for discovering and instantiating tools."""

    _instance: ClassVar[ToolRegistry | None] = None

    def __new__(cls) -> ToolRegistry:
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self) -> None:
        # 避免重新初始時覆蓋既有狀態
        if not hasattr(self, "_tool_classes"):
            self._tool_classes: dict[str, type[Toolkit]] = {}
        if not hasattr(self, "_loaded"):
            self._loaded: bool = False

    def get_tool_class(self, name: str) -> type[Toolkit] | None:
        if not self._loaded:
            self._load_tools()
        return self._tool_classes.get(name)

    def get_all_tool_names(self) -> list[str]:
        if not self._loaded:
            self._load_tools()
        return list(self._tool_classes.keys())

    def get_tool_instance(
        self, tool_config: dict[str, Any], **dependencies: Any
    ) -> Any | None:
        tool_type = tool_config.get("type", "toolkit")

        if tool_type == "toolkit":
            return self._create_toolkit_instance(tool_config, **dependencies)
        if tool_type == "mcp":
            return self._create_mcp_instance(tool_config)

        logger.error("Unsupported tool type '%s'", tool_type)
        return None

    def _create_toolkit_instance(
        self, config: dict[str, Any], **dependencies: Any
    ) -> Any | None:
        name = config.get("name")
        if not name:
            logger.warning("Toolkit configuration missing name")
            return None

        params = config.get("params", {})
        tool_class = self.get_tool_class(name)

        if not tool_class:
            logger.warning("Toolkit '%s' not registered", name)
            return None

        try:
            combined = {**dependencies, **params}
            instance = tool_class(**combined)
            logger.debug("Created toolkit '%s'", name)
            return instance
        except Exception as exc:  # pragma: no cover - instantiation failure
            logger.error("Failed to create toolkit '%s': %s", name, exc)
            return None

    def _create_mcp_instance(self, config: dict[str, Any]) -> Any | None:
        server_name = config.get("name")
        if not server_name:
            logger.warning("MCP configuration missing server name")
            return None

        if not config.get("enabled", True):
            logger.debug("MCP server '%s' disabled in configuration", server_name)
            return None

        if not mcp_settings.enable_mcp_system:
            logger.debug("MCP system disabled; skipping server '%s'", server_name)
            return None

        allowed_funcs = config.get("functions") or config.get("allowed_functions")
        if allowed_funcs is not None:
            if isinstance(allowed_funcs, list):
                allowed_funcs = [
                    str(name).strip() for name in allowed_funcs if str(name).strip()
                ]
            else:
                logger.warning(
                    "MCP configuration for '%s' has invalid functions list; ignoring",
                    server_name,
                )
                allowed_funcs = None

        toolkit = get_mcp_toolkit(
            server_name,
            allowed_functions=allowed_funcs,
        )
        if toolkit is None:
            logger.warning("MCP server '%s' not available", server_name)
            return None

        logger.info(
            "MCP toolkit created for server '%s' with %s function(s)",
            server_name,
            len(toolkit.functions),
        )
        return toolkit

    def _load_tools(self) -> None:
        if self._loaded:
            return

        logger.info("Loading toolkits")

        extra_tools_dir = Path.cwd() / "domain" / "agno" / "tools"
        if extra_tools_dir.is_dir():
            logger.debug("Adding additional tools directory: %s", extra_tools_dir)
            tools_pkg.__path__.append(str(extra_tools_dir))
        else:
            logger.debug("Optional tools directory not found: %s", extra_tools_dir)

        if settings.environment == "development":
            logger.debug("Development environment detected; loading defaults only")
        else:
            self._scan_and_register_tools()

        self._load_default_tools()
        self._loaded = True
        logger.info(
            "Tool loading complete; available toolkits: %s",
            ", ".join(self._tool_classes.keys()) or "<none>",
        )

    def _scan_and_register_tools(self) -> None:
        for _, module_name, _ in pkgutil.iter_modules(tools_pkg.__path__):
            try:
                module = importlib.import_module(f"{tools_pkg.__name__}.{module_name}")
            except ImportError as exc:  # pragma: no cover - dynamic imports
                logger.debug("Skipping toolkit module '%s': %s", module_name, exc)
                continue

            for attr_name in dir(module):
                attr = getattr(module, attr_name)
                if (
                    isinstance(attr, type)
                    and issubclass(attr, Toolkit)
                    and attr is not Toolkit
                ):
                    self._tool_classes[attr_name] = attr
                    logger.debug("Registered toolkit '%s'", attr_name)

    def _load_default_tools(self) -> None:
        try:
            from agno.tools.calculator import CalculatorTools

            self._tool_classes["CalculatorTools"] = CalculatorTools
        except ImportError:  # pragma: no cover - optional dependency
            logger.debug("CalculatorTools not available")

    def validate_tool_config(self, tool_config: dict[str, Any]) -> bool:
        if not isinstance(tool_config, dict):
            logger.warning("Tool configuration must be a mapping")
            return False

        if "name" not in tool_config:
            logger.error("Tool configuration missing name")
            return False

        tool_type = tool_config.get("type", "toolkit")
        if tool_type not in {"toolkit", "mcp"}:
            logger.error("Unsupported tool type '%s'", tool_type)
            return False

        return True

    def get_tool_info(self) -> dict[str, Any]:
        if not self._loaded:
            self._load_tools()

        return {
            "loaded": self._loaded,
            "total_toolkit_classes": len(self._tool_classes),
            "available_toolkits": list(self._tool_classes.keys()),
            "supported_types": ["toolkit", "mcp"],
        }


tool_registry = ToolRegistry()
