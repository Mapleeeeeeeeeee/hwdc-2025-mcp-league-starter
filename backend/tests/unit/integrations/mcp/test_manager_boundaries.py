"""Boundary and edge case tests for MCPManager."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from src.integrations.mcp.manager import (
    MCPManager,
    get_available_mcp_servers,
    get_mcp_status,
    graceful_mcp_cleanup,
    initialize_mcp_system,
    is_mcp_initialized,
)
from src.integrations.mcp.server_params import (
    MCPParamsManager,
    MCPServerParams,
    TransportType,
)


class TestMCPManagerSystemInitialization:
    """Test system initialization boundary cases."""

    @pytest.fixture
    def mock_params_manager(self):
        """Create mock params manager."""
        manager = MagicMock(spec=MCPParamsManager)
        manager.settings = MagicMock()
        manager.settings.enable_mcp_system = True
        manager.validate_config = MagicMock(return_value=True)
        manager.check_environment_requirements = MagicMock(
            return_value={"node": True, "npm": True}
        )
        manager.get_default_params = MagicMock(return_value=[])
        return manager

    @pytest.fixture
    def mcp_manager(self, mock_params_manager):
        """Create MCPManager instance."""
        MCPManager._instance = None
        MCPManager._class_initialised = False
        return MCPManager(params_manager=mock_params_manager)

    @pytest.mark.asyncio
    async def test_initialize_with_disabled_system_expects_false(
        self, mcp_manager, mock_params_manager
    ):
        """Test initialization with MCP system disabled returns False."""
        # Arrange - system disabled
        mock_params_manager.settings.enable_mcp_system = False

        # Act
        result = await mcp_manager.initialize_system()

        # Assert - should return False and not initialize
        assert result is False
        assert not mcp_manager.is_initialized()

    @pytest.mark.asyncio
    async def test_initialize_with_no_valid_configs_expects_false(
        self, mcp_manager, mock_params_manager
    ):
        """Test initialization with no valid configs returns False."""
        # Arrange - no configs
        mock_params_manager.get_default_params.return_value = []

        # Act
        result = await mcp_manager.initialize_system()

        # Assert
        assert result is False
        assert not mcp_manager.is_initialized()

    @pytest.mark.asyncio
    async def test_initialize_with_invalid_config_expects_skipped(
        self, mcp_manager, mock_params_manager
    ):
        """Test invalid config is skipped during initialization."""
        # Arrange - invalid config
        invalid_config = MCPServerParams(
            name="invalid-server",
            transport=TransportType.STDIO,
            command="node",
            enabled=True,
        )
        mock_params_manager.get_default_params.return_value = [invalid_config]
        mock_params_manager.validate_config.return_value = False

        # Act
        result = await mcp_manager.initialize_system()

        # Assert - should skip invalid config
        assert result is False
        assert not mcp_manager.is_initialized()

    @pytest.mark.asyncio
    async def test_initialize_with_valid_config_expects_success(
        self, mcp_manager, mock_params_manager
    ):
        """Test initialization with valid config succeeds."""
        # Arrange
        valid_config = MCPServerParams(
            name="valid-server",
            transport=TransportType.STDIO,
            command="node",
            args=["server.js"],
            enabled=True,
        )
        mock_params_manager.get_default_params.return_value = [valid_config]
        mock_params_manager.validate_config.return_value = True

        mock_tools = MagicMock()
        mock_tools.functions = {"test_func": MagicMock()}

        with patch(
            "src.integrations.mcp.manager.MCPTools",
            return_value=mock_tools,
        ):
            # Act
            result = await mcp_manager.initialize_system()

            # Assert
            assert result is True
            assert mcp_manager.is_initialized()


class TestMCPManagerServerStatus:
    """Test server status and metadata boundary cases."""

    @pytest.fixture
    def mcp_manager(self):
        """Create MCPManager instance."""
        MCPManager._instance = None
        MCPManager._class_initialised = False
        manager = MCPManager()
        return manager

    def test_get_server_status_with_no_servers_expects_empty_dict(self, mcp_manager):
        """Test server status with no servers returns empty dict."""
        # Arrange - no servers
        mcp_manager._configs = []
        mcp_manager._servers = {}

        # Act
        status = mcp_manager.get_server_status()

        # Assert
        assert status == {}

    def test_get_server_status_with_disconnected_server_expects_info(self, mcp_manager):
        """Test status includes disconnected server from config."""
        # Arrange - config exists but server not connected
        config = MCPServerParams(
            name="disconnected-server",
            transport=TransportType.STDIO,
            command="node",
            description="Test server",
            enabled=True,
        )
        mcp_manager._configs = [config]
        mcp_manager._servers = {}

        # Act
        status = mcp_manager.get_server_status()

        # Assert
        assert "disconnected-server" in status
        assert status["disconnected-server"]["connected"] is False
        assert status["disconnected-server"]["enabled"] is True
        assert status["disconnected-server"]["description"] == "Test server"

    def test_get_server_status_with_connected_server_expects_details(self, mcp_manager):
        """Test status includes connected server details."""
        # Arrange - connected server
        config = MCPServerParams(
            name="connected-server",
            transport=TransportType.STDIO,
            command="node",
            description="Connected",
            enabled=True,
        )
        mock_tools = MagicMock()
        mock_tools.functions = {
            "func1": {"name": "func1"},
            "func2": {"name": "func2"},
        }

        mcp_manager._configs = [config]
        mcp_manager._servers = {"connected-server": mock_tools}

        # Act
        status = mcp_manager.get_server_status()

        # Assert
        assert "connected-server" in status
        assert status["connected-server"]["connected"] is True
        assert status["connected-server"]["function_count"] == 2
        assert "func1" in status["connected-server"]["functions"]

    def test_get_system_status_when_not_initialized_expects_message(self, mcp_manager):
        """Test system status when not initialized."""
        # Arrange - not initialized
        mcp_manager._initialized = False

        # Act
        status = mcp_manager.get_system_status()

        # Assert
        assert status["initialized"] is False
        assert status["total_servers"] == 0
        assert status["total_functions"] == 0
        assert "message" in status

    def test_get_system_status_when_initialized_expects_summary(self, mcp_manager):
        """Test system status when initialized with servers."""
        # Arrange
        config = MCPServerParams(
            name="server1",
            transport=TransportType.STDIO,
            command="node",
            enabled=True,
        )
        mock_tools = MagicMock()
        mock_tools.functions = {"func1": {}, "func2": {}, "func3": {}}

        mcp_manager._initialized = True
        mcp_manager._configs = [config]
        mcp_manager._servers = {"server1": mock_tools}

        # Act
        status = mcp_manager.get_system_status()

        # Assert
        assert status["initialized"] is True
        assert status["total_servers"] == 1
        assert status["total_functions"] == 3
        assert "server1" in status["servers"]


class TestMCPManagerShutdownBoundaries:
    """Test shutdown and cleanup boundary cases."""

    @pytest.fixture
    def mcp_manager(self):
        """Create MCPManager instance."""
        MCPManager._instance = None
        MCPManager._class_initialised = False
        return MCPManager()

    @pytest.mark.asyncio
    async def test_shutdown_when_not_initialized_expects_no_error(self, mcp_manager):
        """Test shutdown when not initialized completes without error."""
        # Arrange - not initialized
        mcp_manager._initialized = False
        mcp_manager._servers = {}

        # Act
        await mcp_manager.shutdown()

        # Assert - should complete without error
        assert not mcp_manager.is_initialized()

    @pytest.mark.asyncio
    async def test_shutdown_with_server_error_expects_continues(self, mcp_manager):
        """Test shutdown continues even if server close fails."""
        # Arrange - server that raises error on close
        mock_tools = MagicMock()
        mock_tools.__aexit__ = AsyncMock(side_effect=RuntimeError("Close failed"))

        mcp_manager._initialized = True
        mcp_manager._servers = {"error-server": mock_tools}

        # Act - should not raise
        await mcp_manager.shutdown()

        # Assert - should cleanup despite error
        assert len(mcp_manager._servers) == 0
        assert not mcp_manager.is_initialized()

    @pytest.mark.asyncio
    async def test_shutdown_with_multiple_servers_expects_all_closed(self, mcp_manager):
        """Test shutdown closes all servers."""
        # Arrange - multiple servers
        mock_tools1 = MagicMock()
        mock_tools1.__aexit__ = AsyncMock()
        mock_tools2 = MagicMock()
        mock_tools2.__aexit__ = AsyncMock()

        mcp_manager._initialized = True
        mcp_manager._servers = {
            "server1": mock_tools1,
            "server2": mock_tools2,
        }

        # Act
        await mcp_manager.shutdown()

        # Assert
        mock_tools1.__aexit__.assert_called_once()
        mock_tools2.__aexit__.assert_called_once()
        assert len(mcp_manager._servers) == 0


class TestMCPManagerGlobalFunctions:
    """Test global MCP manager functions."""

    @pytest.mark.asyncio
    async def test_initialize_mcp_system_expects_singleton_call(self):
        """Test global initialize calls singleton."""
        # Arrange
        MCPManager._instance = None

        with patch.object(
            MCPManager, "initialize_system", new_callable=AsyncMock
        ) as mock_init:
            mock_init.return_value = True

            # Act
            result = await initialize_mcp_system()

            # Assert
            assert result is True
            mock_init.assert_called_once()

    def test_get_mcp_status_expects_singleton_call(self):
        """Test global status calls singleton."""
        # Arrange
        MCPManager._instance = None

        with patch.object(MCPManager, "get_system_status") as mock_status:
            mock_status.return_value = {"initialized": False}

            # Act
            result = get_mcp_status()

            # Assert
            assert "initialized" in result
            mock_status.assert_called_once()

    @pytest.mark.asyncio
    async def test_graceful_cleanup_expects_singleton_call(self):
        """Test global cleanup calls singleton."""
        # Arrange
        MCPManager._instance = None

        with patch.object(
            MCPManager, "shutdown", new_callable=AsyncMock
        ) as mock_shutdown:
            # Act
            await graceful_mcp_cleanup()

            # Assert
            mock_shutdown.assert_called_once()

    def test_is_mcp_initialized_expects_singleton_call(self):
        """Test global is_initialized calls singleton."""
        # Arrange
        MCPManager._instance = None

        with patch.object(MCPManager, "is_initialized") as mock_is_init:
            mock_is_init.return_value = False

            # Act
            result = is_mcp_initialized()

            # Assert
            assert result is False
            mock_is_init.assert_called_once()

    def test_get_available_servers_expects_singleton_call(self):
        """Test global get_available calls singleton."""
        # Arrange
        MCPManager._instance = None

        with patch.object(MCPManager, "get_available_servers") as mock_get_avail:
            mock_get_avail.return_value = ["server1", "server2"]

            # Act
            result = get_available_mcp_servers()

            # Assert
            assert len(result) == 2
            mock_get_avail.assert_called_once()


class TestMCPManagerReloadServer:
    """Test reload server boundary cases."""

    @pytest.fixture
    def mock_params_manager(self):
        """Create mock params manager."""
        manager = MagicMock(spec=MCPParamsManager)
        manager.get_default_params = MagicMock(return_value=[])
        return manager

    @pytest.fixture
    def mcp_manager(self, mock_params_manager):
        """Create MCPManager instance."""
        MCPManager._instance = None
        MCPManager._class_initialised = False
        return MCPManager(params_manager=mock_params_manager)

    @pytest.mark.asyncio
    async def test_reload_nonexistent_server_expects_error(
        self, mcp_manager, mock_params_manager
    ):
        """Test reloading nonexistent server raises exception."""
        # Arrange
        from src.shared.exceptions.mcp import MCPServerNotFoundError

        mcp_manager._initialized = True
        mock_params_manager.get_default_params.return_value = []

        # Act & Assert - should raise exception
        with pytest.raises(MCPServerNotFoundError) as exc_info:
            await mcp_manager.reload_server("nonexistent")

        assert "nonexistent" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_reload_server_with_new_config_expects_reconnect(
        self, mcp_manager, mock_params_manager
    ):
        """Test reload with new config closes old and creates new."""
        # Arrange - existing server
        old_tools = MagicMock()
        old_tools.__aexit__ = AsyncMock()
        mcp_manager._initialized = True
        mcp_manager._servers = {"test-server": old_tools}

        new_config = MCPServerParams(
            name="test-server",
            transport=TransportType.STDIO,
            command="node",
            args=["server.js"],
            enabled=True,
        )
        mock_params_manager.get_default_params.return_value = [new_config]

        new_tools = MagicMock()
        new_tools.functions = {}

        with patch(
            "src.integrations.mcp.manager.MCPTools",
            return_value=new_tools,
        ):
            # Act
            result = await mcp_manager.reload_server("test-server")

            # Assert
            assert result.success is True
            old_tools.__aexit__.assert_called_once()
            assert mcp_manager._servers["test-server"] == new_tools
