"""FastMCP server implementation exposing this application's capabilities."""

from __future__ import annotations

from typing import Any

from fastmcp import FastMCP

from src.core.logging import get_logger

logger = get_logger(__name__)

# Create FastMCP server instance
mcp_server = FastMCP(
    name="HWDC-2025-MCP-League",
    instructions="MCP server exposing conversation and MCP management capabilities",
)


@mcp_server.tool
def list_mcp_servers() -> dict[str, Any]:
    """List all configured MCP servers and their status.

    Returns:
        Dictionary containing server information including:
        - initialized: Whether MCP system is initialized
        - servers: Dict of server name to server info
        - total_servers: Count of configured servers
        - total_functions: Total number of available MCP functions
        - available_servers: List of connected server names
    """
    from src.integrations.mcp import get_mcp_status

    logger.info("MCP tool called: list_mcp_servers")
    return get_mcp_status()


@mcp_server.tool
async def reload_mcp_server(server_name: str) -> dict[str, Any]:
    """Reload a specific MCP server by name.

    Args:
        server_name: Name of the MCP server to reload

    Returns:
        Dictionary containing:
        - server_name: Name of the server
        - success: Whether reload succeeded
        - message: Status message
        - function_count: Number of functions available after reload
    """
    from src.integrations.mcp import reload_mcp_server as _reload_server

    logger.info("MCP tool called: reload_mcp_server (server=%s)", server_name)
    result = await _reload_server(server_name)
    return {
        "server_name": result.server_name,
        "success": result.success,
        "message": result.message,
        "function_count": result.function_count,
    }


@mcp_server.tool
async def reload_all_mcp_servers() -> dict[str, Any]:
    """Reload all enabled MCP servers.

    Returns:
        Dictionary containing:
        - success: Whether any servers reloaded successfully
        - reloaded_count: Number of servers successfully reloaded
        - failed_count: Number of servers that failed to reload
        - results: List of per-server reload results
    """
    from src.integrations.mcp import reload_all_mcp_servers as _reload_all

    logger.info("MCP tool called: reload_all_mcp_servers")
    result = await _reload_all()
    return {
        "success": result.success,
        "reloaded_count": result.reloaded_count,
        "failed_count": result.failed_count,
        "results": [
            {
                "server_name": r.server_name,
                "success": r.success,
                "message": r.message,
                "function_count": r.function_count,
            }
            for r in result.results
        ],
    }


@mcp_server.tool
def get_mcp_server_functions(server_name: str) -> list[str]:
    """Get list of available functions for a specific MCP server.

    Args:
        server_name: Name of the MCP server

    Returns:
        List of function names available on the server
    """
    from src.integrations.mcp import get_mcp_server_functions as _get_functions

    logger.info("MCP tool called: get_mcp_server_functions (server=%s)", server_name)
    return _get_functions(server_name)


@mcp_server.tool
def get_available_mcp_servers() -> list[str]:
    """Get list of all connected MCP server names.

    Returns:
        List of server names that are currently connected
    """
    from src.integrations.mcp import get_available_mcp_servers as _get_servers

    logger.info("MCP tool called: get_available_mcp_servers")
    return _get_servers()


@mcp_server.resource("config://app")
def get_app_config() -> dict[str, Any]:
    """Get application configuration information.

    Returns:
        Dictionary containing:
        - environment: Current environment (dev/staging/production)
        - host: Server host
        - port: Server port
        - enable_mcp_system: Whether MCP system is enabled
        - cors_origins: Allowed CORS origins
    """
    from src.config import settings
    from src.integrations.mcp.config import mcp_settings

    logger.info("MCP resource accessed: config://app")
    return {
        "environment": settings.environment,
        "host": settings.host,
        "port": settings.port,
        "enable_mcp_system": mcp_settings.enable_mcp_system,
        "cors_origins": settings.cors_origins,
    }


@mcp_server.resource("health://system")
def get_system_health() -> dict[str, Any]:
    """Get system health status.

    Returns:
        Dictionary containing:
        - status: "healthy" or "unhealthy"
        - mcp_initialized: Whether MCP system is initialized
        - available_servers: List of connected MCP servers
    """
    from src.integrations.mcp import get_available_mcp_servers, is_mcp_initialized

    logger.info("MCP resource accessed: health://system")
    return {
        "status": "healthy",
        "mcp_initialized": is_mcp_initialized(),
        "available_servers": get_available_mcp_servers(),
    }
