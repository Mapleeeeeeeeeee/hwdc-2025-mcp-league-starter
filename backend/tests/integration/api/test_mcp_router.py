"""Integration tests for MCP router endpoints."""

from __future__ import annotations

from collections.abc import AsyncIterator

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from src.main import app

pytestmark = [pytest.mark.integration, pytest.mark.api]


@pytest_asyncio.fixture
async def async_client() -> AsyncIterator[AsyncClient]:
    transport = ASGITransport(app=app)
    await app.router.startup()
    try:
        async with AsyncClient(
            transport=transport,
            base_url="http://testserver",
        ) as client:
            yield client
    finally:
        await app.router.shutdown()


@pytest.mark.asyncio
async def test_list_mcp_servers__returns_status_payload(
    async_client: AsyncClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Mock the MCPManager's get_system_status method instead
    def _fake_get_system_status() -> dict[str, object]:
        return {
            "initialized": True,
            "servers": {
                "filesystem": {
                    "connected": True,
                    "enabled": True,
                    "description": "Filesystem browsing tools",
                    "functions": ["list", "read"],
                    "function_count": 2,
                },
                "context7": {
                    "connected": False,
                    "enabled": False,
                    "description": "Context7 integration",
                    "functions": [],
                    "function_count": 0,
                },
            },
            "total_servers": 2,
            "total_functions": 2,
        }

    from src.integrations.mcp.manager import MCPManager

    monkeypatch.setattr(
        MCPManager, "get_system_status", lambda self: _fake_get_system_status()
    )

    response = await async_client.get("/api/v1/mcp/servers")

    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["data"]["initialized"] is True
    servers = payload["data"]["servers"]
    assert len(servers) == 2

    filesystem = next(server for server in servers if server["name"] == "filesystem")
    assert filesystem["connected"] is True
    assert filesystem["enabled"] is True
    assert filesystem["functionCount"] == 2

    context7 = next(server for server in servers if server["name"] == "context7")
    assert context7["connected"] is False
    assert context7["enabled"] is False
    assert context7["functionCount"] == 0

    assert payload["message"] == "MCP servers retrieved"
    assert "X-Trace-ID" in response.headers
    assert "X-Process-Time" in response.headers
