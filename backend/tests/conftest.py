"""Test configuration shared across unit and integration suites."""

from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

os.chdir(ROOT)

# Set up test environment variables before any imports
# This ensures that modules requiring these variables can be imported successfully
# The token set here is ONLY used when no real token is present (e.g., in CI)
# If MCP_SERVER_AUTH_TOKEN is already set in the environment, it will NOT be overridden
if "MCP_SERVER_AUTH_TOKEN" not in os.environ:
    os.environ["MCP_SERVER_AUTH_TOKEN"] = "test-token-for-testing-only"


@pytest.fixture
def test_mcp_auth_token() -> str:
    """Provide the MCP server authentication token for tests.

    This fixture provides the current MCP_SERVER_AUTH_TOKEN value,
    which could be either:
    - The real token from environment (for integration tests)
    - The test fallback token (for unit tests in CI)
    """
    return os.environ["MCP_SERVER_AUTH_TOKEN"]
