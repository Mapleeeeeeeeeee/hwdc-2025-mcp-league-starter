"""FastMCP server implementation exposing this application's capabilities."""

from __future__ import annotations

from fastmcp import FastMCP
from fastmcp.server.auth import StaticTokenVerifier

from src.config import settings
from src.core.logging import get_logger
from src.integrations.llm import ConversationAgentFactory
from src.integrations.mcp import manager as mcp_manager
from src.models import MCPToolSelection
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
        tools: list[dict] | None = None,
    ) -> MCPChatResponse:
        """呼叫此功能前，請先依序查詢
        - list_available_models
        - get_available_mcp_servers
        - get_mcp_server_functions

        才知道要使用哪個模型、請對方執行哪個伺服器的哪個函數（可以是多個）。

        此功能為主要功能，呼叫他能夠與 LLM 模型進行對話，
        並可選擇不同模型和維持對話上下文。
        如果指定 tools，則只使用指定的工具；如果不指定，則不使用任何工具。

        Args:
            message (str): 用戶的訊息內容，必填。
            model_key (str | None): 可選的 LLM 模型鍵，如果不指定則使用預設模型。
            conversation_id (str | None): 可選的對話 ID，用於維持上下文和多輪對話。
            user_id (str): 用戶 ID，預設為 "peer-caller"。
            tools (list[dict] | None): 可選的工具選擇列表，
                每個 dict 包含 'server' 和可選的 'functions'。

        Returns:
            MCPChatResponse: 包含對話回應的 Pydantic 模型，包括 AI 的回覆、對話 ID 等。
        """
        logger.info("MCP tool 'chat' called by user=%s", user_id)
        agent_factory = get_agent_factory()
        chat_usecase = MCPChatUsecase(agent_factory=agent_factory)

        # Convert tools dict to MCPToolSelection list
        tool_selections = None
        if tools:
            tool_selections = []
            for tool_dict in tools:
                selection = MCPToolSelection(
                    server=tool_dict["server"], functions=tool_dict.get("functions")
                )
                tool_selections.append(selection)

        return await chat_usecase.chat(
            message, model_key, conversation_id, user_id, tool_selections
        )

    @server.tool
    def list_mcp_servers() -> dict:
        """列出所有配置的 MCP 伺服器及其狀態。

        提供伺服器清單，包括是否啟用、連接狀態等。有助於監控和調試。

        Returns:
            dict: 包含狀態的字典，由 MCPServerManagementUsecase.list_servers() 生成。
        """
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
        """重新載入指定的 MCP 伺服器。

        如果伺服器出錯或配置改變，可以手動重新載入，而不影響其他伺服器。

        Args:
            server_name (str): 要重新載入的伺服器名稱。

        Returns:
            dict: 重新載入結果的字典，由 reload_server 生成。
        """
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
        """重新載入所有啟用的 MCP 伺服器。

        批量操作，適合全系統重置或配置更新後的同步。

        Returns:
            dict: 重新載入結果的字典，由 reload_all_servers 生成。
        """
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
        """獲取指定 MCP 伺服器的可用函數列表。

        列出某個伺服器暴露的工具或函數，讓客戶端知道可以調用什麼。

        Args:
            server_name (str): 伺服器名稱。

        Returns:
            list[str]: 函數名稱列表。
        """
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
        """獲取所有已連接 MCP 伺服器的名稱列表。

        簡單的清單，提供活躍伺服器的概覽。只返回名稱。

        Returns:
            list[str]: 伺服器名稱列表。
        """
        logger.info("MCP tool called: get_available_mcp_servers")
        mcp_manager_instance = get_mcp_manager()
        agent_factory = get_agent_factory()
        management_usecase = MCPServerManagementUsecase(
            mcp_manager=mcp_manager_instance, agent_factory=agent_factory
        )
        return management_usecase.get_available_servers()

    @server.tool
    def list_available_models() -> ListAvailableModelsResponse:
        """列出所有配置的 LLM 模型。

        提供模型清單，讓客戶端選擇適合的模型進行對話或任務。

        Returns:
            ListAvailableModelsResponse: 模型列表的 Pydantic 模型。
        """
        logger.info("MCP tool 'list_available_models' called")
        mcp_manager_instance = get_mcp_manager()
        agent_factory = get_agent_factory()
        management_usecase = MCPServerManagementUsecase(
            mcp_manager=mcp_manager_instance, agent_factory=agent_factory
        )
        return management_usecase.list_available_models()

    @server.tool
    def get_server_capabilities() -> GetServerCapabilitiesResponse:
        """獲取這個容器的綜合能力資訊。

        提供伺服器的元資料，讓客戶端了解整體功能。

        Returns:
            GetServerCapabilitiesResponse: 能力資訊的 Pydantic 模型。
        """
        logger.info("MCP tool 'get_server_capabilities' called")
        mcp_manager_instance = get_mcp_manager()
        agent_factory = get_agent_factory()
        management_usecase = MCPServerManagementUsecase(
            mcp_manager=mcp_manager_instance, agent_factory=agent_factory
        )
        return management_usecase.get_server_capabilities()

    @server.tool
    def get_app_config() -> AppConfigResponse:
        """獲取應用程式配置資訊。

        暴露配置，讓外部工具或管理員查看設定。注意可能包含敏感資訊。

        Returns:
            AppConfigResponse: 配置資訊的 Pydantic 模型。
        """
        logger.info("MCP tool 'get_app_config' called")
        mcp_manager_instance = get_mcp_manager()
        agent_factory = get_agent_factory()
        management_usecase = MCPServerManagementUsecase(
            mcp_manager=mcp_manager_instance, agent_factory=agent_factory
        )
        return management_usecase.get_app_config()

    @server.tool
    def get_system_health() -> SystemHealthResponse:
        """獲取系統健康狀態。

        監控系統健康，提供健康檢查端點。

        Returns:
            SystemHealthResponse: 健康狀態的 Pydantic 模型。
        """
        logger.info("MCP tool 'get_system_health' called")
        mcp_manager_instance = get_mcp_manager()
        agent_factory = get_agent_factory()
        management_usecase = MCPServerManagementUsecase(
            mcp_manager=mcp_manager_instance, agent_factory=agent_factory
        )
        return management_usecase.get_system_health()
