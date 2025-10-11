"""Unit tests for MCPManager HTTP transport integration."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from mcp.types import Tool
from src.integrations.mcp.http_connection import HTTPMCPConnection
from src.integrations.mcp.http_toolkit import HTTPMCPToolkit
from src.integrations.mcp.manager import MCPManager
from src.integrations.mcp.server_params import (
    AuthType,
    HTTPAuthConfig,
    MCPParamsManager,
    MCPServerParams,
    TransportType,
)
from src.integrations.mcp.toolkit import MCPToolkit


class TestMCPManagerHTTPIntegration:
    """Test MCPManager HTTP transport integration."""

    @pytest.fixture
    def mock_params_manager(self):
        """Create mock MCPParamsManager."""
        manager = MagicMock(spec=MCPParamsManager)
        manager.validate_config = MagicMock(return_value=True)
        return manager

    @pytest.fixture
    def mcp_manager(self, mock_params_manager):
        """Create MCPManager instance."""
        MCPManager._instance = None
        MCPManager._class_initialised = False
        return MCPManager(params_manager=mock_params_manager)

    @pytest.fixture
    def http_config(self):
        """Create HTTP server configuration."""
        return MCPServerParams(
            name="http-test",
            transport=TransportType.HTTP,
            url="https://api.example.com/mcp",
            auth=HTTPAuthConfig(type=AuthType.BEARER, token="test-token"),
            timeout_seconds=60,
            enabled=True,
        )

    @pytest.fixture
    def stdio_config(self):
        """Create stdio server configuration."""
        return MCPServerParams(
            name="stdio-test",
            transport=TransportType.STDIO,
            command="node",
            args=["server.js"],
            env={},
            timeout_seconds=60,
            enabled=True,
        )

    @pytest.fixture
    def mock_http_conn(self):
        """Create mock HTTPMCPConnection."""
        conn = MagicMock(spec=HTTPMCPConnection)
        conn.session = MagicMock()
        conn.session_id = "test-session"
        conn.tools = [
            Tool(name="http_tool", description="Test", inputSchema={}),
        ]
        conn.close = AsyncMock()
        return conn

    @pytest.mark.asyncio
    async def test_init_http_expects_connection(
        self, mcp_manager, http_config, mock_http_conn
    ):
        """Test HTTP server initialization creates connection."""
        with patch(
            "src.integrations.mcp.manager.create_http_mcp_connection",
            return_value=mock_http_conn,
        ):
            await mcp_manager._initialise_single_server(http_config)
            assert "http-test" in mcp_manager._servers

    @pytest.mark.asyncio
    async def test_init_stdio_expects_tools(self, mcp_manager, stdio_config):
        """Test stdio server initialization creates MCPTools."""
        mock_tools = MagicMock()
        with patch(
            "src.integrations.mcp.manager.MCPTools",
            return_value=mock_tools,
        ):
            await mcp_manager._initialise_single_server(stdio_config)
            assert "stdio-test" in mcp_manager._servers

    def test_get_toolkit_http_expects_http_toolkit(self, mcp_manager, mock_http_conn):
        """Test HTTP server toolkit is HTTPMCPToolkit."""
        mcp_manager._initialized = True
        mcp_manager._servers["test"] = mock_http_conn
        toolkit = mcp_manager.get_toolkit_for_server("test")
        assert isinstance(toolkit, HTTPMCPToolkit)

    def test_get_toolkit_stdio_expects_mcp_toolkit(self, mcp_manager):
        """Test stdio server toolkit is MCPToolkit."""
        mock_tools = MagicMock()
        mock_tools.functions = {}
        mcp_manager._initialized = True
        mcp_manager._servers["test"] = mock_tools
        toolkit = mcp_manager.get_toolkit_for_server("test")
        assert isinstance(toolkit, MCPToolkit)

    def test_get_toolkit_nonexistent_expects_none(self, mcp_manager):
        """Test nonexistent server toolkit is None."""
        mcp_manager._initialized = True
        toolkit = mcp_manager.get_toolkit_for_server("nonexistent")
        assert toolkit is None

    def test_is_http_server_with_http_expects_true(self, mcp_manager, mock_http_conn):
        """Test HTTP connection is detected as HTTP server."""
        assert mcp_manager._is_http_server(mock_http_conn) is True

    def test_is_http_server_with_stdio_expects_false(self, mcp_manager):
        """Test stdio tools is not HTTP server."""
        assert mcp_manager._is_http_server(MagicMock()) is False
