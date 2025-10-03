"""Unit tests for ConversationUsecase._attach_requested_tools method."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from src.models.conversation import MCPToolSelection
from src.usecases.conversation import ConversationUsecase


class TestAttachRequestedTools:
    """Test ConversationUsecase._attach_requested_tools method."""

    @pytest.fixture
    def mock_agent_factory(self):
        """Create a mock conversation agent factory."""
        factory = MagicMock()
        return factory

    @pytest.fixture
    def conversation_usecase(self, mock_agent_factory):
        """Create ConversationUsecase instance with mocked factory."""
        return ConversationUsecase(agent_factory=mock_agent_factory)

    @pytest.fixture
    def mock_agent(self):
        """Create a mock agent."""
        agent = MagicMock()
        agent.add_tool = MagicMock()
        return agent

    def test_attach_requested_tools_with_none_expects_no_tools_added(
        self, conversation_usecase, mock_agent
    ):
        """Test that None selections result in no tools being attached."""
        # Arrange
        selections = None

        # Act
        conversation_usecase._attach_requested_tools(mock_agent, selections)

        # Assert
        mock_agent.add_tool.assert_not_called()

    def test_attach_requested_tools_with_empty_list_expects_no_tools_added(
        self, conversation_usecase, mock_agent
    ):
        """Test that empty selections list result in no tools being attached."""
        # Arrange
        selections = []

        # Act
        conversation_usecase._attach_requested_tools(mock_agent, selections)

        # Assert
        mock_agent.add_tool.assert_not_called()

    def test_attach_requested_tools_with_single_server_expects_toolkit_added(
        self, conversation_usecase, mock_agent
    ):
        """Test attaching a single server with all functions."""
        # Arrange
        selections = [
            MCPToolSelection(server="test-server", functions=None),
        ]

        mock_toolkit = MagicMock()
        mock_toolkit.functions = {"func1": MagicMock(), "func2": MagicMock()}

        with patch(
            "src.usecases.conversation.conversation_usecase.get_mcp_toolkit",
            return_value=mock_toolkit,
        ) as mock_get_toolkit:
            # Act
            conversation_usecase._attach_requested_tools(mock_agent, selections)

            # Assert
            mock_get_toolkit.assert_called_once_with(
                "test-server", allowed_functions=None
            )
            mock_agent.add_tool.assert_called_once_with(mock_toolkit)

    def test_attach_requested_tools_with_specific_functions_expects_filtered_toolkit(
        self, conversation_usecase, mock_agent
    ):
        """Test attaching a server with specific functions."""
        # Arrange
        selections = [
            MCPToolSelection(server="test-server", functions=["func1", "func2"]),
        ]

        mock_toolkit = MagicMock()
        mock_toolkit.functions = {"func1": MagicMock(), "func2": MagicMock()}

        with patch(
            "src.usecases.conversation.conversation_usecase.get_mcp_toolkit",
            return_value=mock_toolkit,
        ) as mock_get_toolkit:
            # Act
            conversation_usecase._attach_requested_tools(mock_agent, selections)

            # Assert
            mock_get_toolkit.assert_called_once_with(
                "test-server", allowed_functions=["func1", "func2"]
            )
            mock_agent.add_tool.assert_called_once()

    def test_attach_requested_tools_with_multiple_servers_expects_all_added(
        self, conversation_usecase, mock_agent
    ):
        """Test attaching multiple servers."""
        # Arrange
        selections = [
            MCPToolSelection(server="server1", functions=None),
            MCPToolSelection(server="server2", functions=["func_a"]),
            MCPToolSelection(server="server3", functions=["func_x", "func_y"]),
        ]

        mock_toolkit1 = MagicMock()
        mock_toolkit1.functions = {"f1": MagicMock(), "f2": MagicMock()}
        mock_toolkit2 = MagicMock()
        mock_toolkit2.functions = {"func_a": MagicMock()}
        mock_toolkit3 = MagicMock()
        mock_toolkit3.functions = {"func_x": MagicMock(), "func_y": MagicMock()}

        toolkits = [mock_toolkit1, mock_toolkit2, mock_toolkit3]

        with patch(
            "src.usecases.conversation.conversation_usecase.get_mcp_toolkit",
            side_effect=toolkits,
        ):
            # Act
            conversation_usecase._attach_requested_tools(mock_agent, selections)

            # Assert
            assert mock_agent.add_tool.call_count == 3
            mock_agent.add_tool.assert_any_call(mock_toolkit1)
            mock_agent.add_tool.assert_any_call(mock_toolkit2)
            mock_agent.add_tool.assert_any_call(mock_toolkit3)

    def test_attach_requested_tools_with_unavailable_toolkit_expects_skipped(
        self, conversation_usecase, mock_agent
    ):
        """Test that unavailable toolkits are skipped."""
        # Arrange
        selections = [
            MCPToolSelection(server="good-server", functions=None),
            MCPToolSelection(server="bad-server", functions=None),
        ]

        mock_good_toolkit = MagicMock()
        mock_good_toolkit.functions = {"func": MagicMock()}

        toolkits = [mock_good_toolkit, None]  # Second toolkit unavailable

        with patch(
            "src.usecases.conversation.conversation_usecase.get_mcp_toolkit",
            side_effect=toolkits,
        ):
            # Act
            conversation_usecase._attach_requested_tools(mock_agent, selections)

            # Assert
            # Only good toolkit should be added
            assert mock_agent.add_tool.call_count == 1
            mock_agent.add_tool.assert_called_once_with(mock_good_toolkit)

    def test_attach_requested_tools_with_empty_toolkit_expects_skipped(
        self, conversation_usecase, mock_agent
    ):
        """Test that toolkits with no functions are skipped."""
        # Arrange
        selections = [
            MCPToolSelection(server="empty-server", functions=None),
        ]

        mock_empty_toolkit = MagicMock()
        mock_empty_toolkit.functions = {}  # No functions

        with patch(
            "src.usecases.conversation.conversation_usecase.get_mcp_toolkit",
            return_value=mock_empty_toolkit,
        ):
            # Act
            conversation_usecase._attach_requested_tools(mock_agent, selections)

            # Assert
            mock_agent.add_tool.assert_not_called()

    def test_attach_requested_tools_with_duplicate_servers_expects_single_attachment(
        self, conversation_usecase, mock_agent
    ):
        """Test that duplicate server names are deduplicated."""
        # Arrange
        selections = [
            MCPToolSelection(server="test-server", functions=None),
            MCPToolSelection(server="test-server", functions=["func1"]),  # Duplicate
        ]

        mock_toolkit = MagicMock()
        mock_toolkit.functions = {"func": MagicMock()}

        with patch(
            "src.usecases.conversation.conversation_usecase.get_mcp_toolkit",
            return_value=mock_toolkit,
        ) as mock_get_toolkit:
            # Act
            conversation_usecase._attach_requested_tools(mock_agent, selections)

            # Assert
            # Should only be called once despite duplicate
            mock_get_toolkit.assert_called_once()
            mock_agent.add_tool.assert_called_once()

    def test_attach_requested_tools_with_whitespace_server_name_expects_trimmed(
        self, conversation_usecase, mock_agent
    ):
        """Test that server names with whitespace are trimmed."""
        # Arrange
        selections = [
            MCPToolSelection(server="  test-server  ", functions=None),
        ]

        mock_toolkit = MagicMock()
        mock_toolkit.functions = {"func": MagicMock()}

        with patch(
            "src.usecases.conversation.conversation_usecase.get_mcp_toolkit",
            return_value=mock_toolkit,
        ) as mock_get_toolkit:
            # Act
            conversation_usecase._attach_requested_tools(mock_agent, selections)

            # Assert
            mock_get_toolkit.assert_called_once_with(
                "test-server", allowed_functions=None
            )

    def test_attach_requested_tools_with_empty_server_name_expects_skipped(
        self, conversation_usecase, mock_agent
    ):
        """Test that empty server names are skipped."""
        # Arrange
        selections = [
            MCPToolSelection(server="", functions=None),
            MCPToolSelection(server="   ", functions=None),  # Whitespace only
            MCPToolSelection(server="valid-server", functions=None),
        ]

        mock_toolkit = MagicMock()
        mock_toolkit.functions = {"func": MagicMock()}

        with patch(
            "src.usecases.conversation.conversation_usecase.get_mcp_toolkit",
            return_value=mock_toolkit,
        ) as mock_get_toolkit:
            # Act
            conversation_usecase._attach_requested_tools(mock_agent, selections)

            # Assert
            # Only valid-server should be processed
            mock_get_toolkit.assert_called_once_with(
                "valid-server", allowed_functions=None
            )

    def test_attach_requested_tools_with_whitespace_function_names_expects_cleaned(
        self, conversation_usecase, mock_agent
    ):
        """Test that function names with whitespace are cleaned."""
        # Arrange
        selections = [
            MCPToolSelection(
                server="test-server",
                functions=["  func1  ", "func2", "   ", "func3"],  # Mixed whitespace
            ),
        ]

        mock_toolkit = MagicMock()
        mock_toolkit.functions = {"func1": MagicMock(), "func2": MagicMock()}

        with patch(
            "src.usecases.conversation.conversation_usecase.get_mcp_toolkit",
            return_value=mock_toolkit,
        ) as mock_get_toolkit:
            # Act
            conversation_usecase._attach_requested_tools(mock_agent, selections)

            # Assert
            # Empty strings should be filtered out
            call_args = mock_get_toolkit.call_args
            assert call_args is not None
            functions = call_args[1]["allowed_functions"]
            assert functions == ["func1", "func2", "func3"]

    def test_attach_requested_tools_with_all_empty_functions_expects_none(
        self, conversation_usecase, mock_agent
    ):
        """Test that if all functions are empty strings, None is passed."""
        # Arrange
        selections = [
            MCPToolSelection(
                server="test-server",
                functions=["", "   ", "  "],  # All empty
            ),
        ]

        mock_toolkit = MagicMock()
        mock_toolkit.functions = {"func": MagicMock()}

        with patch(
            "src.usecases.conversation.conversation_usecase.get_mcp_toolkit",
            return_value=mock_toolkit,
        ) as mock_get_toolkit:
            # Act
            conversation_usecase._attach_requested_tools(mock_agent, selections)

            # Assert
            # Should pass None when all functions are empty
            mock_get_toolkit.assert_called_once_with(
                "test-server", allowed_functions=None
            )
