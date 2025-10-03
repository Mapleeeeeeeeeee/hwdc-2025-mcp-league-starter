"""MCP server management exceptions."""

from __future__ import annotations

from src.core.exceptions import BadRequestError, InternalServerError


class MCPServerNotFoundError(BadRequestError):
    """MCP server not found in configuration."""

    def __init__(self, server_name: str, **kwargs) -> None:
        super().__init__(
            detail=f"MCP server '{server_name}' not found in configuration",
            i18n_key="errors.mcp.server_not_found",
            i18n_params={"server_name": server_name},
            context={"server_name": server_name},
            **kwargs,
        )


class MCPServerDisabledError(BadRequestError):
    """MCP server is disabled in configuration."""

    def __init__(self, server_name: str, **kwargs) -> None:
        super().__init__(
            detail=f"MCP server '{server_name}' is disabled",
            i18n_key="errors.mcp.server_disabled",
            i18n_params={"server_name": server_name},
            context={"server_name": server_name},
            **kwargs,
        )


class MCPServerReloadError(InternalServerError):
    """Failed to reload MCP server."""

    def __init__(self, server_name: str, reason: str | None = None, **kwargs) -> None:
        detail = f"Failed to reload MCP server '{server_name}'"
        if reason:
            detail = f"{detail}: {reason}"

        super().__init__(
            detail=detail,
            i18n_key="errors.mcp.reload_failed",
            i18n_params={"server_name": server_name, "reason": reason or "Unknown"},
            context={"server_name": server_name, "reason": reason},
            **kwargs,
        )


class MCPNoServersAvailableError(BadRequestError):
    """No enabled MCP servers available."""

    def __init__(self, **kwargs) -> None:
        super().__init__(
            detail="No enabled MCP servers available to reload",
            i18n_key="errors.mcp.no_servers_available",
            **kwargs,
        )
