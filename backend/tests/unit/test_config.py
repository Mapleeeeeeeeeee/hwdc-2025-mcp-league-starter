"""Unit tests for application configuration and secrets management.

This test suite validates Settings class behavior including:
- Secret retrieval with format validation
- Security enforcement for malformed secrets
- Environment variable parsing
"""

from __future__ import annotations

import os
import warnings
from unittest.mock import patch

import pytest
from src.config import Settings


class TestSettingsGetSecret:
    """Test Settings.get_secret() method for secure secret retrieval."""

    def test_get_secret_with_valid_value_expects_value_returned(self):
        """Test retrieving a valid secret returns the value."""
        # Arrange
        settings = Settings()
        expected_value = "valid-secret-token-123"

        # Act
        with patch.dict(os.environ, {"TEST_SECRET": expected_value}):
            actual_value = settings.get_secret("TEST_SECRET")

        # Assert
        assert actual_value == expected_value

    def test_get_secret_with_missing_variable_expects_none(self):
        """Test retrieving non-existent secret returns None."""
        # Arrange
        settings = Settings()

        # Act
        with patch.dict(os.environ, {}, clear=True):
            actual_value = settings.get_secret("NONEXISTENT_SECRET")

        # Assert
        assert actual_value is None

    def test_get_secret_with_default_value_expects_default_returned(self):
        """Test retrieving missing secret with default returns default value."""
        # Arrange
        settings = Settings()
        default_value = "default-secret"

        # Act
        with patch.dict(os.environ, {}, clear=True):
            actual_value = settings.get_secret("MISSING_SECRET", default=default_value)

        # Assert
        assert actual_value == default_value

    def test_get_secret_with_leading_whitespace_expects_stripped_value(self):
        """Test secret with leading whitespace is automatically stripped."""
        # Arrange
        settings = Settings()
        raw_value = "  secret-with-whitespace"
        expected_value = "secret-with-whitespace"

        # Act
        with patch.dict(os.environ, {"WHITESPACE_SECRET": raw_value}):
            with warnings.catch_warnings(record=True) as warning_list:
                warnings.simplefilter("always")
                actual_value = settings.get_secret("WHITESPACE_SECRET")

        # Assert
        assert actual_value == expected_value
        assert len(warning_list) == 1
        assert "leading/trailing whitespace" in str(warning_list[0].message)

    def test_get_secret_with_trailing_whitespace_expects_stripped_value(self):
        """Test secret with trailing whitespace is automatically stripped."""
        # Arrange
        settings = Settings()
        raw_value = "secret-with-whitespace  "
        expected_value = "secret-with-whitespace"

        # Act
        with patch.dict(os.environ, {"WHITESPACE_SECRET": raw_value}):
            with warnings.catch_warnings(record=True) as warning_list:
                warnings.simplefilter("always")
                actual_value = settings.get_secret("WHITESPACE_SECRET")

        # Assert
        assert actual_value == expected_value
        assert len(warning_list) == 1

    def test_get_secret_with_strip_false_expects_unmodified_value(self):
        """Test secret with strip=False returns value with whitespace."""
        # Arrange
        settings = Settings()
        expected_value = "  secret-with-whitespace  "

        # Act
        with patch.dict(os.environ, {"WHITESPACE_SECRET": expected_value}):
            actual_value = settings.get_secret("WHITESPACE_SECRET", strip=False)

        # Assert
        assert actual_value == expected_value

    def test_get_secret_with_equals_prefix_expects_value_error(self):
        """Test secret starting with '=' raises ValueError.

        This prevents security issues from malformed .env files like:
        MCP_SERVER_AUTH_TOKEN==value (would be read as "=value")
        """
        # Arrange
        settings = Settings()
        malformed_value = "=invalid-secret-format"

        # Act & Assert
        with patch.dict(os.environ, {"MALFORMED_SECRET": malformed_value}):
            with pytest.raises(
                ValueError,
                match="Secret 'MALFORMED_SECRET' has invalid format: starts with '='",
            ):
                settings.get_secret("MALFORMED_SECRET")

    def test_get_secret_with_double_equals_expects_value_error(self):
        """Test secret from KEY==VALUE format raises ValueError.

        Simulates common .env file mistake: KEY==VALUE instead of KEY=VALUE
        """
        # Arrange
        settings = Settings()
        # This is what os.getenv would return for MCP_SERVER_AUTH_TOKEN==secret
        malformed_value = "=secret-token-123"

        # Act & Assert
        with patch.dict(os.environ, {"AUTH_TOKEN": malformed_value}):
            with pytest.raises(ValueError, match="starts with '='"):
                settings.get_secret("AUTH_TOKEN")

    def test_get_secret_with_validate_false_allows_equals_prefix(self):
        """Test validation can be disabled to allow '=' prefix."""
        # Arrange
        settings = Settings()
        value_with_equals = "=some-value"

        # Act
        with patch.dict(os.environ, {"SPECIAL_SECRET": value_with_equals}):
            actual_value = settings.get_secret("SPECIAL_SECRET", validate_format=False)

        # Assert
        assert actual_value == value_with_equals

    def test_get_secret_with_empty_string_expects_empty_string(self):
        """Test empty string secret is preserved."""
        # Arrange
        settings = Settings()

        # Act
        with patch.dict(os.environ, {"EMPTY_SECRET": ""}):
            actual_value = settings.get_secret("EMPTY_SECRET")

        # Assert
        assert actual_value == ""

    def test_get_secret_with_only_whitespace_expects_empty_after_strip(self):
        """Test secret with only whitespace becomes empty after strip."""
        # Arrange
        settings = Settings()

        # Act
        with patch.dict(os.environ, {"WHITESPACE_ONLY": "   "}):
            with warnings.catch_warnings(record=True):
                warnings.simplefilter("always")
                actual_value = settings.get_secret("WHITESPACE_ONLY")

        # Assert
        assert actual_value == ""


class TestSettingsMCPServerAuthToken:
    """Test MCP_SERVER_AUTH_TOKEN environment variable handling.

    These tests validate that the application correctly handles and validates
    the authentication token used for MCP server peer-to-peer communication.
    """

    def test_mcp_server_import_with_valid_token_expects_success(self):
        """Test importing mcp.server module with valid token succeeds."""
        # Arrange
        valid_token = "valid-bearer-token-123"

        # Act & Assert
        with patch.dict(os.environ, {"MCP_SERVER_AUTH_TOKEN": valid_token}):
            # Should not raise
            import importlib

            import src.integrations.mcp.server

            importlib.reload(src.integrations.mcp.server)

    def test_mcp_server_import_without_token_expects_value_error(self):
        """Test importing mcp.server module without token raises ValueError."""
        # Arrange & Act & Assert
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(
                ValueError,
                match="MCP_SERVER_AUTH_TOKEN environment variable is required",
            ):
                import importlib

                import src.integrations.mcp.server

                importlib.reload(src.integrations.mcp.server)

    def test_mcp_server_import_with_malformed_token_expects_value_error(self):
        """Test importing mcp.server with malformed token raises ValueError.

        This test validates protection against .env file errors like:
        MCP_SERVER_AUTH_TOKEN==secret (double equals)
        """
        # Arrange
        malformed_token = "=bearer-token-with-prefix"

        # Act & Assert
        with patch.dict(os.environ, {"MCP_SERVER_AUTH_TOKEN": malformed_token}):
            with pytest.raises(ValueError, match="starts with '='"):
                import importlib

                import src.integrations.mcp.server

                importlib.reload(src.integrations.mcp.server)

    def test_mcp_server_import_with_whitespace_token_expects_warning(self):
        """Test importing mcp.server with whitespace token triggers warning."""
        # Arrange
        token_with_whitespace = "  bearer-token-123  "

        # Act
        with patch.dict(os.environ, {"MCP_SERVER_AUTH_TOKEN": token_with_whitespace}):
            with warnings.catch_warnings(record=True) as warning_list:
                warnings.simplefilter("always")
                import importlib

                import src.integrations.mcp.server

                importlib.reload(src.integrations.mcp.server)

        # Assert
        assert len(warning_list) >= 1
        assert any(
            "leading/trailing whitespace" in str(w.message) for w in warning_list
        )


class TestSettingsCORSConfiguration:
    """Test CORS configuration parsing and validation."""

    def test_cors_origins_in_development_expects_default_origins(self):
        """Test CORS origins in development mode returns sensible defaults."""
        # Arrange
        with patch.dict(
            os.environ,
            {"ENVIRONMENT": "development", "CORS_ALLOWED_ORIGINS": ""},
            clear=True,
        ):
            settings = Settings()

        # Act
        origins = settings.cors_origins

        # Assert
        assert "http://localhost:3001" in origins
        assert "http://localhost:8080" in origins
        assert "http://localhost:3000" in origins

    def test_cors_origins_in_production_without_config_expects_empty_list(self):
        """Test CORS origins in production without config returns empty list."""
        # Arrange
        with patch.dict(
            os.environ,
            {"ENVIRONMENT": "production", "CORS_ALLOWED_ORIGINS": ""},
            clear=True,
        ):
            settings = Settings()

        # Act
        origins = settings.cors_origins

        # Assert
        assert origins == []

    def test_cors_origins_with_explicit_config_expects_configured_origins(self):
        """Test explicitly configured CORS origins are used."""
        # Arrange
        with patch.dict(
            os.environ,
            {"CORS_ALLOWED_ORIGINS": '["https://app.example.com"]'},
        ):
            settings = Settings()

        # Act
        origins = settings.cors_origins

        # Assert
        assert origins == ["https://app.example.com"]
