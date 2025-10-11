"""HTTP/SSE transport client for Model Context Protocol."""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any

from mcp.client.streamable_http import streamablehttp_client

from src.core.logging import get_logger

from .server_params import MCPServerParams

logger = get_logger(__name__)


@asynccontextmanager
async def http_mcp_client(
    params: MCPServerParams,
) -> AsyncIterator[tuple[Any, Any, Any]]:
    """
    Create and connect to a remote HTTP MCP server.

    This function provides a context manager for connecting to MCP servers
    using the HTTP/SSE transport protocol. It uses the official MCP Python SDK's
    streamablehttp_client implementation.

    Args:
        params: Server parameters containing:
            - url: The HTTP endpoint URL (e.g., "https://api.example.com/mcp")
            - auth: Optional authentication configuration
            - timeout_seconds: Connection timeout

    Yields:
        Tuple of (read_stream, write_stream, session_info) for MCP communication

    Raises:
        ValueError: If URL is missing or invalid
        httpx.HTTPError: If connection fails
        asyncio.TimeoutError: If connection times out

    Example:
        ```python
        from mcp import ClientSession

        params = MCPServerParams(
            name="remote-api",
            transport=TransportType.HTTP,
            url="https://api.example.com/mcp",
            auth=HTTPAuthConfig(type="bearer", token="xxx"),
        )

        async with http_mcp_client(params) as (read, write, _):
            async with ClientSession(read, write) as session:
                await session.initialize()
                tools = await session.list_tools()
        ```
    """
    if not params.url:
        msg = f"HTTP MCP client for '{params.name}' requires a URL"
        raise ValueError(msg)

    logger.info(
        "Connecting to HTTP MCP server '%s' at %s",
        params.name,
        params.url,
    )

    # Build headers for authentication
    headers: dict[str, str] = {}
    if params.auth and params.auth.token:
        if params.auth.type == "bearer":
            headers[params.auth.header_name] = f"Bearer {params.auth.token}"
        elif params.auth.type == "api_key":
            headers[params.auth.header_name] = params.auth.token
        else:
            logger.warning(
                "Unknown auth type '%s' for MCP server '%s', skipping auth",
                params.auth.type,
                params.name,
            )

    try:
        # Use the official MCP SDK's streamable HTTP client
        async with streamablehttp_client(
            url=params.url,
            headers=headers if headers else None,
            timeout=params.timeout_seconds,
        ) as (read_stream, write_stream, session_info):
            logger.info(
                "Successfully connected to HTTP MCP server '%s'",
                params.name,
            )
            yield read_stream, write_stream, session_info

    except Exception as exc:
        logger.error(
            "Failed to connect to HTTP MCP server '%s' at %s: %s",
            params.name,
            params.url,
            exc,
        )
        raise
    finally:
        logger.info(
            "Disconnected from HTTP MCP server '%s'",
            params.name,
        )
