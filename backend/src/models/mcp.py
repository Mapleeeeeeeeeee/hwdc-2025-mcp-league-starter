"""Schemas for MCP server management endpoints."""

from __future__ import annotations

from pydantic import Field

from .base import APIBaseModel


class MCPToolSelection(APIBaseModel):
    server: str = Field(description="Target MCP server name")
    functions: list[str] | None = Field(
        default=None,
        description="Optional list of MCP function names to enable",
    )


class MCPServerInfo(APIBaseModel):
    name: str
    description: str | None = None
    connected: bool
    enabled: bool
    function_count: int
    functions: list[str]


class ListMCPServersResponse(APIBaseModel):
    initialized: bool
    servers: list[MCPServerInfo]


class ReloadMCPServerResponse(APIBaseModel):
    server_name: str
    success: bool
    message: str | None = None
    function_count: int = 0


class ReloadAllMCPServersResponse(APIBaseModel):
    success: bool
    reloaded_count: int
    failed_count: int
    results: list[ReloadMCPServerResponse]


# Peer node management schemas
class AddPeerNodeRequest(APIBaseModel):
    peer_name: str = Field(
        description="Unique name for the peer node",
        min_length=1,
        max_length=100,
    )
    peer_url: str = Field(
        description="HTTP URL of the peer's MCP endpoint (e.g., http://peer:8000/mcp)",
        pattern=r"^https?://",
    )
    auth_token: str | None = Field(
        default=None, description="Optional bearer token for authentication"
    )


class AddPeerNodeResponse(APIBaseModel):
    success: bool
    peer_name: str
    peer_url: str
    function_count: int
    message: str | None = None


class RemovePeerNodeResponse(APIBaseModel):
    success: bool
    peer_name: str
    message: str | None = None


class PeerNodeInfo(APIBaseModel):
    name: str
    url: str
    description: str | None = None
    connected: bool
    function_count: int


class ListPeerNodesResponse(APIBaseModel):
    peers: list[PeerNodeInfo]
