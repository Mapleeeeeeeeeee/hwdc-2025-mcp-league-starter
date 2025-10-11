"""Wrapper that exposes MCP server functions as an Agno toolkit."""

from __future__ import annotations

from collections.abc import Collection
from typing import Any

from agno.tools import Toolkit
from agno.tools.mcp import MCPTools

from src.core.logging import get_logger

logger = get_logger(__name__)


class MCPToolkit(Toolkit):
    """Expose MCP functions registered on a remote server."""

    def __init__(
        self,
        server_name: str,
        mcp_tools: MCPTools,
        *,
        allowed_functions: Collection[str] | None = None,
    ) -> None:
        super().__init__(name=f"mcp_{server_name}", add_instructions=True)
        self.server_name = server_name
        self._mcp_tools = mcp_tools
        self._allowed = (
            {name.strip() for name in allowed_functions} if allowed_functions else None
        )
        self._load_functions()

    def _load_functions(self) -> None:
        """Load functions from MCPTools instance into this toolkit."""
        functions = getattr(self._mcp_tools, "functions", {})
        if not functions:
            logger.debug(
                "No MCP functions exposed by server '%s'",
                self.server_name,
            )
            return

        for func_name, func in functions.items():
            if self._allowed is not None and func_name not in self._allowed:
                continue

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
