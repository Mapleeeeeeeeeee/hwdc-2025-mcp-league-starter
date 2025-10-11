"""Unit tests for HTTP transport in MCPServerParams."""

from __future__ import annotations

import pytest
from src.integrations.mcp.server_params import (
    AuthType,
    HTTPAuthConfig,
    MCPServerParams,
    TransportType,
)


class TestHTTPAuthConfig:
    """Test HTTPAuthConfig authentication configuration."""

    def test_build_header_with_bearer_token_expects_bearer_header(self):
        """Test building bearer authentication header."""
        # Arrange
        auth = HTTPAuthConfig(
            type=AuthType.BEARER,
            token="test-bearer-token-123",
        )

        # Act
        header = auth.build_header()

        # Assert
        assert header == {"Authorization": "Bearer test-bearer-token-123"}

    def test_build_header_with_api_key_expects_api_key_header(self):
        """Test building API key authentication header."""
        # Arrange
        auth = HTTPAuthConfig(
            type=AuthType.API_KEY,
            token="api-key-xyz",
        )

        # Act
        header = auth.build_header()

        # Assert
        assert header == {"Authorization": "api-key-xyz"}

    def test_build_header_with_custom_header_name_expects_custom_header(self):
        """Test building authentication header with custom header name."""
        # Arrange
        auth = HTTPAuthConfig(
            type=AuthType.BEARER,
            token="custom-token",
            header_name="X-API-Key",
        )

        # Act
        header = auth.build_header()

        # Assert
        assert header == {"X-API-Key": "Bearer custom-token"}

    def test_init_with_empty_token_expects_value_error(self):
        """Test initializing with empty token raises ValueError."""
        # Act & Assert
        with pytest.raises(ValueError, match="Auth token cannot be empty"):
            HTTPAuthConfig(type=AuthType.BEARER, token="")

    def test_init_with_whitespace_token_expects_value_error(self):
        """Test initializing with whitespace-only token raises ValueError."""
        # Act & Assert
        with pytest.raises(ValueError, match="Auth token cannot be empty"):
            HTTPAuthConfig(type=AuthType.BEARER, token="   ")

    def test_init_with_empty_header_name_expects_value_error(self):
        """Test initializing with empty header name raises ValueError."""
        # Act & Assert
        with pytest.raises(ValueError, match="Header name cannot be empty"):
            HTTPAuthConfig(
                type=AuthType.BEARER,
                token="valid-token",
                header_name="",
            )

    def test_build_header_with_none_token_expects_value_error(self):
        """Test building header with None token raises ValueError."""
        # Arrange
        auth = HTTPAuthConfig(type=AuthType.BEARER, token="initial-token")
        auth.token = None  # Simulate corruption

        # Act & Assert
        with pytest.raises(ValueError, match="Cannot build header: token is None"):
            auth.build_header()


class TestMCPServerParamsHTTPTransport:
    """Test MCPServerParams with HTTP transport."""

    def test_init_with_http_transport_expects_http_server(self):
        """Test creating HTTP transport server configuration."""
        # Arrange & Act
        params = MCPServerParams(
            name="http-server",
            transport=TransportType.HTTP,
            url="https://api.example.com/mcp",
            timeout_seconds=60,
            enabled=True,
        )

        # Assert
        assert params.transport == TransportType.HTTP
        assert params.url == "https://api.example.com/mcp"
        assert params.is_http_transport() is True
        assert params.is_stdio_transport() is False

    def test_init_with_sse_transport_expects_http_behavior(self):
        """Test SSE transport is treated as HTTP transport."""
        # Arrange & Act
        params = MCPServerParams(
            name="sse-server",
            transport=TransportType.SSE,
            url="https://api.example.com/sse",
        )

        # Assert
        assert params.transport == TransportType.SSE
        assert params.is_http_transport() is True
        assert params.is_stdio_transport() is False

    def test_init_with_http_and_auth_expects_auth_configured(self):
        """Test creating HTTP server with authentication."""
        # Arrange
        auth = HTTPAuthConfig(
            type=AuthType.BEARER,
            token="secure-token",
        )

        # Act
        params = MCPServerParams(
            name="secure-http-server",
            transport=TransportType.HTTP,
            url="https://api.example.com/mcp",
            auth=auth,
        )

        # Assert
        assert params.auth is not None
        assert params.auth.type == AuthType.BEARER
        assert params.auth.token == "secure-token"

    def test_is_http_transport_with_stdio_expects_false(self):
        """Test is_http_transport returns False for stdio transport."""
        # Arrange
        params = MCPServerParams(
            name="stdio-server",
            transport=TransportType.STDIO,
            command="node",
            args=["server.js"],
        )

        # Act & Assert
        assert params.is_http_transport() is False
        assert params.is_stdio_transport() is True

    def test_get_full_command_with_http_transport_expects_empty_string(self):
        """Test get_full_command returns empty string for HTTP transport."""
        # Arrange
        params = MCPServerParams(
            name="http-server",
            transport=TransportType.HTTP,
            url="https://api.example.com/mcp",
        )

        # Act
        command = params.get_full_command()

        # Assert
        assert command == ""

    def test_get_command_list_with_http_transport_expects_empty_list(self):
        """Test get_command_list returns empty list for HTTP transport."""
        # Arrange
        params = MCPServerParams(
            name="http-server",
            transport=TransportType.HTTP,
            url="https://api.example.com/mcp",
        )

        # Act
        command_list = params.get_command_list()

        # Assert
        assert command_list == []


class TestMCPParamsManagerHTTPParsing:
    """Test MCPParamsManager parsing of HTTP server configurations."""

    def test_create_params_from_dict_with_http_type_expects_http_params(self):
        """Test parsing configuration with HTTP type."""
        # Arrange
        from src.integrations.mcp.server_params import MCPParamsManager

        manager = MCPParamsManager()
        config_data = {
            "name": "http-api",
            "type": "http",
            "url": "https://api.example.com/mcp",
            "timeout_seconds": 30,
            "enabled": True,
            "description": "HTTP MCP server",
        }

        # Act
        params = manager._create_params_from_dict(config_data)

        # Assert
        assert params is not None
        assert params.name == "http-api"
        assert params.transport == TransportType.HTTP
        assert params.url == "https://api.example.com/mcp"
        assert params.timeout_seconds == 30
        assert params.enabled is True

    def test_create_params_from_dict_with_bearer_auth_expects_auth_configured(self):
        """Test parsing HTTP configuration with bearer authentication."""
        # Arrange
        from src.integrations.mcp.server_params import MCPParamsManager

        manager = MCPParamsManager()
        config_data = {
            "name": "secure-api",
            "type": "http",
            "url": "https://api.example.com/mcp",
            "auth": {
                "type": "bearer",
                "token": "secret-token-123",
            },
        }

        # Act
        params = manager._create_params_from_dict(config_data)

        # Assert
        assert params is not None
        assert params.auth is not None
        assert params.auth.type == AuthType.BEARER
        assert params.auth.token == "secret-token-123"

    def test_create_params_from_dict_with_api_key_auth_expects_auth_configured(self):
        """Test parsing HTTP configuration with API key authentication."""
        # Arrange
        from src.integrations.mcp.server_params import MCPParamsManager

        manager = MCPParamsManager()
        config_data = {
            "name": "api-key-server",
            "type": "http",
            "url": "https://api.example.com/mcp",
            "auth": {
                "type": "api_key",
                "token": "api-key-xyz",
                "header_name": "X-API-Key",
            },
        }

        # Act
        params = manager._create_params_from_dict(config_data)

        # Assert
        assert params is not None
        assert params.auth is not None
        assert params.auth.type == AuthType.API_KEY
        assert params.auth.token == "api-key-xyz"
        assert params.auth.header_name == "X-API-Key"

    def test_create_params_from_dict_with_missing_url_expects_none(self):
        """Test parsing HTTP configuration without URL returns None."""
        # Arrange
        from src.integrations.mcp.server_params import MCPParamsManager

        manager = MCPParamsManager()
        config_data = {
            "name": "invalid-http",
            "type": "http",
            # Missing url
            "enabled": True,
        }

        # Act
        params = manager._create_params_from_dict(config_data)

        # Assert
        assert params is None

    def test_create_params_from_dict_with_invalid_auth_type_expects_bearer_fallback(
        self,
    ):
        """Test parsing with invalid auth type falls back to bearer."""
        # Arrange
        from src.integrations.mcp.server_params import MCPParamsManager

        manager = MCPParamsManager()
        config_data = {
            "name": "fallback-auth",
            "type": "http",
            "url": "https://api.example.com/mcp",
            "auth": {
                "type": "invalid_type",
                "token": "token-123",
            },
        }

        # Act
        params = manager._create_params_from_dict(config_data)

        # Assert
        assert params is not None
        assert params.auth is not None
        assert params.auth.type == AuthType.BEARER  # Fallback

    def test_create_params_from_dict_with_auth_but_no_token_expects_no_auth(self):
        """Test parsing with auth config but missing token results in no auth."""
        # Arrange
        from src.integrations.mcp.server_params import MCPParamsManager

        manager = MCPParamsManager()
        config_data = {
            "name": "no-token",
            "type": "http",
            "url": "https://api.example.com/mcp",
            "auth": {
                "type": "bearer",
                # Missing token
            },
        }

        # Act
        params = manager._create_params_from_dict(config_data)

        # Assert
        assert params is not None
        assert params.auth is None

    def test_validate_config_with_http_and_no_url_expects_false(self):
        """Test validating HTTP config without URL returns False."""
        # Arrange
        from src.integrations.mcp.server_params import MCPParamsManager

        manager = MCPParamsManager()
        params = MCPServerParams(
            name="invalid-http",
            transport=TransportType.HTTP,
            url=None,  # Invalid
        )

        # Act
        is_valid = manager.validate_config(params)

        # Assert
        assert is_valid is False

    def test_validate_config_with_http_and_url_expects_true(self):
        """Test validating valid HTTP config returns True."""
        # Arrange
        from src.integrations.mcp.server_params import MCPParamsManager

        manager = MCPParamsManager()
        params = MCPServerParams(
            name="valid-http",
            transport=TransportType.HTTP,
            url="https://api.example.com/mcp",
        )

        # Act
        is_valid = manager.validate_config(params)

        # Assert
        assert is_valid is True

    def test_validate_config_with_stdio_and_no_command_expects_false(self):
        """Test validating stdio config without command returns False."""
        # Arrange
        from src.integrations.mcp.server_params import MCPParamsManager

        manager = MCPParamsManager()
        params = MCPServerParams(
            name="invalid-stdio",
            transport=TransportType.STDIO,
            command=None,  # Invalid
        )

        # Act
        is_valid = manager.validate_config(params)

        # Assert
        assert is_valid is False
