"""Response schemas for FastMCP server tools and resources."""

from __future__ import annotations

from typing import Any

from pydantic import Field

from .base import APIBaseModel


class MCPChatResponse(APIBaseModel):
    """Response from the chat tool."""

    success: bool = Field(description="Whether the chat request was successful")
    content: str = Field(description="The assistant's response message")
    model: str = Field(description="The LLM model used for the response")
    conversation_id: str = Field(description="Unique identifier for the conversation")
    message_id: str | None = Field(
        default=None, description="Unique identifier for this message"
    )
    error: str | None = Field(default=None, description="Error message if failed")


class LLMModelInfo(APIBaseModel):
    """Information about an available LLM model."""

    key: str = Field(description="Unique key for the model")
    name: str = Field(description="Display name of the model")
    provider: str = Field(description="LLM provider (e.g., openai, ollama)")
    model_id: str = Field(description="Provider-specific model identifier")
    supports_streaming: bool = Field(
        description="Whether the model supports streaming responses"
    )
    base_url: str | None = Field(default=None, description="Base URL for the model API")


class ListAvailableModelsResponse(APIBaseModel):
    """Response from list_available_models tool."""

    models: list[LLMModelInfo] = Field(description="List of available LLM models")
    active_model: str = Field(description="Key of the currently active model")
    total_count: int = Field(description="Total number of available models")
    error: str | None = Field(default=None, description="Error message if failed")


class ChatCapability(APIBaseModel):
    """Chat capability information."""

    available: bool = Field(description="Whether chat is available")
    description: str = Field(description="Description of chat capability")
    supported_models: list[LLMModelInfo] = Field(description="List of supported models")
    default_model: str = Field(description="Default model key")


class MCPServersCapability(APIBaseModel):
    """MCP servers capability information."""

    initialized: bool = Field(description="Whether MCP system is initialized")
    servers: dict[str, Any] = Field(description="Server status information")
    total_functions: int = Field(description="Total number of available functions")


class ResourceInfo(APIBaseModel):
    """Information about a server resource."""

    uri: str = Field(description="Resource URI")
    description: str = Field(description="Resource description")


class ServerCapabilities(APIBaseModel):
    """Detailed server capabilities."""

    chat: ChatCapability = Field(description="Chat capability information")
    mcp_servers: MCPServersCapability = Field(description="MCP servers information")
    resources: list[ResourceInfo] = Field(description="Available resources")


class EnvironmentInfo(APIBaseModel):
    """Server environment information."""

    name: str = Field(description="Environment name (e.g., development, production)")
    host: str = Field(description="Server host")
    port: int = Field(description="Server port")


class GetServerCapabilitiesResponse(APIBaseModel):
    """Response from get_server_capabilities tool."""

    capabilities: ServerCapabilities = Field(
        description="Server capabilities information"
    )
    environment: EnvironmentInfo = Field(description="Environment information")
    version: str = Field(description="Server version")
    error: str | None = Field(default=None, description="Error message if failed")


class AppConfigResponse(APIBaseModel):
    """Response from config://app resource."""

    environment: str = Field(description="Environment name")
    host: str = Field(description="Server host")
    port: int = Field(description="Server port")
    enable_mcp_system: bool = Field(description="Whether MCP system is enabled")
    cors_origins: list[str] = Field(description="Allowed CORS origins")


class SystemHealthResponse(APIBaseModel):
    """Response from health://system resource."""

    status: str = Field(description="Overall system status")
    mcp_initialized: bool = Field(description="Whether MCP system is initialized")
    available_servers: list[str] = Field(description="List of available MCP servers")
