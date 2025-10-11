"""HTTP/SSE MCP connection management."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from mcp import ClientSession
from mcp.types import Tool


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
    """

    session: ClientSession
    session_id: str | None
    tools: list[Tool]
    read_stream: Any  # MemoryObjectReceiveStream[SessionMessage | Exception]
    write_stream: Any  # MemoryObjectSendStream[SessionMessage]
    get_session_id_callback: Any  # Callable[[], str | None]

    async def close(self) -> None:
        """Close the HTTP MCP connection gracefully."""
        try:
            await self.session.__aexit__(None, None, None)
        except Exception:
            # Ignore errors during cleanup
            pass
