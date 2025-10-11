"""Unit tests for HTTPMCPConnection and HTTPMCPToolkit."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest
from mcp.types import CallToolResult, TextContent, Tool
from src.integrations.mcp.http_connection import HTTPMCPConnection
from src.integrations.mcp.http_toolkit import HTTPMCPToolkit
from src.shared.exceptions.mcp import MCPToolExecutionError


class TestHTTPMCPConnection:
    """Test HTTPMCPConnection close functionality."""

    @pytest.mark.asyncio
    async def test_close_with_valid_connection_expects_clean_exit(self):
        """Test closing connection exits both session and client context."""
        # Arrange
        mock_session = MagicMock()
        mock_session.__aexit__ = AsyncMock()

        mock_client_context = MagicMock()
        mock_client_context.__aexit__ = AsyncMock()

        connection = HTTPMCPConnection(
            session=mock_session,
            session_id="test-session-123",
            tools=[],
            read_stream=MagicMock(),
            write_stream=MagicMock(),
            get_session_id_callback=MagicMock(),
            client_context=mock_client_context,
        )

        # Act
        await connection.close()

        # Assert
        mock_session.__aexit__.assert_called_once_with(None, None, None)
        mock_client_context.__aexit__.assert_called_once_with(None, None, None)

    @pytest.mark.asyncio
    async def test_close_with_session_error_expects_context_still_closed(self):
        """Test that client context is closed even if session close fails."""
        # Arrange
        mock_session = MagicMock()
        mock_session.__aexit__ = AsyncMock(
            side_effect=Exception("Session close failed")
        )

        mock_client_context = MagicMock()
        mock_client_context.__aexit__ = AsyncMock()

        connection = HTTPMCPConnection(
            session=mock_session,
            session_id="test-session-456",
            tools=[],
            read_stream=MagicMock(),
            write_stream=MagicMock(),
            get_session_id_callback=MagicMock(),
            client_context=mock_client_context,
        )

        # Act
        await connection.close()

        # Assert
        mock_session.__aexit__.assert_called_once()
        mock_client_context.__aexit__.assert_called_once()  # Still called

    @pytest.mark.asyncio
    async def test_close_with_context_error_expects_no_exception_raised(self):
        """Test that context close errors are logged but not raised."""
        # Arrange
        mock_session = MagicMock()
        mock_session.__aexit__ = AsyncMock()

        mock_client_context = MagicMock()
        mock_client_context.__aexit__ = AsyncMock(
            side_effect=Exception("Context close failed")
        )

        connection = HTTPMCPConnection(
            session=mock_session,
            session_id="test-session-789",
            tools=[],
            read_stream=MagicMock(),
            write_stream=MagicMock(),
            get_session_id_callback=MagicMock(),
            client_context=mock_client_context,
        )

        # Act - should not raise exception
        await connection.close()

        # Assert
        mock_session.__aexit__.assert_called_once()
        mock_client_context.__aexit__.assert_called_once()


class TestHTTPMCPToolkit:
    """Test HTTPMCPToolkit functionality."""

    @pytest.fixture
    def mock_session(self):
        """Create mock ClientSession."""
        session = MagicMock()
        session.call_tool = AsyncMock()
        return session

    @pytest.fixture
    def sample_tools(self):
        """Create sample MCP tools."""
        return [
            Tool(
                name="get_weather",
                description="Get weather information",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "city": {"type": "string"},
                    },
                    "required": ["city"],
                },
            ),
            Tool(
                name="get_time",
                description="Get current time",
                inputSchema={"type": "object", "properties": {}},
            ),
        ]

    def test_init_with_tools_expects_functions_loaded(self, mock_session, sample_tools):
        """Test initializing toolkit loads all tools as functions."""
        # Act
        toolkit = HTTPMCPToolkit(
            server_name="test-server",
            session=mock_session,
            tools=sample_tools,
        )

        # Assert
        assert len(toolkit.functions) == 2
        assert "get_weather" in toolkit.functions
        assert "get_time" in toolkit.functions
        assert toolkit.name == "mcp_test-server"

    def test_init_with_allowed_functions_expects_filtered_functions(
        self, mock_session, sample_tools
    ):
        """Test initializing toolkit with allowed_functions filters tools."""
        # Act
        toolkit = HTTPMCPToolkit(
            server_name="filtered-server",
            session=mock_session,
            tools=sample_tools,
            allowed_functions=["get_weather"],
        )

        # Assert
        assert len(toolkit.functions) == 1
        assert "get_weather" in toolkit.functions
        assert "get_time" not in toolkit.functions

    def test_init_with_no_tools_expects_empty_functions(self, mock_session):
        """Test initializing toolkit with no tools."""
        # Act
        toolkit = HTTPMCPToolkit(
            server_name="empty-server",
            session=mock_session,
            tools=[],
        )

        # Assert
        assert len(toolkit.functions) == 0

    @pytest.mark.asyncio
    async def test_call_tool_with_valid_args_expects_text_result(
        self, mock_session, sample_tools
    ):
        """Test calling a tool returns text content."""
        # Arrange
        toolkit = HTTPMCPToolkit(
            server_name="test-server",
            session=mock_session,
            tools=sample_tools,
        )

        # Mock tool result
        result = CallToolResult(
            content=[
                TextContent(type="text", text="Temperature: 72°F"),
            ]
        )
        mock_session.call_tool = AsyncMock(return_value=result)

        # Act
        weather_func = toolkit.functions["get_weather"]
        output = await weather_func.entrypoint(city="San Francisco")  # type: ignore

        # Assert
        assert output == "Temperature: 72°F"
        mock_session.call_tool.assert_called_once_with(
            "get_weather",
            arguments={"city": "San Francisco"},
        )

    @pytest.mark.asyncio
    async def test_call_tool_with_multiple_text_content_expects_joined_result(
        self, mock_session, sample_tools
    ):
        """Test calling a tool with multiple text contents joins them."""
        # Arrange
        toolkit = HTTPMCPToolkit(
            server_name="test-server",
            session=mock_session,
            tools=sample_tools,
        )

        # Mock tool result with multiple text parts
        result = CallToolResult(
            content=[
                TextContent(type="text", text="Part 1"),
                TextContent(type="text", text="Part 2"),
            ]
        )
        mock_session.call_tool = AsyncMock(return_value=result)

        # Act
        weather_func = toolkit.functions["get_weather"]
        output = await weather_func.entrypoint(city="New York")  # type: ignore

        # Assert
        assert output == "Part 1\nPart 2"

    @pytest.mark.asyncio
    async def test_call_tool_with_no_content_expects_success_message(
        self, mock_session, sample_tools
    ):
        """Test calling a tool with no content returns success message."""
        # Arrange
        toolkit = HTTPMCPToolkit(
            server_name="test-server",
            session=mock_session,
            tools=sample_tools,
        )

        # Mock tool result with no content
        result = CallToolResult(content=[])
        mock_session.call_tool = AsyncMock(return_value=result)

        # Act
        time_func = toolkit.functions["get_time"]
        output = await time_func.entrypoint()  # type: ignore

        # Assert
        assert output == "Tool executed successfully (no output)"

    @pytest.mark.asyncio
    async def test_call_tool_with_timeout_expects_tool_execution_error(
        self, mock_session, sample_tools
    ):
        """Test tool execution timeout raises MCPToolExecutionError."""
        # Arrange
        toolkit = HTTPMCPToolkit(
            server_name="timeout-server",
            session=mock_session,
            tools=sample_tools,
        )

        # Mock timeout
        mock_session.call_tool = AsyncMock(side_effect=TimeoutError("Timed out"))

        # Act & Assert
        weather_func = toolkit.functions["get_weather"]
        with pytest.raises(MCPToolExecutionError) as exc_info:
            await weather_func.entrypoint(city="Boston")  # type: ignore

        assert "timeout-server" in str(exc_info.value)
        assert "get_weather" in str(exc_info.value)
        assert "timed out" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_call_tool_with_execution_error_expects_tool_execution_error(
        self, mock_session, sample_tools
    ):
        """Test tool execution error raises MCPToolExecutionError."""
        # Arrange
        toolkit = HTTPMCPToolkit(
            server_name="error-server",
            session=mock_session,
            tools=sample_tools,
        )

        # Mock execution error
        mock_session.call_tool = AsyncMock(
            side_effect=Exception("Tool execution failed")
        )

        # Act & Assert
        weather_func = toolkit.functions["get_weather"]
        with pytest.raises(MCPToolExecutionError) as exc_info:
            await weather_func.entrypoint(city="Chicago")  # type: ignore

        assert "error-server" in str(exc_info.value)
        assert "get_weather" in str(exc_info.value)

    def test_reload_functions_expects_functions_reloaded(self, mock_session):
        """Test reloading functions clears and reloads."""
        # Arrange
        initial_tools = [
            Tool(name="tool1", description="Tool 1", inputSchema={}),
        ]
        toolkit = HTTPMCPToolkit(
            server_name="reload-server",
            session=mock_session,
            tools=initial_tools,
        )

        # Modify tools list
        toolkit._tools = [
            Tool(name="tool2", description="Tool 2", inputSchema={}),
        ]

        # Act
        toolkit.reload_functions()

        # Assert
        assert len(toolkit.functions) == 1
        assert "tool2" in toolkit.functions
        assert "tool1" not in toolkit.functions

    def test_get_function_names_expects_list_of_names(self, mock_session, sample_tools):
        """Test getting function names returns list."""
        # Arrange
        toolkit = HTTPMCPToolkit(
            server_name="test-server",
            session=mock_session,
            tools=sample_tools,
        )

        # Act
        names = toolkit.get_function_names()

        # Assert
        assert set(names) == {"get_weather", "get_time"}

    def test_get_server_info_expects_complete_info(self, mock_session, sample_tools):
        """Test getting server info returns complete metadata."""
        # Arrange
        toolkit = HTTPMCPToolkit(
            server_name="info-server",
            session=mock_session,
            tools=sample_tools,
        )

        # Act
        info = toolkit.get_server_info()

        # Assert
        assert info["server_name"] == "info-server"
        assert info["toolkit_name"] == "mcp_info-server"
        assert info["function_count"] == 2
        assert info["transport"] == "http"
        assert set(info["functions"]) == {"get_weather", "get_time"}

    def test_repr_expects_readable_string(self, mock_session, sample_tools):
        """Test __repr__ returns readable representation."""
        # Arrange
        toolkit = HTTPMCPToolkit(
            server_name="repr-server",
            session=mock_session,
            tools=sample_tools,
        )

        # Act
        repr_str = repr(toolkit)

        # Assert
        assert "HTTPMCPToolkit" in repr_str
        assert "repr-server" in repr_str
        assert "functions=2" in repr_str

    @pytest.mark.asyncio
    async def test_call_tool_with_structured_content_expects_string_conversion(
        self, mock_session, sample_tools
    ):
        """Test calling tool with structured content converts to string."""
        # Arrange
        toolkit = HTTPMCPToolkit(
            server_name="structured-server",
            session=mock_session,
            tools=sample_tools,
        )

        # Mock tool result with structured content
        result = CallToolResult(
            content=[],
            structuredContent={"temperature": 72, "unit": "F"},
        )
        mock_session.call_tool = AsyncMock(return_value=result)

        # Act
        weather_func = toolkit.functions["get_weather"]
        output = await weather_func.entrypoint(city="Miami")  # type: ignore

        # Assert
        assert "temperature" in output
        assert "72" in output
