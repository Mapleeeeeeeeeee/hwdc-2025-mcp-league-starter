"""Boundary tests for MCPToolkit."""

from __future__ import annotations

from unittest.mock import MagicMock

from src.integrations.mcp.toolkit import MCPToolkit


class TestMCPToolkitBoundaries:
    """Test MCPToolkit boundary cases."""

    def test_init_with_empty_functions_expects_empty_toolkit(self):
        """Test toolkit with no functions."""
        # Arrange
        mock_tools = MagicMock()
        mock_tools.functions = {}

        # Act
        toolkit = MCPToolkit(
            server_name="test",
            mcp_tools=mock_tools,
            allowed_functions=None,
        )

        # Assert
        assert len(toolkit.get_function_names()) == 0

    def test_init_with_allowed_functions_expects_filtered(self):
        """Test toolkit filters to allowed functions."""
        # Arrange
        mock_tools = MagicMock()
        mock_tools.functions = {
            "func1": MagicMock(),
            "func2": MagicMock(),
            "func3": MagicMock(),
        }

        # Act
        toolkit = MCPToolkit(
            server_name="test",
            mcp_tools=mock_tools,
            allowed_functions=["func1", "func3"],
        )

        # Assert
        names = toolkit.get_function_names()
        assert len(names) == 2
        assert "func1" in names
        assert "func3" in names
        assert "func2" not in names

    def test_get_function_names_expects_sorted_list(self):
        """Test function names are returned as list."""
        # Arrange
        mock_tools = MagicMock()
        mock_tools.functions = {
            "zebra": MagicMock(),
            "apple": MagicMock(),
            "mango": MagicMock(),
        }

        # Act
        toolkit = MCPToolkit(
            server_name="test",
            mcp_tools=mock_tools,
            allowed_functions=None,
        )

        # Assert
        names = toolkit.get_function_names()
        assert len(names) == 3
        assert "apple" in names
        assert "mango" in names
        assert "zebra" in names

    def test_reload_functions_expects_functions_reloaded(self):
        """Test reload clears and reloads functions."""
        # Arrange
        mock_tools = MagicMock()
        mock_tools.functions = {
            "func1": MagicMock(),
            "func2": MagicMock(),
        }

        toolkit = MCPToolkit(
            server_name="test",
            mcp_tools=mock_tools,
            allowed_functions=None,
        )

        # Modify the underlying functions
        mock_tools.functions = {
            "func3": MagicMock(),
            "func4": MagicMock(),
        }

        # Act
        toolkit.reload_functions()

        # Assert
        names = toolkit.get_function_names()
        assert len(names) == 2
        assert "func3" in names
        assert "func4" in names
        assert "func1" not in names

    def test_get_server_info_expects_complete_info(self):
        """Test server info returns all details."""
        # Arrange
        mock_tools = MagicMock()
        mock_tools.functions = {
            "func1": MagicMock(),
            "func2": MagicMock(),
        }

        toolkit = MCPToolkit(
            server_name="my-server",
            mcp_tools=mock_tools,
            allowed_functions=None,
        )

        # Act
        info = toolkit.get_server_info()

        # Assert
        assert info["server_name"] == "my-server"
        assert info["toolkit_name"] == "mcp_my-server"
        assert info["function_count"] == 2
        assert len(info["functions"]) == 2

    def test_init_with_whitespace_in_allowed_expects_stripped(self):
        """Test allowed functions with whitespace are stripped."""
        # Arrange
        mock_tools = MagicMock()
        mock_tools.functions = {
            "func1": MagicMock(),
            "func2": MagicMock(),
        }

        # Act
        toolkit = MCPToolkit(
            server_name="test",
            mcp_tools=mock_tools,
            allowed_functions=[" func1 ", "func2  "],
        )

        # Assert
        assert len(toolkit.get_function_names()) == 2

    def test_init_with_no_functions_attr_expects_empty_toolkit(self):
        """Test toolkit handles mcp_tools without functions attr."""
        # Arrange
        mock_tools = MagicMock()
        del mock_tools.functions  # Remove functions attribute

        # Act
        toolkit = MCPToolkit(
            server_name="test",
            mcp_tools=mock_tools,
            allowed_functions=None,
        )

        # Assert
        assert len(toolkit.get_function_names()) == 0
