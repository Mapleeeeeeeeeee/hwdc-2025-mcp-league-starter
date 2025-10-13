"""Tests for MCPServerGuardMiddleware."""

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from src.core.middleware import MCPServerGuardMiddleware


@pytest.fixture
def app_with_mcp_disabled():
    """Create a test app with MCP server disabled."""
    app = FastAPI()
    app.add_middleware(
        MCPServerGuardMiddleware,
        as_a_mcp_server=False,
        enable_mcp_system=True,
    )

    @app.get("/api/test")
    def test_endpoint():
        return {"status": "ok"}

    return app


@pytest.fixture
def app_with_mcp_enabled():
    """Create a test app with MCP server enabled."""
    app = FastAPI()
    app.add_middleware(
        MCPServerGuardMiddleware,
        as_a_mcp_server=True,
        enable_mcp_system=True,
    )

    @app.get("/api/test")
    def test_endpoint():
        return {"status": "ok"}

    @app.post("/mcp")
    def mcp_endpoint():
        return {"mcp": "active"}

    return app


def test_mcp_endpoint_blocked_when_disabled(app_with_mcp_disabled):
    """Test that /mcp endpoint returns 503 when AS_A_MCP_SERVER=false."""
    client = TestClient(app_with_mcp_disabled)

    # Test GET request
    response = client.get("/mcp")
    assert response.status_code == 503
    data = response.json()
    assert "error" in data
    assert data["error"]["type"] == "MCPServerNotAvailableError"
    assert data["error"]["context"]["as_a_mcp_server"] is False
    assert data["error"]["context"]["enable_mcp_system"] is True

    # Test POST request
    response = client.post("/mcp")
    assert response.status_code == 503

    # Test with path
    response = client.post("/mcp/some/path")
    assert response.status_code == 503


def test_mcp_endpoint_passes_when_enabled(app_with_mcp_enabled):
    """Test that /mcp endpoint passes through when AS_A_MCP_SERVER=true."""
    client = TestClient(app_with_mcp_enabled)

    response = client.post("/mcp")
    assert response.status_code == 200
    data = response.json()
    assert data["mcp"] == "active"


def test_non_mcp_endpoints_unaffected_when_disabled(app_with_mcp_disabled):
    """Test that non-MCP endpoints work normally when MCP is disabled."""
    client = TestClient(app_with_mcp_disabled)

    response = client.get("/api/test")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"


def test_non_mcp_endpoints_unaffected_when_enabled(app_with_mcp_enabled):
    """Test that non-MCP endpoints work normally when MCP is enabled."""
    client = TestClient(app_with_mcp_enabled)

    response = client.get("/api/test")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"


def test_error_message_content(app_with_mcp_disabled):
    """Test that error message contains helpful information."""
    client = TestClient(app_with_mcp_disabled)

    response = client.post("/mcp/test")
    data = response.json()

    # Check response structure
    assert "success" in data
    assert data["success"] is False
    assert "error" in data

    error = data["error"]
    assert "type" in error
    assert "message" in error
    assert "context" in error

    # Check message content
    assert "AS_A_MCP_SERVER" in error["message"]
    assert "set to false" in error["message"]
    assert "AS_A_MCP_SERVER=true" in error["message"]

    # Check context
    assert "hint" in error["context"]
    assert "ENABLE_MCP_SYSTEM=true" in error["context"]["hint"]
