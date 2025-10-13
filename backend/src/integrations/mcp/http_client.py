"""HTTP/SSE transport client for Model Context Protocol."""

from __future__ import annotations

import httpx
from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client

from src.core.logging import get_logger
from src.shared.exceptions.mcp import (
    MCPAuthenticationError,
    MCPConnectionError,
    MCPConnectionTimeoutError,
    MCPHTTPError,
    MCPInvalidConfigError,
)

from .http_connection import HTTPMCPConnection
from .server_params import MCPServerParams

logger = get_logger(__name__)

# Constants for HTTP client configuration
_HTTP_CLIENT_TERMINATE_ON_CLOSE = (
    False  # Manual lifecycle management for persistent connections
)
_HTTP_CLIENT_DEFAULT_TIMEOUT = 60  # Default timeout in seconds


async def create_http_mcp_connection(
    params: MCPServerParams,
) -> HTTPMCPConnection:
    """
    Create and connect to a remote HTTP MCP server with persistent session.

    This function establishes a persistent connection to an HTTP/SSE MCP server
    and returns a connection object that maintains the session state.

    Args:
        params: Server parameters containing:
            - url: The HTTP endpoint URL (e.g., "https://api.example.com/mcp")
            - auth: Optional authentication configuration
            - timeout_seconds: Connection timeout

    Returns:
        HTTPMCPConnection object with active session and cached tools

    Raises:
        MCPInvalidConfigError: If URL is missing or configuration is invalid
        MCPConnectionError: If HTTP connection fails
        MCPConnectionTimeoutError: If connection times out

    Example:
        ```python
        params = MCPServerParams(
            name="remote-api",
            type="http",
            url="https://api.example.com/mcp",
            auth=HTTPAuthConfig(type="bearer", token="xxx"),
        )

        connection = await create_http_mcp_connection(params)
        # Use connection.session to interact with the server
        # Remember to call await connection.close() when done
        ```
    """
    if not params.url:
        raise MCPInvalidConfigError(
            server_name=params.name,
            reason="HTTP transport requires a URL",
        )

    logger.info(
        "Connecting to HTTP MCP server '%s' at %s",
        params.name,
        params.url,
    )

    # Build headers for authentication
    headers: dict[str, str] = {}
    if params.auth:
        try:
            headers.update(params.auth.build_header())
        except ValueError as exc:
            logger.warning(
                "Failed to build auth header for MCP server '%s': %s",
                params.name,
                exc,
            )

    try:
        # Create the streamable HTTP client (without using context manager)
        # We need to manually manage the lifecycle
        client_context = streamablehttp_client(
            url=params.url,
            headers=headers if headers else None,
            timeout=params.timeout_seconds or _HTTP_CLIENT_DEFAULT_TIMEOUT,
            terminate_on_close=_HTTP_CLIENT_TERMINATE_ON_CLOSE,
        )

        # Enter the context and get the streams
        read_stream, write_stream, get_session_id = await client_context.__aenter__()

        # Create a ClientSession (also without using context manager)
        session = ClientSession(read_stream, write_stream)
        await session.__aenter__()

        # Initialize the session to establish the connection
        await session.initialize()

        # Get the session ID
        session_id = get_session_id()

        # List available tools and cache them
        tools_result = await session.list_tools()
        tools = tools_result.tools if tools_result.tools else []

        logger.info(
            "Successfully connected to HTTP MCP server '%s' (Session ID: %s, %s tools)",
            params.name,
            session_id,
            len(tools),
        )

        # Create and return the connection object
        return HTTPMCPConnection(
            session=session,
            session_id=session_id,
            tools=tools,
            read_stream=read_stream,
            write_stream=write_stream,
            get_session_id_callback=get_session_id,
            client_context=client_context,  # Store for proper cleanup
        )

    except ValueError as exc:
        # Configuration or validation errors
        logger.error(
            "Invalid configuration for HTTP MCP server '%s': %s",
            params.name,
            exc,
        )
        raise MCPInvalidConfigError(
            server_name=params.name,
            reason=str(exc),
        ) from exc
    except TimeoutError as exc:
        # Connection timeout
        logger.error(
            "Connection to HTTP MCP server '%s' at %s timed out",
            params.name,
            params.url,
        )
        raise MCPConnectionTimeoutError(
            server_name=params.name,
            transport="http",
            timeout_seconds=params.timeout_seconds,
        ) from exc
    except httpx.HTTPStatusError as exc:
        # HTTP status errors (4xx, 5xx)
        status_code = exc.response.status_code
        response_text = (
            exc.response.text[:200] if exc.response.text else "No response body"
        )

        # Handle authentication errors (401, 403)
        if status_code in (401, 403):
            logger.error(
                "Authentication failed for MCP server '%s' at %s: HTTP %s",
                params.name,
                params.url,
                status_code,
            )
            raise MCPAuthenticationError(
                server_name=params.name,
                url=params.url,
                status_code=status_code,
                reason=f"Check authentication token. Response: {response_text}",
            ) from exc

        # Handle other HTTP errors
        logger.error(
            "HTTP %s error from MCP server '%s' at %s: %s",
            status_code,
            params.name,
            params.url,
            response_text,
        )
        raise MCPHTTPError(
            server_name=params.name,
            url=params.url,
            status_code=status_code,
            reason=response_text,
        ) from exc
    except httpx.ConnectError as exc:
        # Network connection errors (DNS, connection refused, etc.)
        logger.error(
            "Network connection error for MCP server '%s' at %s: %s",
            params.name,
            params.url,
            exc,
        )
        raise MCPConnectionError(
            server_name=params.name,
            transport="http",
            reason=(
                f"Cannot reach server at {params.url}. "
                f"Check URL and network connectivity: {exc}"
            ),
        ) from exc
    except httpx.HTTPError as exc:
        # Other HTTP errors (network issues, etc.)
        logger.error(
            "HTTP connection error for MCP server '%s' at %s: %s",
            params.name,
            params.url,
            exc,
        )
        raise MCPConnectionError(
            server_name=params.name,
            transport="http",
            reason=str(exc),
        ) from exc
    except Exception as exc:
        # Unexpected errors (may include MCP SDK internal errors)
        error_msg = str(exc)
        error_type = type(exc).__name__

        # Try to extract HTTP status code from error message if possible
        status_code_hint = ""
        if "502" in error_msg or "Bad Gateway" in error_msg:
            status_code_hint = (
                " (Possible HTTP 502 Bad Gateway - target server unavailable)"
            )
        elif "401" in error_msg or "Unauthorized" in error_msg:
            status_code_hint = (
                " (Possible HTTP 401 Unauthorized - check authentication)"
            )
        elif "403" in error_msg or "Forbidden" in error_msg:
            status_code_hint = " (Possible HTTP 403 Forbidden - check permissions)"
        elif "404" in error_msg or "Not Found" in error_msg:
            status_code_hint = " (Possible HTTP 404 Not Found - check URL)"
        elif "timeout" in error_msg.lower():
            status_code_hint = " (Connection timeout - server not responding)"

        logger.error(
            "Failed to connect to HTTP MCP server '%s' at %s\n"
            "   Error type: %s\n"
            "   Error message: %s%s",
            params.name,
            params.url,
            error_type,
            error_msg,
            status_code_hint,
        )

        raise MCPConnectionError(
            server_name=params.name,
            transport="http",
            reason=f"{error_type}: {error_msg}{status_code_hint}",
        ) from exc
