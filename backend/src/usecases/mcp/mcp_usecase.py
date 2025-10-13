"""Use cases for MCP (Model Context Protocol) related operations."""

from __future__ import annotations

import tomllib
from uuid import uuid4

from src.config import settings
from src.core.exceptions import ServiceUnavailableError
from src.core.logging import get_logger
from src.integrations.llm import ConversationAgentFactory
from src.integrations.mcp import manager as mcp_manager_module  # Keep for type hinting
from src.integrations.mcp.config import mcp_settings
from src.models.conversation import ConversationMessage, ConversationRequest
from src.models.mcp import (
    ListMCPServersResponse,
    MCPServerInfo,
    ReloadAllMCPServersResponse,
    ReloadMCPServerResponse,
)
from src.models.mcp_tools import (
    AppConfigResponse,
    ChatCapability,
    EnvironmentInfo,
    GetServerCapabilitiesResponse,
    ListAvailableModelsResponse,
    LLMModelInfo,
    MCPChatResponse,
    MCPServersCapability,
    ResourceInfo,
    ServerCapabilities,
    SystemHealthResponse,
)
from src.shared.exceptions import (
    MCPServerDisabledError,
    MCPServerNotFoundError,
    MCPServerReloadError,
)
from src.usecases.conversation import ConversationUsecase

logger = get_logger(__name__)


class MCPServerManagementUsecase:
    """Use cases for managing MCP servers and system capabilities."""

    def __init__(
        self,
        mcp_manager: mcp_manager_module.MCPManager,
        agent_factory: ConversationAgentFactory,
    ) -> None:
        self.mcp_manager = mcp_manager
        self.agent_factory = agent_factory

    def list_servers(self) -> ListMCPServersResponse:
        """List all configured MCP servers and their status."""
        status = self.mcp_manager.get_system_status()
        servers = [
            MCPServerInfo(
                name=name,
                description=info.get("description"),
                connected=bool(info.get("connected")),
                enabled=bool(info.get("enabled")),
                function_count=int(info.get("function_count", 0)),
                functions=info.get("functions", []),
            )
            for name, info in status.get("servers", {}).items()
        ]
        return ListMCPServersResponse(
            initialized=bool(status.get("initialized", False)),
            servers=servers,
        )

    async def reload_server(self, server_name: str) -> ReloadMCPServerResponse:
        """Reload a specific MCP server by name."""
        logger.info("Executing use case to reload MCP server '%s'", server_name)
        try:
            return await self.mcp_manager.reload_server(server_name)
        except (
            MCPServerNotFoundError,
            MCPServerDisabledError,
            MCPServerReloadError,
        ) as e:
            logger.warning("MCP server reload failed validation: %s", e)
            # For tools, it's better to return a structured response than to raise
            # an HTTP exception that the tool caller may not understand.
            return ReloadMCPServerResponse(
                server_name=server_name,
                success=False,
                message=str(e),
                function_count=0,
            )

    async def reload_all_servers(self) -> ReloadAllMCPServersResponse:
        """Reload all enabled MCP servers."""
        logger.info("Executing use case to reload all MCP servers")
        return await self.mcp_manager.reload_all_servers()

    def get_server_functions(self, server_name: str) -> list[str]:
        """Get list of available functions for a specific MCP server."""
        return list(self.mcp_manager.get_functions_for_server(server_name).keys())

    def get_available_servers(self) -> list[str]:
        """Get list of all connected MCP server names."""
        return self.mcp_manager.get_available_servers()

    def get_app_config(self) -> AppConfigResponse:
        """Get application configuration information."""
        return AppConfigResponse(
            environment=settings.environment,
            host=settings.host,
            port=settings.port,
            enable_mcp_system=mcp_settings.enable_mcp_system,
            cors_origins=settings.cors_origins,
        )

    def get_system_health(self) -> SystemHealthResponse:
        """Get system health status."""
        return SystemHealthResponse(
            status="healthy",
            mcp_initialized=self.mcp_manager.is_initialized(),
            available_servers=self.mcp_manager.get_available_servers(),
        )

    def list_available_models(self) -> ListAvailableModelsResponse:
        """List all available LLM models configured in this container."""
        try:
            all_models = self.agent_factory.get_available_models()
            active_model_key = self.agent_factory.get_active_model_key()

            models_info = [
                LLMModelInfo(
                    key=model_config.key,
                    name=model_config.metadata.get("display_name", model_config.key),
                    provider=model_config.provider,
                    model_id=model_config.model_id,
                    supports_streaming=model_config.supports_streaming,
                    base_url=model_config.base_url,
                )
                for model_config in all_models
            ]

            return ListAvailableModelsResponse(
                models=models_info,
                active_model=active_model_key,
                total_count=len(models_info),
                error=None,
            )
        except Exception as exc:
            logger.error("Failed to list models: %s", exc, exc_info=True)
            return ListAvailableModelsResponse(
                models=[],
                active_model="unknown",
                total_count=0,
                error=f"Failed to retrieve available LLM models: {exc}",
            )

    def get_server_capabilities(self) -> GetServerCapabilitiesResponse:
        """Get comprehensive capability information for this container."""
        try:
            models_data = self.list_available_models()
            mcp_info = self.mcp_manager.get_system_status()

            try:
                with open("pyproject.toml", "rb") as f:
                    pyproject = tomllib.load(f)
                version = pyproject["project"]["version"]
            except Exception:
                version = "unknown"

            capabilities = ServerCapabilities(
                chat=ChatCapability(
                    available=True,
                    description=(
                        "Natural language chat with access to all local MCP tools"
                    ),
                    supported_models=models_data.models,
                    default_model=models_data.active_model,
                ),
                mcp_servers=MCPServersCapability(
                    initialized=mcp_info.get("initialized", False),
                    servers=mcp_info.get("servers", {}),
                    total_functions=mcp_info.get("total_functions", 0),
                ),
                resources=[
                    ResourceInfo(
                        uri="config://app",
                        description="Application configuration",
                    ),
                    ResourceInfo(
                        uri="health://system",
                        description="System health status",
                    ),
                ],
            )

            return GetServerCapabilitiesResponse(
                capabilities=capabilities,
                environment=EnvironmentInfo(
                    name=settings.environment,
                    host=settings.host,
                    port=settings.port,
                ),
                version=version,
                error=None,
            )
        except Exception as exc:
            logger.error("Failed to get server capabilities: %s", exc, exc_info=True)
            # Return a minimal response with error
            return GetServerCapabilitiesResponse(
                capabilities=ServerCapabilities(
                    chat=ChatCapability(
                        available=False,
                        description="",
                        supported_models=[],
                        default_model="unknown",
                    ),
                    mcp_servers=MCPServersCapability(
                        initialized=False,
                        servers={},
                        total_functions=0,
                    ),
                    resources=[],
                ),
                environment=EnvironmentInfo(
                    name="unknown",
                    host="unknown",
                    port=0,
                ),
                version="unknown",
                error=f"Failed to retrieve server capabilities: {exc}",
            )


class MCPChatUsecase:
    """Use case for handling chat interactions via MCP."""

    def __init__(self, agent_factory: ConversationAgentFactory) -> None:
        self.agent_factory = agent_factory

    async def chat(
        self,
        message: str,
        model_key: str | None = None,
        conversation_id: str | None = None,
        user_id: str = "peer-caller",
    ) -> MCPChatResponse:
        """
        Execute a natural language conversation through the local Agent,
        providing access to all configured MCP tools for a peer.
        """
        logger.info(
            "Executing MCP chat use case for user=%s, model=%s",
            user_id,
            model_key or "default",
        )
        try:
            usecase = ConversationUsecase(self.agent_factory)
            conv_id = conversation_id or f"peer-{uuid4()}"
            request = ConversationRequest(
                user_id=user_id,
                conversation_id=conv_id,
                model_key=model_key,
                history=[ConversationMessage(role="user", content=message)],
                tools=None,  # None triggers auto-attachment of all MCP tools
            )

            reply = await usecase.generate_reply(request)

            return MCPChatResponse(
                success=True,
                content=reply.content,
                model=reply.model_key,
                conversation_id=reply.conversation_id,
                message_id=reply.message_id,
                error=None,
            )
        except ServiceUnavailableError as e:
            logger.error(
                "MCP chat failed due to service unavailability: %s", e, exc_info=True
            )
            return MCPChatResponse(
                success=False,
                content="",
                model=model_key or "unknown",
                conversation_id=conversation_id or "unknown",
                message_id=None,
                error=e.detail,
            )
        except Exception as exc:
            logger.error(
                "An unexpected error occurred during MCP chat: %s", exc, exc_info=True
            )
            return MCPChatResponse(
                success=False,
                content="",
                model=model_key or "unknown",
                conversation_id=conversation_id or "unknown",
                message_id=None,
                error=f"An unexpected internal error occurred: {exc}",
            )
