"""Unit tests for HTTP MCP client connection."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest
from mcp.types import Tool
from src.integrations.mcp.http_client import create_http_mcp_connection
from src.integrations.mcp.http_connection import HTTPMCPConnection
from src.integrations.mcp.server_params import (
    AuthType,
    HTTPAuthConfig,
    MCPServerParams,
    TransportType,
)
from src.shared.exceptions.mcp import (
    MCPConnectionError,
    MCPConnectionTimeoutError,
    MCPInvalidConfigError,
)


class TestCreateHTTPMCPConnection:
    """Test create_http_mcp_connection function."""

    @pytest.fixture
    def mock_http_context(self):
        """Create mock context for streamablehttp_client."""
        context = MagicMock()
        context.__aenter__ = AsyncMock()
        context.__aexit__ = AsyncMock()

        # Mock streams and session_id callback
        read_stream = MagicMock()
        write_stream = MagicMock()
        get_session_id = MagicMock(return_value="test-session-123")

        context.__aenter__.return_value = (read_stream, write_stream, get_session_id)
        return context, read_stream, write_stream, get_session_id

    @pytest.fixture
    def mock_client_session(self):
        """Create mock ClientSession."""
        session = MagicMock()
        session.__aenter__ = AsyncMock(return_value=session)
        session.__aexit__ = AsyncMock()
        session.initialize = AsyncMock()

        # Mock tools list result
        tools_result = MagicMock()
        tools_result.tools = [
            Tool(name="test_tool", description="Test tool", inputSchema={}),
        ]
        session.list_tools = AsyncMock(return_value=tools_result)

        return session

    @pytest.mark.asyncio
    async def test_create_http_mcp_connection_with_valid_params_expects_connection(
        self, mock_http_context, mock_client_session
    ):
        """Test creating HTTP MCP connection with valid parameters."""
        # Arrange
        context, read_stream, write_stream, get_session_id = mock_http_context
        params = MCPServerParams(
            name="test-http-server",
            transport=TransportType.HTTP,
            url="https://api.example.com/mcp",
            timeout_seconds=60,
        )

        with (
            patch(
                "src.integrations.mcp.http_client.streamablehttp_client",
                return_value=context,
            ),
            patch(
                "src.integrations.mcp.http_client.ClientSession",
                return_value=mock_client_session,
            ),
        ):
            # Act
            connection = await create_http_mcp_connection(params)

            # Assert
            assert isinstance(connection, HTTPMCPConnection)
            assert connection.session == mock_client_session
            assert connection.session_id == "test-session-123"
            assert len(connection.tools) == 1
            assert connection.tools[0].name == "test_tool"
            mock_client_session.initialize.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_http_mcp_connection_with_bearer_auth_expects_auth_header(
        self, mock_http_context, mock_client_session
    ):
        """Test creating connection with bearer authentication includes auth header."""
        # Arrange
        context, _, _, _ = mock_http_context
        auth = HTTPAuthConfig(type=AuthType.BEARER, token="secret-token")
        params = MCPServerParams(
            name="secure-server",
            transport=TransportType.HTTP,
            url="https://api.example.com/mcp",
            auth=auth,
        )

        with (
            patch(
                "src.integrations.mcp.http_client.streamablehttp_client",
                return_value=context,
            ) as mock_streamable,
            patch(
                "src.integrations.mcp.http_client.ClientSession",
                return_value=mock_client_session,
            ),
        ):
            # Act
            await create_http_mcp_connection(params)

            # Assert
            # Verify that streamablehttp_client was called with auth headers
            call_kwargs = mock_streamable.call_args.kwargs
            assert "headers" in call_kwargs
            assert call_kwargs["headers"]["Authorization"] == "Bearer secret-token"

    @pytest.mark.asyncio
    async def test_create_http_mcp_connection_with_no_auth_expects_no_headers(
        self, mock_http_context, mock_client_session
    ):
        """Test creating connection without authentication."""
        # Arrange
        context, _, _, _ = mock_http_context
        params = MCPServerParams(
            name="public-server",
            transport=TransportType.HTTP,
            url="https://api.example.com/mcp",
            auth=None,
        )

        with (
            patch(
                "src.integrations.mcp.http_client.streamablehttp_client",
                return_value=context,
            ) as mock_streamable,
            patch(
                "src.integrations.mcp.http_client.ClientSession",
                return_value=mock_client_session,
            ),
        ):
            # Act
            await create_http_mcp_connection(params)

            # Assert
            call_kwargs = mock_streamable.call_args.kwargs
            assert call_kwargs.get("headers") is None

    @pytest.mark.asyncio
    async def test_create_connection_with_missing_url_expects_invalid_config_error(
        self,
    ):
        """Test creating connection without URL raises MCPInvalidConfigError."""
        # Arrange
        params = MCPServerParams(
            name="invalid-server",
            transport=TransportType.HTTP,
            url=None,  # Missing URL
        )

        # Act & Assert
        with pytest.raises(MCPInvalidConfigError) as exc_info:
            await create_http_mcp_connection(params)

        assert "invalid-server" in str(exc_info.value)
        assert "URL" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_create_http_mcp_connection_with_timeout_expects_timeout_error(
        self, mock_http_context
    ):
        """Test connection timeout raises MCPConnectionTimeoutError."""
        # Arrange
        context, _, _, _ = mock_http_context
        params = MCPServerParams(
            name="timeout-server",
            transport=TransportType.HTTP,
            url="https://api.example.com/mcp",
            timeout_seconds=5,
        )

        with (
            patch(
                "src.integrations.mcp.http_client.streamablehttp_client",
                return_value=context,
            ),
            patch(
                "src.integrations.mcp.http_client.ClientSession"
            ) as mock_session_class,
        ):
            # Mock session initialization to timeout
            mock_session = AsyncMock()
            mock_session.initialize = AsyncMock(side_effect=TimeoutError("Timed out"))
            mock_session.__aenter__ = AsyncMock(return_value=mock_session)
            mock_session_class.return_value = mock_session

            # Act & Assert
            with pytest.raises(MCPConnectionTimeoutError) as exc_info:
                await create_http_mcp_connection(params)

            assert "timeout-server" in str(exc_info.value)
            assert exc_info.value.context["timeout_seconds"] == 5

    @pytest.mark.asyncio
    async def test_create_http_mcp_connection_with_http_error_expects_connection_error(
        self, mock_http_context
    ):
        """Test HTTP error raises MCPConnectionError."""
        # Arrange
        context, _, _, _ = mock_http_context
        params = MCPServerParams(
            name="error-server",
            transport=TransportType.HTTP,
            url="https://api.example.com/mcp",
        )

        with (
            patch(
                "src.integrations.mcp.http_client.streamablehttp_client",
                return_value=context,
            ),
            patch(
                "src.integrations.mcp.http_client.ClientSession"
            ) as mock_session_class,
        ):
            # Mock session to raise HTTP error
            mock_session = AsyncMock()
            mock_session.initialize = AsyncMock(
                side_effect=httpx.HTTPError("Connection failed")
            )
            mock_session.__aenter__ = AsyncMock(return_value=mock_session)
            mock_session_class.return_value = mock_session

            # Act & Assert
            with pytest.raises(MCPConnectionError) as exc_info:
                await create_http_mcp_connection(params)

            assert "error-server" in str(exc_info.value)
            assert "http" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_create_connection_with_value_error_expects_invalid_config(
        self, mock_http_context
    ):
        """Test ValueError during connection raises MCPInvalidConfigError."""
        # Arrange
        context, _, _, _ = mock_http_context
        params = MCPServerParams(
            name="invalid-params-server",
            transport=TransportType.HTTP,
            url="https://api.example.com/mcp",
        )

        with (
            patch(
                "src.integrations.mcp.http_client.streamablehttp_client",
                return_value=context,
            ),
            patch(
                "src.integrations.mcp.http_client.ClientSession"
            ) as mock_session_class,
        ):
            # Mock session to raise ValueError
            mock_session = AsyncMock()
            mock_session.initialize = AsyncMock(
                side_effect=ValueError("Invalid configuration")
            )
            mock_session.__aenter__ = AsyncMock(return_value=mock_session)
            mock_session_class.return_value = mock_session

            # Act & Assert
            with pytest.raises(MCPInvalidConfigError) as exc_info:
                await create_http_mcp_connection(params)

            assert "invalid-params-server" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_create_connection_with_unexpected_error_expects_error(
        self, mock_http_context
    ):
        """Test unexpected error raises MCPConnectionError."""
        # Arrange
        context, _, _, _ = mock_http_context
        params = MCPServerParams(
            name="unexpected-error-server",
            transport=TransportType.HTTP,
            url="https://api.example.com/mcp",
        )

        with (
            patch(
                "src.integrations.mcp.http_client.streamablehttp_client",
                return_value=context,
            ),
            patch(
                "src.integrations.mcp.http_client.ClientSession"
            ) as mock_session_class,
        ):
            # Mock session to raise unexpected error
            mock_session = AsyncMock()
            mock_session.initialize = AsyncMock(
                side_effect=RuntimeError("Unexpected error")
            )
            mock_session.__aenter__ = AsyncMock(return_value=mock_session)
            mock_session_class.return_value = mock_session

            # Act & Assert
            with pytest.raises(MCPConnectionError) as exc_info:
                await create_http_mcp_connection(params)

            assert "unexpected-error-server" in str(exc_info.value)
            assert "Unexpected error" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_create_http_mcp_connection_with_custom_timeout_expects_timeout_used(
        self, mock_http_context, mock_client_session
    ):
        """Test that custom timeout is passed to the HTTP client."""
        # Arrange
        context, _, _, _ = mock_http_context
        params = MCPServerParams(
            name="custom-timeout-server",
            transport=TransportType.HTTP,
            url="https://api.example.com/mcp",
            timeout_seconds=120,
        )

        with (
            patch(
                "src.integrations.mcp.http_client.streamablehttp_client",
                return_value=context,
            ) as mock_streamable,
            patch(
                "src.integrations.mcp.http_client.ClientSession",
                return_value=mock_client_session,
            ),
        ):
            # Act
            await create_http_mcp_connection(params)

            # Assert
            call_kwargs = mock_streamable.call_args.kwargs
            assert call_kwargs["timeout"] == 120

    @pytest.mark.asyncio
    async def test_create_http_mcp_connection_with_no_tools_expects_empty_tools_list(
        self, mock_http_context
    ):
        """Test connection with server that has no tools."""
        # Arrange
        context, read_stream, write_stream, get_session_id = mock_http_context
        params = MCPServerParams(
            name="no-tools-server",
            transport=TransportType.HTTP,
            url="https://api.example.com/mcp",
        )

        # Mock session with no tools
        mock_session = MagicMock()
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock()
        mock_session.initialize = AsyncMock()
        tools_result = MagicMock()
        tools_result.tools = None  # No tools
        mock_session.list_tools = AsyncMock(return_value=tools_result)

        with (
            patch(
                "src.integrations.mcp.http_client.streamablehttp_client",
                return_value=context,
            ),
            patch(
                "src.integrations.mcp.http_client.ClientSession",
                return_value=mock_session,
            ),
        ):
            # Act
            connection = await create_http_mcp_connection(params)

            # Assert
            assert connection.tools == []

    @pytest.mark.asyncio
    async def test_create_connection_with_auth_error_expects_no_auth_header(
        self, mock_http_context, mock_client_session
    ):
        """Test that auth header build errors are logged but connection proceeds."""
        # Arrange
        context, _, _, _ = mock_http_context
        # Create mock auth that will fail to build header
        mock_auth = MagicMock()
        mock_auth.build_header = MagicMock(
            side_effect=ValueError("Failed to build header")
        )

        params = MCPServerParams(
            name="auth-error-server",
            transport=TransportType.HTTP,
            url="https://api.example.com/mcp",
        )
        params.auth = mock_auth

        with (
            patch(
                "src.integrations.mcp.http_client.streamablehttp_client",
                return_value=context,
            ) as mock_streamable,
            patch(
                "src.integrations.mcp.http_client.ClientSession",
                return_value=mock_client_session,
            ),
        ):
            # Act
            connection = await create_http_mcp_connection(params)

            # Assert
            # Connection should succeed without auth header
            assert isinstance(connection, HTTPMCPConnection)
            call_kwargs = mock_streamable.call_args.kwargs
            # No headers should be passed when auth fails
            assert call_kwargs.get("headers") is None
