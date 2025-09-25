"""Endpoints for managing MCP server metadata."""

from __future__ import annotations

from fastapi import APIRouter
from src.integrations.mcp import get_mcp_status
from src.models import ListMCPServersResponse, MCPServerInfo
from src.shared.response import APIResponse, create_success_response

router = APIRouter(prefix="/mcp", tags=["mcp"])


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
