"""Boundary tests for server_params.py."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from src.integrations.mcp.server_params import (
    MCPParamsManager,
    MCPServerParams,
    MCPSettings,
    TransportType,
)


class TestMCPServerParamsSTDIOBoundaries:
    """Test STDIO transport boundary cases."""

    def test_get_full_command_with_args_expects_joined_string(self):
        """Test command with args returns joined string."""
        # Arrange
        params = MCPServerParams(
            name="test",
            transport=TransportType.STDIO,
            command="node",
            args=["server.js", "--port", "3000"],
            enabled=True,
        )

        # Act
        full_command = params.get_full_command()

        # Assert
        assert full_command == "node server.js --port 3000"

    def test_get_full_command_with_no_args_expects_command_only(self):
        """Test command without args returns command only."""
        # Arrange
        params = MCPServerParams(
            name="test",
            transport=TransportType.STDIO,
            command="npx some-tool",
            args=None,
            enabled=True,
        )

        # Act
        full_command = params.get_full_command()

        # Assert
        assert full_command == "npx some-tool"

    def test_get_command_list_with_args_expects_list(self):
        """Test command list with args returns list."""
        # Arrange
        params = MCPServerParams(
            name="test",
            transport=TransportType.STDIO,
            command="python",
            args=["-m", "server"],
            enabled=True,
        )

        # Act
        cmd_list = params.get_command_list()

        # Assert
        assert cmd_list == ["python", "-m", "server"]

    def test_get_command_list_with_no_args_expects_split(self):
        """Test command with no args splits on space."""
        # Arrange
        params = MCPServerParams(
            name="test",
            transport=TransportType.STDIO,
            command="npx -y @modelcontextprotocol/server-everything",
            args=None,
            enabled=True,
        )

        # Act
        cmd_list = params.get_command_list()

        # Assert
        assert len(cmd_list) == 3
        assert cmd_list[0] == "npx"
        assert cmd_list[1] == "-y"


class TestMCPParamsManagerLoadBoundaries:
    """Test config loading boundary cases."""

    @pytest.fixture
    def mock_settings(self):
        """Create mock settings."""
        settings = MagicMock(spec=MCPSettings)
        settings.enable_mcp_system = True
        return settings

    def test_get_default_params_with_disabled_system_expects_empty(self, mock_settings):
        """Test disabled system returns empty list."""
        # Arrange
        mock_settings.enable_mcp_system = False
        manager = MCPParamsManager(settings=mock_settings)

        # Act
        params = manager.get_default_params()

        # Assert
        assert params == []


class TestMCPParamsManagerValidation:
    """Test configuration validation boundaries."""

    def test_validate_stdio_with_no_command_expects_false(self):
        """Test STDIO without command is invalid."""
        # Arrange
        manager = MCPParamsManager()
        config = MCPServerParams(
            name="test",
            transport=TransportType.STDIO,
            command=None,
            enabled=True,
        )

        # Act
        is_valid = manager.validate_config(config)

        # Assert
        assert is_valid is False

    def test_validate_stdio_with_empty_command_expects_false(self):
        """Test STDIO with empty command is invalid."""
        # Arrange
        manager = MCPParamsManager()
        config = MCPServerParams(
            name="test",
            transport=TransportType.STDIO,
            command="",
            enabled=True,
        )

        # Act
        is_valid = manager.validate_config(config)

        # Assert
        assert is_valid is False

    def test_validate_stdio_with_command_expects_true(self):
        """Test STDIO with command is valid."""
        # Arrange
        manager = MCPParamsManager()
        config = MCPServerParams(
            name="test",
            transport=TransportType.STDIO,
            command="node",
            args=["server.js"],
            enabled=True,
        )

        # Act
        is_valid = manager.validate_config(config)

        # Assert
        assert is_valid is True


class TestMCPServerParamsEnvironmentVariables:
    """Test environment variable handling boundaries."""

    def test_create_with_env_expects_env_stored(self):
        """Test environment variables are stored."""
        # Arrange & Act
        params = MCPServerParams(
            name="test",
            transport=TransportType.STDIO,
            command="node",
            env={"NODE_ENV": "production", "API_KEY": "secret"},
            enabled=True,
        )

        # Assert
        assert params.env is not None
        assert params.env["NODE_ENV"] == "production"
        assert params.env["API_KEY"] == "secret"

    def test_create_with_empty_env_expects_empty_dict(self):
        """Test empty environment dict is preserved."""
        # Arrange & Act
        params = MCPServerParams(
            name="test",
            transport=TransportType.STDIO,
            command="node",
            env={},
            enabled=True,
        )

        # Assert
        assert params.env == {}

    def test_create_with_no_env_expects_none(self):
        """Test no environment dict is None."""
        # Arrange & Act
        params = MCPServerParams(
            name="test",
            transport=TransportType.STDIO,
            command="node",
            enabled=True,
        )

        # Assert
        assert params.env is None


class TestMCPParamsManagerConfigParsing:
    """Test config parsing edge cases."""

    def test_create_params_with_stdio_expects_params(self):
        """Test creating stdio params from dict."""
        # Arrange
        manager = MCPParamsManager()
        config_dict = {
            "name": "test-server",
            "command": "node",
            "args": ["server.js"],
        }

        # Act
        params = manager._create_params_from_dict(config_dict)

        # Assert
        assert params is not None
        assert params.name == "test-server"
        assert params.command == "node"
        assert params.transport == TransportType.STDIO

    def test_create_params_with_env_expects_env_stored(self):
        """Test environment variables are parsed."""
        # Arrange
        manager = MCPParamsManager()
        config_dict = {
            "name": "test-server",
            "command": "node",
            "env": {
                "NODE_ENV": "production",
                "API_KEY": "secret123",
            },
        }

        # Act
        params = manager._create_params_from_dict(config_dict)

        # Assert
        assert params is not None
        assert params.env is not None
        assert params.env["NODE_ENV"] == "production"
        assert params.env["API_KEY"] == "secret123"

    def test_create_params_with_disabled_expects_disabled(self):
        """Test disabled flag is respected."""
        # Arrange
        manager = MCPParamsManager()
        config_dict = {
            "name": "test-server",
            "command": "node",
            "enabled": False,
        }

        # Act
        params = manager._create_params_from_dict(config_dict)

        # Assert
        assert params is not None
        assert params.enabled is False

    def test_create_params_with_enabled_true_expects_enabled(self):
        """Test enabled flag is respected."""
        # Arrange
        manager = MCPParamsManager()
        config_dict = {
            "name": "test-server",
            "command": "node",
            "enabled": True,
        }

        # Act
        params = manager._create_params_from_dict(config_dict)

        # Assert
        assert params is not None
        assert params.enabled is True

    def test_create_params_with_timeout_expects_timeout_set(self):
        """Test timeout is parsed."""
        # Arrange
        manager = MCPParamsManager()
        config_dict = {
            "name": "test-server",
            "command": "node",
            "timeout_seconds": 120,
        }

        # Act
        params = manager._create_params_from_dict(config_dict)

        # Assert
        assert params is not None
        assert params.timeout_seconds == 120

    def test_create_params_with_description_expects_description_set(self):
        """Test description is parsed."""
        # Arrange
        manager = MCPParamsManager()
        config_dict = {
            "name": "test-server",
            "command": "node",
            "description": "Test MCP server",
        }

        # Act
        params = manager._create_params_from_dict(config_dict)

        # Assert
        assert params is not None
        assert params.description == "Test MCP server"

    def test_create_params_with_missing_name_expects_none(self):
        """Test missing name returns None."""
        # Arrange
        manager = MCPParamsManager()
        config_dict = {
            "command": "node",
        }

        # Act
        params = manager._create_params_from_dict(config_dict)

        # Assert
        assert params is None

    def test_create_params_with_http_but_no_url_expects_none(self):
        """Test HTTP without URL returns None."""
        # Arrange
        manager = MCPParamsManager()
        config_dict = {
            "name": "test-server",
            "type": "http",
        }

        # Act
        params = manager._create_params_from_dict(config_dict)

        # Assert
        assert params is None

    def test_create_params_with_stdio_but_no_command_expects_none(self):
        """Test stdio without command returns None."""
        # Arrange
        manager = MCPParamsManager()
        config_dict = {
            "name": "test-server",
        }

        # Act
        params = manager._create_params_from_dict(config_dict)

        # Assert
        assert params is None


class TestMCPParamsManagerConfigLoading:
    """Test config file loading edge cases."""

    def test_load_with_non_dict_server_entry_expects_skipped(self):
        """Test non-dict server entries are skipped."""
        # Arrange
        manager = MCPParamsManager()

        # Mock the payload loading to return invalid entry
        invalid_payload = {
            "mcpServers": {
                "valid-server": {
                    "command": "node",
                },
                "invalid-server": "not a dict",
            }
        }

        with patch.object(
            manager, "_load_servers_payload", return_value=invalid_payload
        ):
            # Act
            params = manager._load_configured_params()

            # Assert
            assert len(params) == 1
            assert params[0].name == "valid-server"

    def test_load_with_mcpservers_not_dict_expects_empty(self):
        """Test mcpServers as non-dict returns empty."""
        # Arrange
        manager = MCPParamsManager()

        invalid_payload = {"mcpServers": "not a dict"}

        with patch.object(
            manager, "_load_servers_payload", return_value=invalid_payload
        ):
            # Act
            params = manager._load_configured_params()

            # Assert
            assert params == []

    def test_load_with_none_payload_expects_empty(self):
        """Test None payload returns empty list."""
        # Arrange
        manager = MCPParamsManager()

        with patch.object(manager, "_load_servers_payload", return_value=None):
            # Act
            params = manager._load_configured_params()

            # Assert
            assert params == []
