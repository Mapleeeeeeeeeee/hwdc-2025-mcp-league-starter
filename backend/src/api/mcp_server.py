"""FastMCP server implementation exposing this application's capabilities."""

from __future__ import annotations

from fastmcp import FastMCP
from fastmcp.server.auth import StaticTokenVerifier

from src.config import settings
from src.core.logging import get_logger
from src.integrations.llm import ConversationAgentFactory
from src.integrations.mcp import manager as mcp_manager
from src.models.mcp_tools import (
    AppConfigResponse,
    GetServerCapabilitiesResponse,
    ListAvailableModelsResponse,
    MCPChatResponse,
    SystemHealthResponse,
)
from src.usecases.mcp.mcp_usecase import (
    MCPChatUsecase,
    MCPServerManagementUsecase,
)

logger = get_logger(__name__)


def get_mcp_manager() -> mcp_manager.MCPManager:
    return mcp_manager.MCPManager()


def get_agent_factory() -> ConversationAgentFactory:
    return ConversationAgentFactory()


# --- Authentication Setup ---
_mcp_auth_token = None
auth_provider = None
mcp_server = None


def initialize_mcp_server():
    """Initialize MCP server only when AS_A_MCP_SERVER is enabled."""
    global _mcp_auth_token, auth_provider, mcp_server

    if mcp_server is not None:
        return mcp_server

    _mcp_auth_token = settings.get_secret("MCP_SERVER_AUTH_TOKEN")
    if not _mcp_auth_token:
        raise ValueError(
            "MCP_SERVER_AUTH_TOKEN environment variable is required for "
            "MCP server authentication. Please set it in your .env file or "
            "environment variables. Example: "
            "MCP_SERVER_AUTH_TOKEN=your-secure-token-here"
        )

    auth_provider = StaticTokenVerifier(
        tokens={
            _mcp_auth_token: {
                "client_id": "mcp-peer-client",
                "scopes": ["mcp:read", "mcp:write", "mcp:admin"],
            }
        }
    )

    logger.info(
        "FastMCP server initialized with bearer token authentication (token: %s...)",
        _mcp_auth_token[:8],
    )

    # --- FastMCP Server Instance ---
    mcp_server = FastMCP(
        name="HWDC-2025-MCP-League",
        instructions="MCP server exposing conversation and MCP management capabilities",
        auth=auth_provider,
    )

    # --- MCP Tools (Thin wrappers around use cases) ---
    _register_mcp_tools(mcp_server)

    return mcp_server


def _register_mcp_tools(server: FastMCP):
    """Register all MCP tools on the server instance."""

    @server.tool
    async def chat(
        message: str,
        model_key: str | None = None,
        conversation_id: str | None = None,
        user_id: str = "peer-caller",
    ) -> MCPChatResponse:
        """Execute natural language conversation through local Agent."""
        logger.info("MCP tool 'chat' called by user=%s", user_id)
        agent_factory = get_agent_factory()
        chat_usecase = MCPChatUsecase(agent_factory=agent_factory)
        return await chat_usecase.chat(message, model_key, conversation_id, user_id)

    @server.tool
    def list_mcp_servers() -> dict:
        """List all configured MCP servers and their status."""
        logger.info("MCP tool called: list_mcp_servers")
        mcp_manager_instance = get_mcp_manager()
        agent_factory = get_agent_factory()
        management_usecase = MCPServerManagementUsecase(
            mcp_manager=mcp_manager_instance, agent_factory=agent_factory
        )
        # .model_dump() is used to convert the Pydantic model to a dict for the tool
        return management_usecase.list_servers().model_dump(by_alias=True)

    @server.tool
    async def reload_mcp_server(server_name: str) -> dict:
        """Reload a specific MCP server by name."""
        logger.info("MCP tool called: reload_mcp_server (server=%s)", server_name)
        mcp_manager_instance = get_mcp_manager()
        agent_factory = get_agent_factory()
        management_usecase = MCPServerManagementUsecase(
            mcp_manager=mcp_manager_instance, agent_factory=agent_factory
        )
        result = await management_usecase.reload_server(server_name)
        return result.model_dump(by_alias=True)

    @server.tool
    async def reload_all_mcp_servers() -> dict:
        """Reload all enabled MCP servers."""
        logger.info("MCP tool called: reload_all_mcp_servers")
        mcp_manager_instance = get_mcp_manager()
        agent_factory = get_agent_factory()
        management_usecase = MCPServerManagementUsecase(
            mcp_manager=mcp_manager_instance, agent_factory=agent_factory
        )
        result = await management_usecase.reload_all_servers()
        return result.model_dump(by_alias=True)

    @server.tool
    def get_mcp_server_functions(server_name: str) -> list[str]:
        """Get list of available functions for a specific MCP server."""
        logger.info(
            "MCP tool called: get_mcp_server_functions (server=%s)", server_name
        )
        mcp_manager_instance = get_mcp_manager()
        agent_factory = get_agent_factory()
        management_usecase = MCPServerManagementUsecase(
            mcp_manager=mcp_manager_instance, agent_factory=agent_factory
        )
        return management_usecase.get_server_functions(server_name)

    @server.tool
    def get_available_mcp_servers() -> list[str]:
        """Get list of all connected MCP server names."""
        logger.info("MCP tool called: get_available_mcp_servers")
        mcp_manager_instance = get_mcp_manager()
        agent_factory = get_agent_factory()
        management_usecase = MCPServerManagementUsecase(
            mcp_manager=mcp_manager_instance, agent_factory=agent_factory
        )
        return management_usecase.get_available_servers()

    @server.tool
    def list_available_models() -> ListAvailableModelsResponse:
        """List all available LLM models configured in this container."""
        logger.info("MCP tool 'list_available_models' called")
        mcp_manager_instance = get_mcp_manager()
        agent_factory = get_agent_factory()
        management_usecase = MCPServerManagementUsecase(
            mcp_manager=mcp_manager_instance, agent_factory=agent_factory
        )
        return management_usecase.list_available_models()

    @server.tool
    def get_server_capabilities() -> GetServerCapabilitiesResponse:
        """Get comprehensive capability information for this container."""
        logger.info("MCP tool 'get_server_capabilities' called")
        mcp_manager_instance = get_mcp_manager()
        agent_factory = get_agent_factory()
        management_usecase = MCPServerManagementUsecase(
            mcp_manager=mcp_manager_instance, agent_factory=agent_factory
        )
        return management_usecase.get_server_capabilities()

    @server.tool
    def get_app_config() -> AppConfigResponse:
        """Get application configuration information."""
        logger.info("MCP tool 'get_app_config' called")
        mcp_manager_instance = get_mcp_manager()
        agent_factory = get_agent_factory()
        management_usecase = MCPServerManagementUsecase(
            mcp_manager=mcp_manager_instance, agent_factory=agent_factory
        )
        return management_usecase.get_app_config()

    @server.tool
    def get_system_health() -> SystemHealthResponse:
        """Get system health status."""
        logger.info("MCP tool 'get_system_health' called")
        mcp_manager_instance = get_mcp_manager()
        agent_factory = get_agent_factory()
        management_usecase = MCPServerManagementUsecase(
            mcp_manager=mcp_manager_instance, agent_factory=agent_factory
        )
        return management_usecase.get_system_health()
