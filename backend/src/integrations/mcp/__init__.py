"""Public API surface for the MCP integration package."""

from __future__ import annotations

from importlib import import_module
from typing import TYPE_CHECKING, Any

__all__ = [
    "MCPManager",
    "MCPToolkit",
    "MCPServerParams",
    "MCPParamsManager",
    "MCPSettings",
    "mcp_settings",
    "default_params_manager",
    "get_mcp_manager",
    "get_mcp_toolkit",
    "initialize_mcp_system",
    "get_mcp_status",
    "graceful_mcp_cleanup",
    "is_mcp_initialized",
    "get_available_mcp_servers",
    "get_mcp_server_functions",
]

_ATTR_MAP: dict[str, tuple[str, str]] = {
    "MCPManager": (".manager", "MCPManager"),
    "initialize_mcp_system": (".manager", "initialize_mcp_system"),
    "get_mcp_status": (".manager", "get_mcp_status"),
    "graceful_mcp_cleanup": (".manager", "graceful_mcp_cleanup"),
    "is_mcp_initialized": (".manager", "is_mcp_initialized"),
    "get_available_mcp_servers": (".manager", "get_available_mcp_servers"),
    "get_mcp_server_functions": (".manager", "get_mcp_server_functions"),
    "MCPToolkit": (".toolkit", "MCPToolkit"),
    "MCPServerParams": (".server_params", "MCPServerParams"),
    "MCPParamsManager": (".server_params", "MCPParamsManager"),
    "default_params_manager": (".server_params", "default_params_manager"),
    "MCPSettings": (".settings", "MCPSettings"),
    "mcp_settings": (".settings", "mcp_settings"),
}

if TYPE_CHECKING:  # pragma: no cover - type checking only
    from .manager import (
        MCPManager,
        get_available_mcp_servers,
        get_mcp_server_functions,
        get_mcp_status,
        graceful_mcp_cleanup,
        initialize_mcp_system,
        is_mcp_initialized,
    )
    from .server_params import (
        MCPParamsManager,
        MCPServerParams,
        default_params_manager,
    )
    from .settings import MCPSettings, mcp_settings
    from .toolkit import MCPToolkit


def __getattr__(name: str) -> Any:
    if name not in _ATTR_MAP:
        raise AttributeError(f"module '{__name__}' has no attribute '{name}'")

    module_path, attr_name = _ATTR_MAP[name]
    module = import_module(f"{__name__}{module_path}")
    value = getattr(module, attr_name)
    globals()[name] = value
    return value


def __dir__() -> list[str]:
    return sorted(__all__)


def get_mcp_manager() -> MCPManager:
    from .manager import MCPManager

    return MCPManager()


def get_mcp_toolkit(server_name: str) -> MCPToolkit | None:
    from .manager import MCPManager

    return MCPManager().get_toolkit_for_server(server_name)
