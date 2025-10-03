"""Endpoints for managing MCP server metadata."""

from __future__ import annotations

from fastapi import APIRouter
from src.core import get_logger
from src.integrations.mcp import (
    get_mcp_status,
    reload_all_mcp_servers,
    reload_mcp_server,
)
from src.models import (
    ListMCPServersResponse,
    MCPServerInfo,
    ReloadAllMCPServersResponse,
    ReloadMCPServerResponse,
)
from src.shared.response import APIResponse, create_success_response

router = APIRouter(prefix="/mcp", tags=["mcp"])
logger = get_logger(__name__)


@router.get(
    "/servers",
    response_model=APIResponse[ListMCPServersResponse],
)
async def list_mcp_servers() -> APIResponse[ListMCPServersResponse]:
    """Return available MCP servers and their exposed functions."""
    status = get_mcp_status()
    servers = []
    for name, info in status.get("servers", {}).items():
        servers.append(
            MCPServerInfo(
                name=name,
                description=info.get("description"),
                connected=bool(info.get("connected")),
                enabled=bool(info.get("enabled")),
                function_count=int(info.get("function_count", 0)),
                functions=info.get("functions", []),
            )
        )

    payload = ListMCPServersResponse(
        initialized=bool(status.get("initialized", False)),
        servers=servers,
    )
    return create_success_response(data=payload, message="MCP servers retrieved")


@router.post(
    "/servers:reload",
    response_model=APIResponse[ReloadAllMCPServersResponse],
)
async def reload_all_servers() -> APIResponse[ReloadAllMCPServersResponse]:
    """Reload all enabled MCP servers."""
    logger.info("Received request to reload all MCP servers")
    payload = await reload_all_mcp_servers()
    return create_success_response(data=payload, message="All servers reloaded")


@router.post(
    "/servers/{server_name}:reload",
    response_model=APIResponse[ReloadMCPServerResponse],
)
async def reload_server(server_name: str) -> APIResponse[ReloadMCPServerResponse]:
    """Reload a specific MCP server by name."""
    logger.info("Received request to reload MCP server '%s'", server_name)
    payload = await reload_mcp_server(server_name)
    return create_success_response(
        data=payload,
        message=f"Server '{server_name}' reloaded successfully",
    )
