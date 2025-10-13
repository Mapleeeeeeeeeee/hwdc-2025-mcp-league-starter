"""Public API for model schemas."""

from .base import APIBaseModel
from .conversation import (
    ConversationMessage,
    ConversationReply,
    ConversationRequest,
    ConversationStreamChunk,
    ListModelsResponse,
    LLMModelDescriptor,
    UpsertLLMModelRequest,
)
from .mcp import (
    ListMCPServersResponse,
    MCPServerInfo,
    MCPToolSelection,
    ReloadAllMCPServersResponse,
    ReloadMCPServerResponse,
)
from .mcp_tools import (
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

__all__ = [
    # Base
    "APIBaseModel",
    # Conversation models
    "ConversationMessage",
    "ConversationReply",
    "ConversationRequest",
    "ConversationStreamChunk",
    "LLMModelDescriptor",
    "ListModelsResponse",
    "UpsertLLMModelRequest",
    # MCP management models (for REST API)
    "MCPToolSelection",
    "MCPServerInfo",
    "ListMCPServersResponse",
    "ReloadMCPServerResponse",
    "ReloadAllMCPServersResponse",
    # MCP server tool response models (for FastMCP tools)
    "AppConfigResponse",
    "ChatCapability",
    "EnvironmentInfo",
    "GetServerCapabilitiesResponse",
    "ListAvailableModelsResponse",
    "LLMModelInfo",
    "MCPChatResponse",
    "MCPServersCapability",
    "ResourceInfo",
    "ServerCapabilities",
    "SystemHealthResponse",
]
