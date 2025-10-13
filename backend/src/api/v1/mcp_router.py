"""Endpoints for managing MCP server metadata."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends
from src.core.logging import get_logger
from src.integrations.llm import ConversationAgentFactory
from src.integrations.mcp import manager as mcp_manager
from src.models.mcp import (
    ListMCPServersResponse,
    ReloadAllMCPServersResponse,
    ReloadMCPServerResponse,
)
from src.shared.response import APIResponse, create_success_response
from src.usecases.mcp.mcp_usecase import MCPServerManagementUsecase

router = APIRouter(prefix="/mcp", tags=["mcp"])
logger = get_logger(__name__)


def get_mcp_manager() -> mcp_manager.MCPManager:
    return mcp_manager.MCPManager()


def get_agent_factory() -> ConversationAgentFactory:
    return ConversationAgentFactory()


def get_server_management_usecase(
    mcp_manager_dep: Annotated[mcp_manager.MCPManager, Depends(get_mcp_manager)],
    agent_factory_dep: Annotated[ConversationAgentFactory, Depends(get_agent_factory)],
) -> MCPServerManagementUsecase:
    return MCPServerManagementUsecase(
        mcp_manager=mcp_manager_dep, agent_factory=agent_factory_dep
    )


ServerManagementUsecaseDep = Annotated[
    MCPServerManagementUsecase, Depends(get_server_management_usecase)
]


@router.get(
    "/servers",
    response_model=APIResponse[ListMCPServersResponse],
)
async def list_mcp_servers(
    usecase: ServerManagementUsecaseDep,
) -> APIResponse[ListMCPServersResponse]:
    """Return available MCP servers and their exposed functions."""
    payload = usecase.list_servers()
    return create_success_response(data=payload, message="MCP servers retrieved")


@router.post(
    "/servers:reload",
    response_model=APIResponse[ReloadAllMCPServersResponse],
)
async def reload_all_servers(
    usecase: ServerManagementUsecaseDep,
) -> APIResponse[ReloadAllMCPServersResponse]:
    """Reload all enabled MCP servers."""
    logger.info("Received request to reload all MCP servers")
    payload = await usecase.reload_all_servers()
    return create_success_response(data=payload, message="All servers reloaded")


@router.post(
    "/servers/{server_name}:reload",
    response_model=APIResponse[ReloadMCPServerResponse],
)
async def reload_server(
    server_name: str,
    usecase: ServerManagementUsecaseDep,
) -> APIResponse[ReloadMCPServerResponse]:
    """Reload a specific MCP server by name."""
    logger.info("Received request to reload MCP server '%s'", server_name)
    # The use case will raise specific exceptions (e.g., NotFoundError)
    # and the global exception handlers will convert them into the correct
    # HTTP error responses, as per the error handling documentation.
    payload = await usecase.reload_server(server_name)
    return create_success_response(
        data=payload,
        message=f"Server '{server_name}' reloaded successfully",
    )
