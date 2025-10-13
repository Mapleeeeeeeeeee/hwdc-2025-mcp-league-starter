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
