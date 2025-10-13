"""Endpoints for managing MCP server metadata."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, status
from src.core import get_logger
from src.integrations.mcp import (
    add_peer_node,
    get_mcp_status,
    list_peer_nodes,
    reload_all_mcp_servers,
    reload_mcp_server,
    remove_peer_node,
)
from src.models import (
    AddPeerNodeRequest,
    AddPeerNodeResponse,
    ListMCPServersResponse,
    ListPeerNodesResponse,
    MCPServerInfo,
    PeerNodeInfo,
    ReloadAllMCPServersResponse,
    ReloadMCPServerResponse,
    RemovePeerNodeResponse,
)
from src.shared.exceptions import (
    MCPServerDisabledError,
    MCPServerNotFoundError,
    MCPServerReloadError,
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
    try:
        payload = await reload_all_mcp_servers()
        return create_success_response(data=payload, message="All servers reloaded")
    except Exception as exc:
        logger.error("Failed to reload all MCP servers: %s", exc, exc_info=True)
        # Return a partial success response instead of raising
        return create_success_response(
            data=ReloadAllMCPServersResponse(
                success=False,
                reloaded_count=0,
                failed_count=0,
                results=[],
            ),
            message=f"Failed to reload servers: {exc}",
        )


@router.post(
    "/servers/{server_name}:reload",
    response_model=APIResponse[ReloadMCPServerResponse],
)
async def reload_server(server_name: str) -> APIResponse[ReloadMCPServerResponse]:
    """Reload a specific MCP server by name."""
    logger.info("Received request to reload MCP server '%s'", server_name)
    try:
        payload = await reload_mcp_server(server_name)
        return create_success_response(
            data=payload,
            message=f"Server '{server_name}' reloaded successfully",
        )
    except (MCPServerNotFoundError, MCPServerDisabledError) as exc:
        # These are expected errors that should return proper error responses
        logger.warning("Server reload validation failed: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    except MCPServerReloadError as exc:
        # Server reload failed but we can return a structured response
        logger.error("Server reload failed: %s", exc)
        return create_success_response(
            data=ReloadMCPServerResponse(
                server_name=server_name,
                success=False,
                message=str(exc),
                function_count=0,
            ),
            message=f"Failed to reload server '{server_name}'",
        )
    except Exception as exc:
        logger.error(
            f"Unexpected error reloading server '{server_name}': {exc}",
            exc_info=True,
        )
        return create_success_response(
            data=ReloadMCPServerResponse(
                server_name=server_name,
                success=False,
                message=f"Unexpected error: {exc}",
                function_count=0,
            ),
            message=f"Failed to reload server '{server_name}'",
        )


# Peer-to-peer MCP node management endpoints


@router.get(
    "/peers",
    response_model=APIResponse[ListPeerNodesResponse],
    summary="List all peer MCP nodes",
)
async def list_peers() -> APIResponse[ListPeerNodesResponse]:
    """List all connected peer MCP nodes (other containers running this application)."""
    logger.info("Received request to list peer nodes")
    peers = list_peer_nodes()

    peer_infos = [
        PeerNodeInfo(
            name=peer["name"],
            url=peer["url"],
            description=peer.get("description"),
            connected=peer["connected"],
            function_count=peer["function_count"],
        )
        for peer in peers
    ]

    payload = ListPeerNodesResponse(peers=peer_infos)
    return create_success_response(
        data=payload, message=f"Found {len(peer_infos)} peer node(s)"
    )


@router.post(
    "/peers",
    response_model=APIResponse[AddPeerNodeResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Add a new peer MCP node",
)
async def add_peer(request: AddPeerNodeRequest) -> APIResponse[AddPeerNodeResponse]:
    """
    Add a peer MCP node for peer-to-peer communication.

    This allows this container to connect to another container running
    the same application and use its exposed MCP tools.
    """
    logger.info(
        "Received request to add peer node '%s' at %s",
        request.peer_name,
        request.peer_url,
    )

    try:
        result = await add_peer_node(
            request.peer_name, request.peer_url, auth_token=request.auth_token
        )

        payload = AddPeerNodeResponse(
            success=result["success"],
            peer_name=result["peer_name"],
            peer_url=result["peer_url"],
            function_count=result["function_count"],
            message=f"Peer node '{request.peer_name}' added successfully",
        )

        return create_success_response(
            data=payload, message=f"Peer node '{request.peer_name}' connected"
        )
    except ValueError as exc:
        logger.error("Failed to add peer node: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)
        ) from exc
    except Exception as exc:
        logger.error("Unexpected error adding peer node: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to add peer node",
        ) from exc


@router.delete(
    "/peers/{peer_name}",
    response_model=APIResponse[RemovePeerNodeResponse],
    summary="Remove a peer MCP node",
)
async def remove_peer(peer_name: str) -> APIResponse[RemovePeerNodeResponse]:
    """Remove a peer MCP node connection."""
    logger.info("Received request to remove peer node '%s'", peer_name)

    try:
        result = await remove_peer_node(peer_name)

        payload = RemovePeerNodeResponse(
            success=result["success"],
            peer_name=result["peer_name"],
            message=f"Peer node '{peer_name}' removed successfully",
        )

        return create_success_response(
            data=payload, message=f"Peer node '{peer_name}' disconnected"
        )
    except ValueError as exc:
        logger.error("Failed to remove peer node: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)
        ) from exc
    except Exception as exc:
        logger.error("Unexpected error removing peer node: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to remove peer node",
        ) from exc
