"""Unit tests for MCPManager reload functionality."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from src.integrations.mcp.manager import MCPManager
from src.integrations.mcp.server_params import MCPParamsManager, MCPServerParams
from src.shared.exceptions import (
    MCPNoServersAvailableError,
    MCPServerDisabledError,
    MCPServerNotFoundError,
    MCPServerReloadError,
)


class TestMCPManagerReloadServer:
    """Test MCPManager.reload_server method."""

    @pytest.fixture
    def mock_params_manager(self):
        """Create a mock MCPParamsManager."""
        manager = MagicMock(spec=MCPParamsManager)
        manager.validate_config = MagicMock(return_value=True)
        return manager

    @pytest.fixture
    def mcp_manager(self, mock_params_manager):
        """Create MCPManager instance with mocked params manager."""
        # Reset singleton state
        MCPManager._instance = None
        MCPManager._class_initialised = False
        manager = MCPManager(params_manager=mock_params_manager)
        manager._initialized = True
        return manager

    @pytest.fixture
    def sample_server_config(self):
        """Create a sample MCP server configuration."""
        return MCPServerParams(
            name="test-server",
            enabled=True,
            command="node",
            args=["server.js"],
            env={},
        )

    @pytest.mark.asyncio
    async def test_reload_server_with_existing_server_expects_success(
        self, mcp_manager, mock_params_manager, sample_server_config
    ):
        """Test successfully reloading an existing server."""
        # Arrange
        server_name = "test-server"
        mock_server = AsyncMock()
        mock_server.__aexit__ = AsyncMock()
        mcp_manager._servers[server_name] = mock_server
        mcp_manager._configs = [sample_server_config]

        # Mock config reload
        mock_params_manager.get_default_params.return_value = [sample_server_config]

        # Mock server initialization
        new_mock_server = AsyncMock()
        with patch(
            "src.integrations.mcp.manager.MCPTools", return_value=new_mock_server
        ):
            # Act
            result = await mcp_manager.reload_server(server_name)

            # Assert
            assert result.server_name == server_name
            assert result.success is True
            assert "reloaded successfully" in result.message.lower()
            assert server_name in mcp_manager._servers
            mock_server.__aexit__.assert_called_once()

    @pytest.mark.asyncio
    async def test_reload_server_with_nonexistent_server_expects_not_found_error(
        self, mcp_manager, mock_params_manager
    ):
        """Test reloading a server that doesn't exist raises error."""
        # Arrange
        server_name = "nonexistent-server"
        mock_params_manager.get_default_params.return_value = []

        # Act & Assert
        with pytest.raises(MCPServerNotFoundError) as exc_info:
            await mcp_manager.reload_server(server_name)

        assert server_name in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_reload_server_with_disabled_server_expects_disabled_error(
        self, mcp_manager, mock_params_manager
    ):
        """Test reloading a disabled server raises error."""
        # Arrange
        server_name = "disabled-server"
        disabled_config = MCPServerParams(
            name=server_name,
            enabled=False,
            command="node",
            args=["server.js"],
            env={},
        )
        mock_params_manager.get_default_params.return_value = [disabled_config]

        # Act & Assert
        with pytest.raises(MCPServerDisabledError) as exc_info:
            await mcp_manager.reload_server(server_name)

        assert server_name in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_reload_server_with_init_failure_expects_reload_error(
        self, mcp_manager, mock_params_manager, sample_server_config
    ):
        """Test reload error when server initialization fails."""
        # Arrange
        server_name = "test-server"
        mcp_manager._servers[server_name] = AsyncMock()
        mcp_manager._configs = [sample_server_config]
        mock_params_manager.get_default_params.return_value = [sample_server_config]

        # Mock server initialization to fail
        with patch(
            "src.integrations.mcp.manager.MCPTools",
            side_effect=Exception("Init failed"),
        ):
            # Act & Assert
            with pytest.raises(MCPServerReloadError) as exc_info:
                await mcp_manager.reload_server(server_name)

            assert server_name in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_reload_server_with_updated_config_expects_new_config_loaded(
        self, mcp_manager, mock_params_manager
    ):
        """Test that reload picks up updated configuration from JSON."""
        # Arrange
        server_name = "test-server"
        old_config = MCPServerParams(
            name=server_name,
            enabled=True,
            command="node",
            args=["old-server.js"],
            env={},
        )
        new_config = MCPServerParams(
            name=server_name,
            enabled=True,
            command="node",
            args=["new-server.js"],  # Updated args
            env={"NEW_VAR": "value"},  # Updated env
        )

        mcp_manager._servers[server_name] = AsyncMock()
        mcp_manager._servers[server_name].__aexit__ = AsyncMock()
        mcp_manager._configs = [old_config]

        # Mock config reload to return new config
        mock_params_manager.get_default_params.return_value = [new_config]

        # Mock server initialization
        new_mock_server = AsyncMock()
        with patch("src.integrations.mcp.manager.MCPTools") as mock_mcp_tools_class:
            mock_mcp_tools_class.return_value = new_mock_server

            # Act
            await mcp_manager.reload_server(server_name)

            # Assert - verify MCPTools was called with new config
            assert mock_mcp_tools_class.called
            # Verify config was refreshed by checking _configs updated
            assert len(mcp_manager._configs) == 1
            assert mcp_manager._configs[0].args == ["new-server.js"]
            assert mcp_manager._configs[0].env is not None
            assert mcp_manager._configs[0].env.get("NEW_VAR") == "value"


class TestMCPManagerReloadAllServers:
    """Test MCPManager.reload_all_servers method."""

    @pytest.fixture
    def mock_params_manager(self):
        """Create a mock MCPParamsManager."""
        manager = MagicMock(spec=MCPParamsManager)
        manager.validate_config = MagicMock(return_value=True)
        return manager

    @pytest.fixture
    def mcp_manager(self, mock_params_manager):
        """Create MCPManager instance with mocked params manager."""
        # Reset singleton state
        MCPManager._instance = None
        MCPManager._class_initialised = False
        manager = MCPManager(params_manager=mock_params_manager)
        manager._initialized = True
        return manager

    @pytest.mark.asyncio
    async def test_reload_all_servers_with_enabled_servers_expects_success(
        self, mcp_manager, mock_params_manager
    ):
        """Test successfully reloading all enabled servers."""
        # Arrange
        configs = [
            MCPServerParams(
                name="server1", enabled=True, command="node", args=["s1.js"], env={}
            ),
            MCPServerParams(
                name="server2", enabled=True, command="node", args=["s2.js"], env={}
            ),
            MCPServerParams(
                name="server3", enabled=False, command="node", args=["s3.js"], env={}
            ),
        ]

        # Add existing servers
        for config in configs[:2]:
            mock_server = AsyncMock()
            mock_server.__aexit__ = AsyncMock()
            mcp_manager._servers[config.name] = mock_server

        mcp_manager._configs = configs
        mock_params_manager.get_default_params.return_value = configs

        # Mock server initialization
        with patch("src.integrations.mcp.manager.MCPTools") as mock_mcp_tools:
            mock_mcp_tools.return_value = AsyncMock()

            # Act
            result = await mcp_manager.reload_all_servers()

            # Assert
            assert result.success is True
            assert result.reloaded_count == 2
            assert result.failed_count == 0
            assert len(result.results) == 2
            assert all(s.success for s in result.results)

    @pytest.mark.asyncio
    async def test_reload_all_servers_with_no_enabled_servers_expects_error(
        self, mcp_manager, mock_params_manager
    ):
        """Test reloading when no servers are enabled raises error."""
        # Arrange
        configs = [
            MCPServerParams(
                name="server1", enabled=False, command="node", args=["s1.js"], env={}
            ),
        ]
        mock_params_manager.get_default_params.return_value = configs

        # Act & Assert
        with pytest.raises(MCPNoServersAvailableError):
            await mcp_manager.reload_all_servers()

    @pytest.mark.asyncio
    async def test_reload_all_servers_with_partial_failures_expects_partial_success(
        self, mcp_manager, mock_params_manager
    ):
        """Test reload continues even when some servers fail."""
        # Arrange
        configs = [
            MCPServerParams(
                name="good-server",
                enabled=True,
                command="node",
                args=["good.js"],
                env={},
            ),
            MCPServerParams(
                name="bad-server",
                enabled=True,
                command="node",
                args=["bad.js"],
                env={},
            ),
        ]

        for config in configs:
            mock_server = AsyncMock()
            mock_server.__aexit__ = AsyncMock()
            mcp_manager._servers[config.name] = mock_server

        mcp_manager._configs = configs
        mock_params_manager.get_default_params.return_value = configs

        # Mock server initialization - one succeeds, one fails
        call_count = 0

        def side_effect(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:  # First call succeeds
                return AsyncMock()
            raise Exception("Init failed")  # Second call fails

        with patch("src.integrations.mcp.manager.MCPTools", side_effect=side_effect):
            # Act
            result = await mcp_manager.reload_all_servers()

            # Assert
            assert result.success is True  # Overall success if any server reloaded
            assert result.reloaded_count == 1
            assert result.failed_count == 1
            assert len(result.results) == 2
            # Check that one succeeded and one failed
            success_count = sum(1 for s in result.results if s.success)
            assert success_count == 1

    @pytest.mark.asyncio
    async def test_reload_all_servers_with_removed_server_expects_server_removed(
        self, mcp_manager, mock_params_manager
    ):
        """Test that servers removed from config are cleaned up on reload."""
        # Arrange
        old_configs = [
            MCPServerParams(
                name="server1", enabled=True, command="node", args=["s1.js"], env={}
            ),
            MCPServerParams(
                name="server2", enabled=True, command="node", args=["s2.js"], env={}
            ),
        ]
        new_configs = [
            MCPServerParams(
                name="server1", enabled=True, command="node", args=["s1.js"], env={}
            ),
            # server2 removed
        ]

        # Add existing servers
        for config in old_configs:
            mock_server = AsyncMock()
            mock_server.__aexit__ = AsyncMock()
            mcp_manager._servers[config.name] = mock_server

        mcp_manager._configs = old_configs

        # Mock config reload to return updated configs
        mock_params_manager.get_default_params.return_value = new_configs

        # Mock server initialization
        with patch("src.integrations.mcp.manager.MCPTools") as mock_mcp_tools:
            mock_mcp_tools.return_value = AsyncMock()

            # Act
            await mcp_manager.reload_all_servers()

            # Assert
            assert "server1" in mcp_manager._servers
            assert "server2" not in mcp_manager._servers  # Removed server cleaned up
            assert mcp_manager._configs == new_configs  # Config updated
