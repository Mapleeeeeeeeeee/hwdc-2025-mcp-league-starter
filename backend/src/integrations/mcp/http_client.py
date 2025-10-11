"""HTTP/SSE transport client for Model Context Protocol."""

from __future__ import annotations

from mcp.client.streamable_http import streamablehttp_client

from src.core.logging import get_logger

from .http_connection import HTTPMCPConnection
from .server_params import MCPServerParams

logger = get_logger(__name__)


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
        ValueError: If URL is missing or invalid
        httpx.HTTPError: If connection fails
        asyncio.TimeoutError: If connection times out

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
        # Create the streamable HTTP client (without using context manager)
        # We need to manually manage the lifecycle
        client_context = streamablehttp_client(
            url=params.url,
            headers=headers if headers else None,
            timeout=params.timeout_seconds,
            terminate_on_close=False,  # We'll handle termination manually
        )

        # Enter the context and get the streams
        read_stream, write_stream, get_session_id = await client_context.__aenter__()

        # Create a ClientSession (also without using context manager)
        from mcp import ClientSession

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

    except Exception as exc:
        logger.error(
            "Failed to connect to HTTP MCP server '%s' at %s: %s",
            params.name,
            params.url,
            exc,
        )
        raise
