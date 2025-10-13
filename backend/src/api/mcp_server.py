"""FastMCP server implementation exposing this application's capabilities."""

from __future__ import annotations

from typing import Annotated, Any

from fastmcp import Depends, FastMCP
from fastmcp.server.auth import StaticTokenVerifier

from src.config import settings
from src.core.logging import get_logger
from src.integrations.llm import ConversationAgentFactory
from src.integrations.mcp import manager as mcp_manager
from src.usecases.mcp.mcp_usecase import (
    MCPChatUsecase,
    MCPServerManagementUsecase,
)

logger = get_logger(__name__)


def get_mcp_manager() -> mcp_manager.MCPManager:
    return mcp_manager.MCPManager()


def get_agent_factory() -> ConversationAgentFactory:
    return ConversationAgentFactory()


def get_server_management_usecase(
    mcp_manager_dep: Annotated[mcp_manager.MCPManager, Depends(get_mcp_manager)],
) -> MCPServerManagementUsecase:
    return MCPServerManagementUsecase(mcp_manager=mcp_manager_dep)


ServerManagementUsecaseDep = Annotated[
    MCPServerManagementUsecase, Depends(get_server_management_usecase)
]


def get_chat_usecase(
    agent_factory_dep: Annotated[ConversationAgentFactory, Depends(get_agent_factory)],
) -> MCPChatUsecase:
    return MCPChatUsecase(agent_factory=agent_factory_dep)


ChatUsecaseDep = Annotated[MCPChatUsecase, Depends(get_chat_usecase)]


# --- Authentication Setup ---
_mcp_auth_token = settings.get_secret("MCP_SERVER_AUTH_TOKEN")
if not _mcp_auth_token:
    raise ValueError(
        "MCP_SERVER_AUTH_TOKEN environment variable is required for "
        "MCP server authentication. Please set it in your .env file or "
        "environment variables. Example: MCP_SERVER_AUTH_TOKEN=your-secure-token-here"
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


@mcp_server.tool
async def chat(
    chat_usecase_dep: ChatUsecaseDep,
    message: str,
    model_key: str | None = None,
    conversation_id: str | None = None,
    user_id: str = "peer-caller",
) -> dict[str, Any]:
    """Execute natural language conversation through local Agent."""
    logger.info("MCP tool 'chat' called by user=%s", user_id)
    return await chat_usecase_dep.chat(message, model_key, conversation_id, user_id)


@mcp_server.tool
def list_mcp_servers(
    management_usecase_dep: ServerManagementUsecaseDep,
) -> dict[str, Any]:
    """List all configured MCP servers and their status."""
    logger.info("MCP tool called: list_mcp_servers")
    # .model_dump() is used to convert the Pydantic model to a dict for the tool
    return management_usecase_dep.list_servers().model_dump(by_alias=True)


@mcp_server.tool
async def reload_mcp_server(
    server_name: str,
    management_usecase_dep: ServerManagementUsecaseDep,
) -> dict[str, Any]:
    """Reload a specific MCP server by name."""
    logger.info("MCP tool called: reload_mcp_server (server=%s)", server_name)
    result = await management_usecase_dep.reload_server(server_name)
    return result.model_dump(by_alias=True)


@mcp_server.tool
async def reload_all_mcp_servers(
    management_usecase_dep: ServerManagementUsecaseDep,
) -> dict[str, Any]:
    """Reload all enabled MCP servers."""
    logger.info("MCP tool called: reload_all_mcp_servers")
    result = await management_usecase_dep.reload_all_servers()
    return result.model_dump(by_alias=True)


@mcp_server.tool
def get_mcp_server_functions(
    server_name: str,
    management_usecase_dep: ServerManagementUsecaseDep,
) -> list[str]:
    """Get list of available functions for a specific MCP server."""
    logger.info("MCP tool called: get_mcp_server_functions (server=%s)", server_name)
    return management_usecase_dep.get_server_functions(server_name)


@mcp_server.tool
def get_available_mcp_servers(
    management_usecase_dep: ServerManagementUsecaseDep,
) -> list[str]:
    """Get list of all connected MCP server names."""
    logger.info("MCP tool called: get_available_mcp_servers")
    return management_usecase_dep.get_available_servers()


@mcp_server.tool
def list_available_models(
    management_usecase_dep: ServerManagementUsecaseDep,
) -> dict[str, Any]:
    """List all available LLM models configured in this container."""
    logger.info("MCP tool 'list_available_models' called")
    return management_usecase_dep.list_available_models()


@mcp_server.tool
def get_server_capabilities(
    management_usecase_dep: ServerManagementUsecaseDep,
) -> dict[str, Any]:
    """Get comprehensive capability information for this container."""
    logger.info("MCP tool 'get_server_capabilities' called")
    return management_usecase_dep.get_server_capabilities()


# --- MCP Resources ---


@mcp_server.resource("config://app")
def get_app_config(
    management_usecase_dep: ServerManagementUsecaseDep,
) -> dict[str, Any]:
    """Get application configuration information."""
    logger.info("MCP resource accessed: config://app")
    return management_usecase_dep.get_app_config()


@mcp_server.resource("health://system")
def get_system_health(
    management_usecase_dep: ServerManagementUsecaseDep,
) -> dict[str, Any]:
    """Get system health status."""
    logger.info("MCP resource accessed: health://system")
    return management_usecase_dep.get_system_health()
