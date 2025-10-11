"""HTTP/SSE MCP toolkit wrapper for Agno."""

from __future__ import annotations

from collections.abc import Collection
from typing import Any

from agno.tools import Toolkit
from agno.tools.function import Function
from mcp import ClientSession
from mcp.types import CallToolResult, TextContent, Tool

from src.core.logging import get_logger
from src.shared.exceptions.mcp import MCPToolExecutionError

logger = get_logger(__name__)


class HTTPMCPToolkit(Toolkit):
    """
    Expose HTTP MCP server functions as an Agno toolkit.

    This toolkit wraps a persistent HTTP MCP ClientSession and provides
    access to the server's tools as callable functions.
    """

    def __init__(
        self,
        server_name: str,
        session: ClientSession,
        tools: list[Tool],
        *,
        allowed_functions: Collection[str] | None = None,
    ) -> None:
        """
        Initialize HTTP MCP toolkit.

        Args:
            server_name: Name of the MCP server
            session: Active MCP ClientSession
            tools: List of available tools from the server
            allowed_functions: Optional list of function names to expose
        """
        super().__init__(name=f"mcp_{server_name}", add_instructions=True)
        self.server_name = server_name
        self._session = session
        self._tools = tools
        self._allowed = (
            {name.strip() for name in allowed_functions} if allowed_functions else None
        )
        self._load_functions()

    def _load_functions(self) -> None:
        """Load and wrap MCP tools as callable functions."""
        if not self._tools:
            logger.debug(
                "No MCP tools exposed by HTTP server '%s'",
                self.server_name,
            )
            return

        for tool in self._tools:
            if self._allowed is not None and tool.name not in self._allowed:
                continue

            # Create a wrapper function for this tool
            self.functions[tool.name] = self._create_tool_wrapper(tool)
            logger.debug(
                "Registered HTTP MCP tool %s.%s",
                self.server_name,
                tool.name,
            )

        logger.info(
            "HTTP MCP toolkit '%s' loaded %s tool(s)",
            self.name,
            len(self.functions),
        )

    def _create_tool_wrapper(self, tool: Tool) -> Function:
        """
        Create a callable wrapper for an MCP tool.

        Args:
            tool: MCP Tool definition

        Returns:
            Agno Function that calls the tool via the session
        """

        async def tool_entrypoint(**kwargs: Any) -> str:
            """
            Call the MCP tool with the provided arguments.

            Args:
                **kwargs: Tool arguments

            Returns:
                Tool result as string
            """
            try:
                logger.debug(
                    "Calling HTTP MCP tool %s.%s with args: %s",
                    self.server_name,
                    tool.name,
                    kwargs,
                )

                # Call the tool via the session
                result: CallToolResult = await self._session.call_tool(
                    tool.name, arguments=kwargs
                )

                # Extract text content from result
                if result.content:
                    # Concatenate all text content
                    text_parts = []
                    for content in result.content:
                        if isinstance(content, TextContent):
                            text_parts.append(content.text)
                    return "\n".join(text_parts) if text_parts else str(result.content)

                # If no content, return structured content or empty
                if result.structuredContent:
                    return str(result.structuredContent)

                return "Tool executed successfully (no output)"

            except TimeoutError as exc:
                # Tool execution timeout
                error_msg = (
                    f"Tool '{tool.name}' on server '{self.server_name}' timed out"
                )
                logger.error(error_msg)
                raise MCPToolExecutionError(
                    server_name=self.server_name,
                    tool_name=tool.name,
                    reason="Execution timed out",
                ) from exc
            except Exception as exc:
                # Other tool execution errors
                error_msg = (
                    f"Tool '{tool.name}' on server '{self.server_name}' failed: {exc}"
                )
                logger.error(error_msg)
                raise MCPToolExecutionError(
                    server_name=self.server_name,
                    tool_name=tool.name,
                    reason=str(exc),
                ) from exc

        # Create Agno Function object with proper schema
        return Function(
            name=tool.name,
            description=tool.description or f"MCP tool: {tool.name}",
            parameters=tool.inputSchema if hasattr(tool, "inputSchema") else {},
            entrypoint=tool_entrypoint,
        )

    def reload_functions(self) -> None:
        """Reload functions from the current tools list."""
        self.functions.clear()
        self._load_functions()

    def get_function_names(self) -> list[str]:
        """Get list of available function names."""
        return list(self.functions.keys())

    def get_server_info(self) -> dict[str, Any]:
        """Get information about the server and toolkit."""
        return {
            "server_name": self.server_name,
            "toolkit_name": self.name,
            "function_count": len(self.functions),
            "functions": self.get_function_names(),
            "transport": "http",
        }

    def __repr__(self) -> str:
        return (
            f"HTTPMCPToolkit(server='{self.server_name}', "
            f"functions={len(self.functions)})"
        )
