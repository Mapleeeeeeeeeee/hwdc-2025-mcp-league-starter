"""HTTP/SSE MCP connection management."""

from __future__ import annotations

from collections.abc import Callable
from contextlib import AbstractAsyncContextManager
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from mcp import ClientSession
from mcp.types import Tool

from src.core.logging import get_logger

if TYPE_CHECKING:
    from anyio.streams.memory import MemoryObjectReceiveStream, MemoryObjectSendStream
    from mcp.shared.session import SessionMessage

logger = get_logger(__name__)


@dataclass
class HTTPMCPConnection:
    """
    Represents a persistent HTTP/SSE MCP connection.

    This class maintains the state of an active HTTP MCP session,
    including the ClientSession, streams, and cached metadata.

    Attributes:
        session: Active MCP ClientSession for communication
        session_id: Unique session identifier from the server
        tools: List of available tools from the server
        read_stream: Read stream for receiving messages
        write_stream: Write stream for sending messages
        get_session_id_callback: Callback to retrieve current session ID
        client_context: The streamablehttp_client context manager (for cleanup)
    """

    session: ClientSession
    session_id: str | None
    tools: list[Tool]
    read_stream: MemoryObjectReceiveStream[SessionMessage | Exception]
    write_stream: MemoryObjectSendStream[SessionMessage]
    get_session_id_callback: Callable[[], str | None]
    client_context: AbstractAsyncContextManager[
        tuple[Any, Any, Callable[[], str | None]]
    ]

    async def close(self) -> None:
        """Close the HTTP MCP connection gracefully."""
        try:
            # First exit the ClientSession
            await self.session.__aexit__(None, None, None)
        except Exception as exc:
            logger.warning("Error closing ClientSession: %s", exc)

        try:
            # Then exit the streamablehttp_client context
            await self.client_context.__aexit__(None, None, None)
        except Exception as exc:
            logger.warning("Error closing HTTP client context: %s", exc)
