"""MCP server management exceptions."""

from __future__ import annotations

from src.core.exceptions import (
    BadGatewayError,
    BadRequestError,
    GatewayTimeoutError,
    InternalServerError,
)


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


class MCPConnectionError(BadGatewayError):
    """Failed to connect to MCP server."""

    def __init__(
        self,
        server_name: str,
        transport: str,
        reason: str | None = None,
        **kwargs,
    ) -> None:
        detail = f"Failed to connect to MCP server '{server_name}' via {transport}"
        if reason:
            detail = f"{detail}: {reason}"

        super().__init__(
            detail=detail,
            i18n_key="errors.mcp.connection_failed",
            i18n_params={
                "server_name": server_name,
                "transport": transport,
                "reason": reason or "Unknown",
            },
            context={
                "server_name": server_name,
                "transport": transport,
                "reason": reason,
            },
            retryable=True,
            retry_after=30,
            **kwargs,
        )


class MCPConnectionTimeoutError(GatewayTimeoutError):
    """MCP server connection timed out."""

    def __init__(
        self,
        server_name: str,
        transport: str,
        timeout_seconds: int,
        **kwargs,
    ) -> None:
        super().__init__(
            detail=f"Connection to MCP server '{server_name}' via {transport} "
            f"timed out after {timeout_seconds}s",
            i18n_key="errors.mcp.connection_timeout",
            i18n_params={
                "server_name": server_name,
                "transport": transport,
                "timeout_seconds": timeout_seconds,
            },
            context={
                "server_name": server_name,
                "transport": transport,
                "timeout_seconds": timeout_seconds,
            },
            retryable=True,
            retry_after=timeout_seconds,
            **kwargs,
        )


class MCPInvalidConfigError(BadRequestError):
    """Invalid MCP server configuration."""

    def __init__(self, server_name: str, reason: str, **kwargs) -> None:
        super().__init__(
            detail=f"Invalid configuration for MCP server '{server_name}': {reason}",
            i18n_key="errors.mcp.invalid_config",
            i18n_params={"server_name": server_name, "reason": reason},
            context={"server_name": server_name, "reason": reason},
            **kwargs,
        )


class MCPToolExecutionError(InternalServerError):
    """MCP tool execution failed."""

    def __init__(
        self,
        server_name: str,
        tool_name: str,
        reason: str | None = None,
        **kwargs,
    ) -> None:
        detail = f"Tool '{tool_name}' on MCP server '{server_name}' failed"
        if reason:
            detail = f"{detail}: {reason}"

        super().__init__(
            detail=detail,
            i18n_key="errors.mcp.tool_execution_failed",
            i18n_params={
                "server_name": server_name,
                "tool_name": tool_name,
                "reason": reason or "Unknown",
            },
            context={
                "server_name": server_name,
                "tool_name": tool_name,
                "reason": reason,
            },
            **kwargs,
        )
