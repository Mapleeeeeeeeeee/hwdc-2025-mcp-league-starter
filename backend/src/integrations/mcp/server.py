"""FastMCP server implementation exposing this application's capabilities."""

from __future__ import annotations

from typing import Any

from fastmcp import FastMCP
from fastmcp.server.auth import StaticTokenVerifier

from src.config import settings
from src.core.logging import get_logger

logger = get_logger(__name__)

# Get authentication token from environment
# IMPORTANT: MCP_SERVER_AUTH_TOKEN is REQUIRED for security
_mcp_auth_token = settings.get_secret("MCP_SERVER_AUTH_TOKEN")
if not _mcp_auth_token:
    raise ValueError(
        "MCP_SERVER_AUTH_TOKEN environment variable is required for "
        "MCP server authentication. Please set it in your .env file or "
        "environment variables. Example: MCP_SERVER_AUTH_TOKEN=your-secure-token-here"
    )

# Create authentication provider using StaticTokenVerifier
# Maps bearer tokens to client information (client_id and scopes)
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

# Create FastMCP server instance with authentication
mcp_server = FastMCP(
    name="HWDC-2025-MCP-League",
    instructions="MCP server exposing conversation and MCP management capabilities",
    auth=auth_provider,
)


@mcp_server.tool
def list_mcp_servers() -> dict[str, Any]:
    """List all configured MCP servers and their status.

    Returns:
        Dictionary containing server information including:
        - initialized: Whether MCP system is initialized
        - servers: Dict of server name to server info
        - total_servers: Count of configured servers
        - total_functions: Total number of available MCP functions
        - available_servers: List of connected server names
    """
    from src.integrations.mcp import get_mcp_status

    logger.info("MCP tool called: list_mcp_servers")
    return get_mcp_status()


@mcp_server.tool
async def reload_mcp_server(server_name: str) -> dict[str, Any]:
    """Reload a specific MCP server by name.

    Args:
        server_name: Name of the MCP server to reload

    Returns:
        Dictionary containing:
        - server_name: Name of the server
        - success: Whether reload succeeded
        - message: Status message
        - function_count: Number of functions available after reload
    """
    from src.integrations.mcp import reload_mcp_server as _reload_server

    logger.info("MCP tool called: reload_mcp_server (server=%s)", server_name)
    result = await _reload_server(server_name)
    return {
        "server_name": result.server_name,
        "success": result.success,
        "message": result.message,
        "function_count": result.function_count,
    }


@mcp_server.tool
async def reload_all_mcp_servers() -> dict[str, Any]:
    """Reload all enabled MCP servers.

    Returns:
        Dictionary containing:
        - success: Whether any servers reloaded successfully
        - reloaded_count: Number of servers successfully reloaded
        - failed_count: Number of servers that failed to reload
        - results: List of per-server reload results
    """
    from src.integrations.mcp import reload_all_mcp_servers as _reload_all

    logger.info("MCP tool called: reload_all_mcp_servers")
    result = await _reload_all()
    return {
        "success": result.success,
        "reloaded_count": result.reloaded_count,
        "failed_count": result.failed_count,
        "results": [
            {
                "server_name": r.server_name,
                "success": r.success,
                "message": r.message,
                "function_count": r.function_count,
            }
            for r in result.results
        ],
    }


@mcp_server.tool
def get_mcp_server_functions(server_name: str) -> list[str]:
    """Get list of available functions for a specific MCP server.

    Args:
        server_name: Name of the MCP server

    Returns:
        List of function names available on the server
    """
    from src.integrations.mcp import get_mcp_server_functions as _get_functions

    logger.info("MCP tool called: get_mcp_server_functions (server=%s)", server_name)
    return _get_functions(server_name)


@mcp_server.tool
def get_available_mcp_servers() -> list[str]:
    """Get list of all connected MCP server names.

    Returns:
        List of server names that are currently connected
    """
    from src.integrations.mcp import get_available_mcp_servers as _get_servers

    logger.info("MCP tool called: get_available_mcp_servers")
    return _get_servers()


@mcp_server.resource("config://app")
def get_app_config() -> dict[str, Any]:
    """Get application configuration information.

    Returns:
        Dictionary containing:
        - environment: Current environment (dev/staging/production)
        - host: Server host
        - port: Server port
        - enable_mcp_system: Whether MCP system is enabled
        - cors_origins: Allowed CORS origins
    """
    from src.config import settings
    from src.integrations.mcp.config import mcp_settings

    logger.info("MCP resource accessed: config://app")
    return {
        "environment": settings.environment,
        "host": settings.host,
        "port": settings.port,
        "enable_mcp_system": mcp_settings.enable_mcp_system,
        "cors_origins": settings.cors_origins,
    }


@mcp_server.resource("health://system")
def get_system_health() -> dict[str, Any]:
    """Get system health status.

    Returns:
        Dictionary containing:
        - status: "healthy" or "unhealthy"
        - mcp_initialized: Whether MCP system is initialized
        - available_servers: List of connected MCP servers
    """
    from src.integrations.mcp import get_available_mcp_servers, is_mcp_initialized

    logger.info("MCP resource accessed: health://system")
    return {
        "status": "healthy",
        "mcp_initialized": is_mcp_initialized(),
        "available_servers": get_available_mcp_servers(),
    }


@mcp_server.tool
async def chat(
    message: str,
    model_key: str | None = None,
    conversation_id: str | None = None,
    user_id: str = "peer-caller",
) -> dict[str, Any]:
    """Execute natural language conversation through local Agent.

    This provides access to all configured MCP tools.

    This tool allows peer nodes to invoke this container's Agent and leverage
    all configured MCP servers (e.g., filesystem, ms365, etc.).

    Args:
        message: Natural language instruction from the user.
                 Examples: "List all files in /project directory"
                          "Count reports from last week"
        model_key: Optional LLM model to use (e.g., 'gpt-4o-mini', 'claude-3').
                  If not specified, uses the default model.
        conversation_id: Optional conversation ID for multi-turn tracking.
                        If not specified, each call is a new conversation.
        user_id: Caller identifier, defaults to "peer-caller"

    Returns:
        Dictionary containing:
        - success: bool - Whether execution succeeded
        - content: str - Agent's response content
        - model: str - Model used
        - conversation_id: str - Conversation ID
        - message_id: str - Message ID
        - error: str | None - Error message if any

    Example:
        >>> result = await chat(
        ...     message="List files in /project directory",
        ...     model_key="gpt-4o-mini"
        ... )
        >>> print(result["content"])
        "Here are the files in /project directory:
        1. report.pdf (1.2 MB)
        2. data.csv (500 KB)
        ..."
    """
    from uuid import uuid4

    from src.integrations.llm import ConversationAgentFactory
    from src.models.conversation import ConversationMessage, ConversationRequest
    from src.usecases.conversation import ConversationUsecase

    logger.info(
        "MCP tool 'chat' called by user=%s, message=%s, model=%s",
        user_id,
        message[:50] + "..." if len(message) > 50 else message,
        model_key or "default",
    )

    try:
        # Create Agent factory and usecase
        factory = ConversationAgentFactory()
        usecase = ConversationUsecase(factory)

        # Generate conversation ID if not provided
        conv_id = conversation_id or f"peer-{uuid4()}"

        # Build conversation request
        request = ConversationRequest(
            user_id=user_id,
            conversation_id=conv_id,
            model_key=model_key,
            history=[ConversationMessage(role="user", content=message)],
            tools=None,  # ⭐ None triggers auto-attach of all MCP tools
        )

        # Execute conversation
        logger.info("Executing conversation with Agent...")
        reply = await usecase.generate_reply(request)

        logger.info(
            "Chat completed successfully: conv_id=%s, response_length=%d",
            conv_id,
            len(reply.content),
        )

        return {
            "success": True,
            "content": reply.content,
            "model": reply.model_key,
            "conversation_id": reply.conversation_id,
            "message_id": reply.message_id,
            "error": None,
        }

    except Exception as exc:
        logger.error("Chat execution failed: %s", exc, exc_info=True)
        return {
            "success": False,
            "content": "",
            "model": model_key or "unknown",
            "conversation_id": conversation_id or "unknown",
            "message_id": None,
            "error": str(exc),
        }


@mcp_server.tool
def list_available_models() -> dict[str, Any]:
    """List all available LLM models configured in this container.

    Returns:
        Dictionary containing:
        - models: list[dict] - List of available models with metadata
        - active_model: str - Current default model key
        - total_count: int - Total number of models

    Example:
        >>> result = list_available_models()
        >>> print(result)
        {
          "models": [
            {
              "key": "gpt-4o-mini",
              "name": "GPT-4O-MINI",
              "provider": "openai",
              "model_id": "gpt-4o-mini",
              "supports_streaming": true,
              "base_url": null
            },
            ...
          ],
          "active_model": "gpt-4o-mini",
          "total_count": 4
        }
    """
    from src.integrations.llm import ConversationAgentFactory

    logger.info("MCP tool 'list_available_models' called")

    try:
        factory = ConversationAgentFactory()

        # Get all available models
        all_models = factory.get_available_models()

        # Get current active model
        active_model_key = factory.get_active_model_key()

        # Format model information
        models_info = []
        for model_config in all_models:
            models_info.append(
                {
                    "key": model_config.key,
                    "name": model_config.metadata.get("display_name", model_config.key),
                    "provider": model_config.provider,
                    "model_id": model_config.model_id,
                    "supports_streaming": model_config.supports_streaming,
                    "base_url": model_config.base_url,
                }
            )

        result = {
            "models": models_info,
            "active_model": active_model_key,
            "total_count": len(models_info),
        }

        logger.info(
            "Listed %d available models, active=%s",
            len(models_info),
            active_model_key,
        )

        return result

    except Exception as exc:
        logger.error("Failed to list models: %s", exc, exc_info=True)
        return {
            "models": [],
            "active_model": "unknown",
            "total_count": 0,
            "error": str(exc),
        }


@mcp_server.tool
def get_server_capabilities() -> dict[str, Any]:
    """Get comprehensive capability information for this container.

    This is a convenience tool that returns all available capabilities in one call,
    including models, MCP servers, resources, and environment information.

    Returns:
        Dictionary containing:
        - capabilities: Complete capability information
          - chat: Chat capability with supported models
          - mcp_servers: Available MCP servers and their status
          - resources: Available resources
        - environment: Environment configuration
        - version: Application version

    Example:
        >>> result = get_server_capabilities()
        >>> print(result)
        {
          "capabilities": {
            "chat": {
              "available": true,
              "description": "Natural language chat with access to all local MCP tools",
              "supported_models": [...],
              "default_model": "gpt-4o-mini"
            },
            "mcp_servers": {
              "initialized": true,
              "servers": {...},
              "total_functions": 15
            },
            "resources": [...]
          },
          "environment": {
            "name": "development",
            "host": "0.0.0.0",
            "port": 8000
          },
          "version": "2.0.0"
        }
    """
    import tomllib

    from src.integrations.llm import ConversationAgentFactory
    from src.integrations.mcp import get_mcp_status

    logger.info("MCP tool 'get_server_capabilities' called")

    try:
        # Get models information directly
        factory = ConversationAgentFactory()
        all_models = factory.get_available_models()
        active_model_key = factory.get_active_model_key()

        models_info = []
        for model_config in all_models:
            models_info.append(
                {
                    "key": model_config.key,
                    "name": model_config.metadata.get("display_name", model_config.key),
                    "provider": model_config.provider,
                    "model_id": model_config.model_id,
                    "supports_streaming": model_config.supports_streaming,
                    "base_url": model_config.base_url,
                }
            )

        # Get MCP servers information directly
        mcp_info = get_mcp_status()

        # Get version from pyproject.toml
        try:
            with open("pyproject.toml", "rb") as f:
                pyproject = tomllib.load(f)
            version = pyproject["project"]["version"]
        except Exception:
            version = "unknown"

        return {
            "capabilities": {
                "chat": {
                    "available": True,
                    "description": (
                        "Natural language chat with access to all local MCP tools"
                    ),
                    "supported_models": models_info,
                    "default_model": active_model_key,
                },
                "mcp_servers": {
                    "initialized": mcp_info.get("initialized", False),
                    "servers": mcp_info.get("servers", {}),
                    "total_functions": mcp_info.get("total_functions", 0),
                },
                "resources": [
                    {
                        "uri": "config://app",
                        "description": "Application configuration",
                    },
                    {
                        "uri": "health://system",
                        "description": "System health status",
                    },
                ],
            },
            "environment": {
                "name": settings.environment,
                "host": settings.host,
                "port": settings.port,
            },
            "version": version,
        }

    except Exception as exc:
        logger.error("Failed to get capabilities: %s", exc, exc_info=True)
        return {
            "capabilities": {},
            "environment": {},
            "version": "unknown",
            "error": str(exc),
        }
