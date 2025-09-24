"""Wrapper that exposes MCP server functions as an Agno toolkit."""

from __future__ import annotations

from typing import Any

from agno.tools import Toolkit
from agno.tools.mcp import MCPTools

from src.core.logging import get_logger

logger = get_logger(__name__)


class MCPToolkit(Toolkit):
    """Expose MCP functions registered on a remote server."""

    def __init__(self, server_name: str, mcp_tools: MCPTools) -> None:
        super().__init__(name=f"mcp_{server_name}", add_instructions=True)
        self.server_name = server_name
        self._mcp_tools = mcp_tools
        self._load_functions()

    def _load_functions(self) -> None:
        try:
            functions = getattr(self._mcp_tools, "functions", {})
            if not functions:
                logger.debug(
                    "No MCP functions exposed by server '%s'",
                    self.server_name,
                )
                return

            for func_name, func in functions.items():
                self.functions[func_name] = func
                logger.debug(
                    "Registered MCP function %s.%s",
                    self.server_name,
                    func_name,
                )

            logger.info(
                "MCP toolkit '%s' loaded %s function(s)",
                self.name,
                len(self.functions),
            )

        except Exception as exc:  # pragma: no cover - defensive logging
            logger.error(
                "Error while loading MCP functions for server '%s': %s",
                self.server_name,
                exc,
            )

    def reload_functions(self) -> None:
        self.functions.clear()
        self._load_functions()

    def get_function_names(self) -> list[str]:
        return list(self.functions.keys())

    def get_server_info(self) -> dict[str, Any]:
        return {
            "server_name": self.server_name,
            "toolkit_name": self.name,
            "function_count": len(self.functions),
            "functions": self.get_function_names(),
        }

    def __repr__(self) -> str:  # pragma: no cover - debug helper
        return (
            f"MCPToolkit(server='{self.server_name}', functions={len(self.functions)})"
        )
