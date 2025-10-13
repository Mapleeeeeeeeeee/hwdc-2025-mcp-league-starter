"""Integration tests for Agno configuration API endpoints."""

import pytest
from httpx import AsyncClient


@pytest.mark.integration
@pytest.mark.api
class TestAgnoConfigAPI:
    """Test suite for Agno configuration API endpoints."""

    @pytest.mark.asyncio
    async def test_get_config__returns_toolkits_and_prompts(self, client: AsyncClient):
        """Test GET /api/v1/agno/config returns configuration."""
        response = await client.get("/api/v1/agno/config")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "toolkits" in data["data"]
        assert "prompts" in data["data"]
        assert isinstance(data["data"]["toolkits"], list)
        assert isinstance(data["data"]["prompts"], list)

    @pytest.mark.asyncio
    async def test_update_toolkit__valid_key__returns_success(
        self, client: AsyncClient
    ):
        """Test PATCH /api/v1/agno/toolkits/{key} with valid key."""
        # First get available toolkits
        config_response = await client.get("/api/v1/agno/config")
        toolkits = config_response.json()["data"]["toolkits"]

        if not toolkits:
            pytest.skip("No toolkits configured")

        toolkit_key = toolkits[0]["key"]
        original_enabled = toolkits[0]["enabled"]

        # Toggle the enabled state
        response = await client.patch(
            f"/api/v1/agno/toolkits/{toolkit_key}",
            json={"enabled": not original_enabled},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert toolkit_key in data["message"]

        # Restore original state
        await client.patch(
            f"/api/v1/agno/toolkits/{toolkit_key}",
            json={"enabled": original_enabled},
        )

    @pytest.mark.asyncio
    async def test_update_toolkit__invalid_key__returns_404(self, client: AsyncClient):
        """Test PATCH /api/v1/agno/toolkits/{key} with invalid key."""
        response = await client.patch(
            "/api/v1/agno/toolkits/nonexistent_toolkit",
            json={"enabled": True},
        )

        assert response.status_code == 400
        data = response.json()
        assert data["success"] is False
        assert data["error"]["type"] == "ToolkitNotFoundError"

    @pytest.mark.asyncio
    async def test_update_prompt__valid_key__returns_success(self, client: AsyncClient):
        """Test PATCH /api/v1/agno/prompts/{key} with valid key."""
        # First get available prompts
        config_response = await client.get("/api/v1/agno/config")
        prompts = config_response.json()["data"]["prompts"]

        if not prompts:
            pytest.skip("No prompts configured")

        prompt_key = prompts[0]["key"]
        original_enabled = prompts[0]["enabled"]

        # Toggle the enabled state
        response = await client.patch(
            f"/api/v1/agno/prompts/{prompt_key}",
            json={"enabled": not original_enabled},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert prompt_key in data["message"]

        # Restore original state
        await client.patch(
            f"/api/v1/agno/prompts/{prompt_key}",
            json={"enabled": original_enabled},
        )

    @pytest.mark.asyncio
    async def test_update_prompt__invalid_key__returns_404(self, client: AsyncClient):
        """Test PATCH /api/v1/agno/prompts/{key} with invalid key."""
        response = await client.patch(
            "/api/v1/agno/prompts/nonexistent_prompt",
            json={"enabled": True},
        )

        assert response.status_code == 400
        data = response.json()
        assert data["success"] is False
        assert data["error"]["type"] == "PromptNotFoundError"

    @pytest.mark.asyncio
    async def test_get_config__includes_trace_id_header(self, client: AsyncClient):
        """Test that response includes trace ID header."""
        response = await client.get("/api/v1/agno/config")

        assert response.status_code == 200
        assert "x-trace-id" in response.headers
