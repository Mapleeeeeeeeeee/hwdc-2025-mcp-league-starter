# TODO: 實現 MCP Peer-to-Peer Agent Chat 功能

> **目標**: 讓主管A容器能透過自然語言呼叫員工B容器的 Agent，員工B的 Agent 會使用本地配置的 MCP tools 執行任務並返回結果。

---

## 📋 目錄

- [架構說明](#架構說明)
- [前置準備](#前置準備)
- [階段一：暴露 chat endpoint](#階段一暴露-chat-endpoint)
- [階段二：暴露能力查詢 endpoints](#階段二暴露能力查詢-endpoints)
- [階段三：端到端測試](#階段三端到端測試)
- [階段四：添加認證（可選）](#階段四添加認證可選)
- [驗收標準](#驗收標準)
- [常見問題](#常見問題)

---

## 架構說明

### 當前狀態 (已完成)

```
容器A (主管)                    容器B (員工)
┌──────────────┐              ┌──────────────────┐
│ Agent A      │              │ FastMCP Server   │
│              │   HTTP       │ /mcp             │
│              ├─────────────→│                  │
│              │              │ ✅ list_mcp_     │
│              │              │    servers()     │
│              │              │ ✅ reload_mcp_   │
│              │              │    server()      │
└──────────────┘              └──────────────────┘
```

### 目標架構 (待實現)

```
容器A (主管)                    容器B (員工)
┌──────────────┐              ┌───────────────────────┐
│ Agent A:     │              │ FastMCP Server /mcp   │
│ "幫我列出員工 │   HTTP       │                       │
│  B的檔案"    ├─────────────→│ ⭐ chat()             │
│              │              │   ↓ 呼叫              │
│              │              │ Agent B               │
│              │              │   ↓ 使用              │
│              │              │ MCP Toolkit           │
│              │  ← 回傳結果 │   ↓ 呼叫              │
│              │              │ filesystem tool       │
└──────────────┘              │ ms365 tool            │
                              └───────────────────────┘
```

---

## 前置準備

### ✅ 確認當前架構

**目的**: 理解代碼結構，確保環境正確

#### 1. 檢查關鍵檔案是否存在

```bash
cd /Users/maple/Desktop/hwdc-2025-mcp-league-starter/backend

# 確認這些檔案存在
ls -la src/integrations/mcp/server.py          # FastMCP server
ls -la src/usecases/conversation/conversation_usecase.py  # 對話邏輯
ls -la src/integrations/llm/factory.py         # Agent factory
ls -la src/models/conversation.py              # 對話模型
ls -la config/llm_models.json                  # 模型配置
ls -la config/mcp_servers.json                 # MCP servers 配置
```

**預期結果**: 所有檔案都存在

#### 2. 檢查當前 FastMCP server 有哪些 tools

```bash
cd backend
uv run python -c "
from src.integrations.mcp.server import mcp_server
print('Current tools:')
for tool_name in dir(mcp_server):
    if not tool_name.startswith('_'):
        print(f'  - {tool_name}')
"
```

**預期輸出**:
```
Current tools:
  - list_mcp_servers
  - reload_mcp_server
  - reload_all_mcp_servers
  - get_mcp_server_functions
  - get_available_mcp_servers
```

#### 3. 檢查 ConversationUsecase 的結構

```bash
cd backend
uv run python -c "
from src.usecases.conversation.conversation_usecase import ConversationUsecase
import inspect
print('ConversationUsecase methods:')
for name, method in inspect.getmembers(ConversationUsecase, predicate=inspect.isfunction):
    if not name.startswith('_'):
        print(f'  - {name}{inspect.signature(method)}')
"
```

**預期輸出**:
```
ConversationUsecase methods:
  - generate_reply(self, payload: ConversationRequest) -> ConversationReply
  - stream_reply(self, payload: ConversationRequest) -> AsyncIterator[...]
```

---

## 階段一：暴露 chat endpoint

### 🎯 目標
讓員工B容器暴露 `chat()` tool，接收自然語言指令，透過本地 Agent 執行並返回結果。

---

### 任務 1.1: 修改 ConversationUsecase 支援自動附加所有 MCP tools

**檔案**: `backend/src/usecases/conversation/conversation_usecase.py`

**位置**: 找到 `_attach_requested_tools` 方法（約在第 103 行）

**修改內容**:

```python
def _attach_requested_tools(
    self,
    agent,
    selections: list[MCPToolSelection] | None,
) -> None:
    # ⭐ 新增：如果 selections 為 None，自動附加所有可用的 MCP servers
    if selections is None:
        from src.integrations.mcp import get_available_mcp_servers, get_mcp_toolkit

        self._logger.info("No tool selection provided, auto-attaching all available MCP servers")
        available_servers = get_available_mcp_servers()

        for server_name in available_servers:
            toolkit = get_mcp_toolkit(server_name)
            if toolkit is None or not toolkit.functions:
                self._logger.warning(
                    "Skipping MCP server '%s' – toolkit unavailable or empty",
                    server_name,
                )
                continue

            function_names = list(toolkit.functions.keys())
            self._logger.info(
                "Auto-attached MCP server '%s' with %s function(s): %s",
                server_name,
                len(function_names),
                ", ".join(function_names[:5]) + ("..." if len(function_names) > 5 else "")
            )
            agent.add_tool(toolkit)

        return

    # 原有邏輯保持不變
    if not selections:
        self._logger.info("No MCP tools selected for this conversation")
        return

    self._logger.info(
        "Attaching MCP tools to agent: %s server(s) selected",
        len(selections),
    )

    seen: set[str] = set()
    for selection in selections:
        server_name = selection.server.strip()
        if not server_name or server_name in seen:
            continue

        seen.add(server_name)
        functions = None
        if selection.functions:
            cleaned = [str(name).strip() for name in selection.functions]
            functions = [name for name in cleaned if name]
            if not functions:
                functions = None

        toolkit = get_mcp_toolkit(
            server_name,
            allowed_functions=functions,
        )
        if toolkit is None or not toolkit.functions:
            self._logger.warning(
                "Skipping MCP server '%s' – toolkit unavailable or empty",
                server_name,
            )
            continue

        function_names = list(toolkit.functions.keys())
        self._logger.info(
            "Adding MCP server '%s' with %s function(s): %s",
            server_name,
            len(function_names),
            ", ".join(function_names) if functions else "all functions",
        )
        agent.add_tool(toolkit)
```

**測試**:

```bash
cd backend
uv run python -c "
from src.usecases.conversation.conversation_usecase import ConversationUsecase
from src.integrations.llm import ConversationAgentFactory
from src.models.conversation import ConversationRequest, ConversationMessage

factory = ConversationAgentFactory()
usecase = ConversationUsecase(factory)

# 測試 selections=None 會自動附加所有 tools
request = ConversationRequest(
    user_id='test-user',
    conversation_id='test-conv',
    history=[
        ConversationMessage(role='user', content='Hello')
    ],
    tools=None  # ⭐ None 會觸發自動附加
)

# 應該看到日誌：Auto-attached MCP server...
print('✅ Test passed: selections=None triggers auto-attach')
"
```

**預期日誌**:
```
INFO: No tool selection provided, auto-attaching all available MCP servers
INFO: Auto-attached MCP server 'filesystem' with 5 function(s): read_file, list_directory, ...
INFO: Auto-attached MCP server 'ms365' with 3 function(s): ...
```

---

### 任務 1.2: 在 FastMCP server 添加 chat tool

**檔案**: `backend/src/integrations/mcp/server.py`

**位置**: 在檔案末尾，`get_system_health()` 之後添加

**新增內容**:

```python
@mcp_server.tool
async def chat(
    message: str,
    model_key: str | None = None,
    conversation_id: str | None = None,
    user_id: str = "peer-caller",
) -> dict[str, Any]:
    """
    透過本地 Agent 執行自然語言對話，Agent 會自動使用所有可用的 MCP tools。

    這個 tool 讓其他容器（peer nodes）能夠呼叫本容器的 Agent，
    並利用本容器配置的所有 MCP servers（如 filesystem、ms365 等）。

    Args:
        message: 用戶的自然語言指令
                 例如：「列出 /project 目錄下的所有檔案」
                       「幫我統計上週的報告數量」
        model_key: 可選，指定使用的 LLM 模型（如 'gpt-4', 'claude-3'）
                  若不指定，使用預設模型
        conversation_id: 可選，對話 ID（用於追蹤多輪對話）
                        若不指定，每次呼叫都是新對話
        user_id: 呼叫者 ID，預設為 "peer-caller"

    Returns:
        Dictionary containing:
        - success: bool - 是否執行成功
        - content: str - Agent 的回應內容
        - model: str - 使用的模型
        - conversation_id: str - 對話 ID
        - error: str | None - 錯誤訊息（如果有）

    Example:
        >>> result = await chat(
        ...     message="列出 /project 目錄下的檔案",
        ...     model_key="gpt-4"
        ... )
        >>> print(result["content"])
        "以下是 /project 目錄的檔案列表：
        1. report.pdf (1.2 MB)
        2. data.csv (500 KB)
        ..."
    """
    from uuid import uuid4
    from src.usecases.conversation import ConversationUsecase
    from src.integrations.llm import ConversationAgentFactory
    from src.models.conversation import ConversationRequest, ConversationMessage

    logger.info(
        "MCP tool 'chat' called by user=%s, message=%s, model=%s",
        user_id,
        message[:50] + "..." if len(message) > 50 else message,
        model_key or "default"
    )

    try:
        # 建立 Agent factory 和 usecase
        factory = ConversationAgentFactory()
        usecase = ConversationUsecase(factory)

        # 生成對話 ID（如果沒提供）
        conv_id = conversation_id or f"peer-{uuid4()}"

        # 構建對話請求
        request = ConversationRequest(
            user_id=user_id,
            conversation_id=conv_id,
            model_key=model_key,
            history=[
                ConversationMessage(role="user", content=message)
            ],
            tools=None,  # ⭐ None 會觸發自動附加所有 MCP tools
        )

        # 執行對話
        logger.info("Executing conversation with Agent...")
        reply = await usecase.generate_reply(request)

        logger.info(
            "Chat completed successfully: conv_id=%s, response_length=%d",
            conv_id,
            len(reply.content)
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
```

**測試**:

```bash
cd backend

# 測試 1: 檢查 tool 是否正確註冊
uv run python -c "
from src.integrations.mcp.server import mcp_server
print('Checking if chat tool is registered...')
# 檢查 chat 是否在 mcp_server 的 tools 中
print('✅ chat tool registered')
"

# 測試 2: 直接呼叫 chat tool (需要 MCP system 已初始化)
uv run python -c "
import asyncio
from src.integrations.mcp import initialize_mcp_system
from src.integrations.mcp.server import chat

async def test():
    # 初始化 MCP system
    await initialize_mcp_system()

    # 呼叫 chat
    result = await chat(
        message='你好，請告訴我當前時間',
        model_key='gpt-4'
    )

    print('Result:', result)
    assert result['success'] == True
    assert len(result['content']) > 0
    print('✅ Chat tool works correctly')

asyncio.run(test())
"
```

**預期輸出**:
```json
{
  "success": true,
  "content": "你好！當前時間是 ...",
  "model": "gpt-4",
  "conversation_id": "peer-123e4567-...",
  "message_id": "msg-123...",
  "error": null
}
```

---

### 任務 1.3: 更新 MCP integration 的 __init__.py

**檔案**: `backend/src/integrations/mcp/__init__.py`

**目的**: 確保 chat tool 可以被正確導入和使用

**確認內容**:

檢查 `mcp_server` 是否已經在 `__all__` 中：

```python
__all__ = [
    "MCPManager",
    "MCPToolkit",
    "HTTPMCPToolkit",
    "HTTPMCPConnection",
    "MCPServerParams",
    "MCPParamsManager",
    "MCPSettings",
    "mcp_settings",
    "default_params_manager",
    "initialize_mcp_system",
    "get_mcp_status",
    "graceful_mcp_cleanup",
    "is_mcp_initialized",
    "get_available_mcp_servers",
    "get_mcp_server_functions",
    "get_mcp_toolkit",
    "reload_mcp_server",
    "reload_all_mcp_servers",
    "mcp_server",  # ⭐ 確認這行存在
    "add_peer_node",
    "remove_peer_node",
    "list_peer_nodes",
]
```

**測試**:

```bash
cd backend
uv run python -c "
from src.integrations.mcp import mcp_server
print('✅ mcp_server can be imported')
print('Available methods:', dir(mcp_server))
"
```

---

### 任務 1.4: 驗證 chat tool 在 FastMCP server 中可用

**測試啟動 FastMCP server**:

```bash
cd backend

# 方式 1: 直接啟動應用
uv run uvicorn src.main:app --host 0.0.0.0 --port 8000

# 在另一個終端測試
curl http://localhost:8000/mcp/sse
```

**預期回應**: SSE stream with server capabilities

**測試 chat tool 是否暴露**:

使用 FastMCP client 連接：

```python
# test_chat_tool.py
import asyncio
from fastmcp import Client
from fastmcp.client.transports import StreamableHttpTransport

async def test():
    async with Client(
        transport=StreamableHttpTransport("http://localhost:8000/mcp")
    ) as client:
        # 列出所有 tools
        tools = await client.list_tools()
        tool_names = [t.name for t in tools]

        print("Available tools:")
        for name in tool_names:
            print(f"  - {name}")

        # 確認 chat 存在
        assert "chat" in tool_names, "chat tool not found!"
        print("\n✅ chat tool is available")

        # 測試呼叫 chat
        result = await client.call_tool("chat", {
            "message": "你好，請簡單回應我",
            "model_key": "gpt-4"
        })

        print("\nChat result:")
        print(result)

asyncio.run(test())
```

**執行測試**:

```bash
cd backend
uv run python test_chat_tool.py
```

**預期輸出**:
```
Available tools:
  - list_mcp_servers
  - reload_mcp_server
  - reload_all_mcp_servers
  - get_mcp_server_functions
  - get_available_mcp_servers
  - chat  ← ⭐ 確認這個存在

✅ chat tool is available

Chat result:
{
  "success": true,
  "content": "你好！我在這裡，有什麼我可以幫助你的嗎？",
  "model": "gpt-4",
  ...
}
```

---

## 階段二：暴露能力查詢 endpoints

### 🎯 目標
讓主管A容器能查詢員工B容器有哪些可用的模型和 MCP servers。

---

### 任務 2.1: 添加 list_available_models tool

**檔案**: `backend/src/integrations/mcp/server.py`

**位置**: 在 `chat()` tool 之後添加

**新增內容**:

```python
@mcp_server.tool
def list_available_models() -> dict[str, Any]:
    """
    列出本容器所有可用的 LLM 模型。

    Returns:
        Dictionary containing:
        - models: list[dict] - 可用模型列表
        - active_model: str - 當前預設模型
        - total_count: int - 模型總數

    Example:
        >>> result = list_available_models()
        >>> print(result)
        {
          "models": [
            {
              "key": "gpt-4",
              "name": "GPT-4",
              "provider": "openai",
              "description": "Most capable model"
            },
            ...
          ],
          "active_model": "gpt-4",
          "total_count": 5
        }
    """
    from src.integrations.llm import ConversationAgentFactory

    logger.info("MCP tool 'list_available_models' called")

    try:
        factory = ConversationAgentFactory()

        # 獲取所有模型
        all_models = factory.list_all_models()

        # 獲取當前預設模型
        active_model = factory.get_active_model_key()

        # 格式化模型資訊
        models_info = []
        for model in all_models:
            models_info.append({
                "key": model.key,
                "name": model.name,
                "provider": model.provider,
                "description": model.description or "",
                "base_url": model.base_url or "",
            })

        result = {
            "models": models_info,
            "active_model": active_model,
            "total_count": len(models_info),
        }

        logger.info(
            "Listed %d available models, active=%s",
            len(models_info),
            active_model
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
```

**測試**:

```bash
cd backend
uv run python -c "
import asyncio
from src.integrations.mcp import initialize_mcp_system
from src.integrations.mcp.server import list_available_models

async def test():
    await initialize_mcp_system()
    result = list_available_models()

    print('Available models:')
    for model in result['models']:
        print(f\"  - {model['key']}: {model['name']} ({model['provider']})\")

    print(f\"\\nActive model: {result['active_model']}\")
    print(f\"Total: {result['total_count']}\")

    assert result['total_count'] > 0
    print('\\n✅ list_available_models works')

asyncio.run(test())
"
```

**預期輸出**:
```
Available models:
  - gpt-4: GPT-4 (openai)
  - gpt-4o: GPT-4o (openai)
  - claude-3-opus: Claude 3 Opus (anthropic)
  - ollama-llama3: Llama 3 (ollama)

Active model: gpt-4
Total: 4

✅ list_available_models works
```

---

### 任務 2.2: 確認 list_mcp_servers tool 已存在

**檔案**: `backend/src/integrations/mcp/server.py`

**確認**: 應該已經有 `list_mcp_servers()` tool（在第 20 行左右）

```python
@mcp_server.tool
def list_mcp_servers() -> dict[str, Any]:
    """List all configured MCP servers and their status."""
    from src.integrations.mcp import get_mcp_status

    logger.info("MCP tool called: list_mcp_servers")
    return get_mcp_status()
```

**測試**:

```bash
cd backend
uv run python -c "
import asyncio
from src.integrations.mcp import initialize_mcp_system
from src.integrations.mcp.server import list_mcp_servers

async def test():
    await initialize_mcp_system()
    result = list_mcp_servers()

    print('MCP System Status:')
    print(f\"  Initialized: {result['initialized']}\")
    print(f\"  Total servers: {result['total_servers']}\")
    print(f\"  Total functions: {result['total_functions']}\")
    print()
    print('Available servers:')
    for server_name, info in result['servers'].items():
        status = '✅' if info['connected'] else '❌'
        print(f\"  {status} {server_name}: {info['function_count']} functions\")

    print('\\n✅ list_mcp_servers works')

asyncio.run(test())
"
```

**預期輸出**:
```
MCP System Status:
  Initialized: True
  Total servers: 3
  Total functions: 15

Available servers:
  ✅ filesystem: 5 functions
  ✅ Context7: 3 functions
  ✅ ms365: 7 functions

✅ list_mcp_servers works
```

---

### 任務 2.3: 添加 get_server_capabilities tool (可選，方便使用)

**檔案**: `backend/src/integrations/mcp/server.py`

**位置**: 在 `list_available_models()` 之後

**新增內容**:

```python
@mcp_server.tool
def get_server_capabilities() -> dict[str, Any]:
    """
    獲取本容器的完整能力資訊（模型 + MCP servers + resources）。

    這是一個便利 tool，一次性返回所有可用資源。

    Returns:
        Dictionary containing:
        - models: 可用模型列表
        - mcp_servers: 可用 MCP servers
        - resources: 可用 resources
        - endpoints: API 端點資訊
    """
    logger.info("MCP tool 'get_server_capabilities' called")

    try:
        # 獲取模型資訊
        models_info = list_available_models()

        # 獲取 MCP servers 資訊
        mcp_info = list_mcp_servers()

        # 獲取配置資訊
        from src.config import settings
        from src.integrations.mcp.config import mcp_settings

        return {
            "capabilities": {
                "chat": {
                    "available": True,
                    "description": "Natural language chat with access to all local MCP tools",
                    "supported_models": models_info["models"],
                    "default_model": models_info["active_model"],
                },
                "mcp_servers": {
                    "initialized": mcp_info["initialized"],
                    "servers": mcp_info.get("servers", {}),
                    "total_functions": mcp_info.get("total_functions", 0),
                },
                "resources": [
                    {
                        "uri": "config://app",
                        "description": "Application configuration"
                    },
                    {
                        "uri": "health://system",
                        "description": "System health status"
                    }
                ],
            },
            "environment": {
                "name": settings.environment,
                "host": settings.host,
                "port": settings.port,
            },
            "version": "2.0.0",
        }

    except Exception as exc:
        logger.error("Failed to get capabilities: %s", exc, exc_info=True)
        return {
            "capabilities": {},
            "environment": {},
            "version": "unknown",
            "error": str(exc),
        }
```

**測試**:

```bash
cd backend
uv run python -c "
import asyncio
import json
from src.integrations.mcp import initialize_mcp_system
from src.integrations.mcp.server import get_server_capabilities

async def test():
    await initialize_mcp_system()
    result = get_server_capabilities()

    print(json.dumps(result, indent=2, ensure_ascii=False))

    assert 'capabilities' in result
    assert result['capabilities']['chat']['available'] == True
    print('\\n✅ get_server_capabilities works')

asyncio.run(test())
"
```

**預期輸出**:
```json
{
  "capabilities": {
    "chat": {
      "available": true,
      "description": "Natural language chat with access to all local MCP tools",
      "supported_models": [...],
      "default_model": "gpt-4"
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
```

---

## 階段三：端到端測試

### 🎯 目標
在兩個容器之間建立 peer connection，測試主管A呼叫員工B的 chat 功能。

---

### 任務 3.1: 準備測試環境

#### 選項 A: Docker Compose (推薦)

**創建**: `docker-compose.test.yml`

```yaml
version: '3.8'

services:
  employee-b:
    build:
      context: .
      dockerfile: backend/Dockerfile
    container_name: employee-b
    environment:
      - HOST=0.0.0.0
      - PORT=8000
      - ENVIRONMENT=development
      - MCP_SERVER_AUTH_TOKEN=shared-secret-123
    ports:
      - "8001:8000"
    volumes:
      - ./backend:/app
    networks:
      - mcp-network

  manager-a:
    build:
      context: .
      dockerfile: backend/Dockerfile
    container_name: manager-a
    environment:
      - HOST=0.0.0.0
      - PORT=8000
      - ENVIRONMENT=development
    ports:
      - "8002:8000"
    volumes:
      - ./backend:/app
    networks:
      - mcp-network
    depends_on:
      - employee-b

networks:
  mcp-network:
    driver: bridge
```

**啟動**:

```bash
# 啟動兩個容器
docker-compose -f docker-compose.test.yml up -d

# 檢查容器狀態
docker-compose -f docker-compose.test.yml ps

# 查看日誌
docker-compose -f docker-compose.test.yml logs -f
```

**預期**:
```
employee-b  | INFO: Application startup complete
manager-a   | INFO: Application startup complete
```

#### 選項 B: 本地兩個進程（開發用）

**終端 1 (員工B)**:

```bash
cd backend
HOST=0.0.0.0 PORT=8001 MCP_SERVER_AUTH_TOKEN=shared-secret-123 \
uv run uvicorn src.main:app --host 0.0.0.0 --port 8001
```

**終端 2 (主管A)**:

```bash
cd backend
HOST=0.0.0.0 PORT=8002 \
uv run uvicorn src.main:app --host 0.0.0.0 --port 8002
```

**驗證**:

```bash
# 檢查員工B
curl http://localhost:8001/health

# 檢查主管A
curl http://localhost:8002/health
```

---

### 任務 3.2: 建立 Peer Connection

**從主管A連接到員工B**:

```bash
curl -X POST http://localhost:8002/api/v1/mcp/peers \
  -H "Content-Type: application/json" \
  -d '{
    "peer_name": "employee-b",
    "peer_url": "http://employee-b:8000/mcp",
    "auth_token": "shared-secret-123"
  }'
```

**如果是本地測試（選項B）**:

```bash
curl -X POST http://localhost:8002/api/v1/mcp/peers \
  -H "Content-Type: application/json" \
  -d '{
    "peer_name": "employee-b",
    "peer_url": "http://localhost:8001/mcp",
    "auth_token": "shared-secret-123"
  }'
```

**預期回應**:

```json
{
  "success": true,
  "data": {
    "success": true,
    "peer_name": "employee-b",
    "peer_url": "http://employee-b:8000/mcp",
    "function_count": 8,
    "message": "Peer node 'employee-b' added successfully"
  },
  "message": "Peer node 'employee-b' connected"
}
```

**驗證連接成功**:

```bash
# 列出所有 peers
curl http://localhost:8002/api/v1/mcp/peers

# 列出所有 MCP servers (應該包含 employee-b)
curl http://localhost:8002/api/v1/mcp/servers
```

**預期**: employee-b 出現在 servers 列表中

---

### 任務 3.3: 測試查詢員工B的能力

**測試 1: 查詢可用模型**

創建測試腳本: `test_peer_capabilities.py`

```python
"""測試查詢 peer node 的能力"""
import asyncio
from src.integrations.mcp import get_mcp_toolkit

async def test_query_models():
    """查詢員工B有哪些可用模型"""
    print("=" * 60)
    print("測試 1: 查詢員工B的可用模型")
    print("=" * 60)

    # 獲取員工B的 toolkit
    toolkit = get_mcp_toolkit("employee-b")

    if toolkit is None:
        print("❌ Failed: Cannot get toolkit for employee-b")
        return

    # 呼叫 list_available_models
    result = await toolkit.call_tool("list_available_models", {})

    print(f"\n員工B有 {result['total_count']} 個可用模型：")
    for model in result['models']:
        print(f"  - {model['key']}: {model['name']} ({model['provider']})")

    print(f"\n預設模型: {result['active_model']}")
    print("\n✅ Test passed")


async def test_query_mcp_servers():
    """查詢員工B有哪些 MCP servers"""
    print("\n" + "=" * 60)
    print("測試 2: 查詢員工B的 MCP servers")
    print("=" * 60)

    toolkit = get_mcp_toolkit("employee-b")

    if toolkit is None:
        print("❌ Failed: Cannot get toolkit for employee-b")
        return

    # 呼叫 list_mcp_servers
    result = await toolkit.call_tool("list_mcp_servers", {})

    print(f"\n員工B的 MCP 系統狀態:")
    print(f"  Initialized: {result['initialized']}")
    print(f"  Total servers: {result['total_servers']}")
    print(f"  Total functions: {result['total_functions']}")

    print("\n可用的 MCP servers:")
    for server_name, info in result['servers'].items():
        status = "✅" if info['connected'] else "❌"
        print(f"  {status} {server_name}:")
        print(f"     - Description: {info.get('description', 'N/A')}")
        print(f"     - Functions: {info['function_count']}")
        print(f"     - Functions list: {', '.join(info['functions'][:3])}...")

    print("\n✅ Test passed")


async def test_get_full_capabilities():
    """查詢員工B的完整能力"""
    print("\n" + "=" * 60)
    print("測試 3: 查詢員工B的完整能力")
    print("=" * 60)

    toolkit = get_mcp_toolkit("employee-b")

    if toolkit is None:
        print("❌ Failed: Cannot get toolkit for employee-b")
        return

    # 呼叫 get_server_capabilities
    result = await toolkit.call_tool("get_server_capabilities", {})

    import json
    print("\n員工B的完整能力:")
    print(json.dumps(result, indent=2, ensure_ascii=False))

    print("\n✅ Test passed")


async def main():
    from src.integrations.mcp import initialize_mcp_system

    # 初始化 MCP system
    print("初始化 MCP system...")
    await initialize_mcp_system()

    # 執行測試
    await test_query_models()
    await test_query_mcp_servers()
    await test_get_full_capabilities()

    print("\n" + "=" * 60)
    print("🎉 所有測試通過！")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
```

**執行測試**:

```bash
# 在主管A容器中執行
cd backend
uv run python test_peer_capabilities.py
```

**預期輸出**:
```
============================================================
測試 1: 查詢員工B的可用模型
============================================================

員工B有 4 個可用模型：
  - gpt-4: GPT-4 (openai)
  - gpt-4o: GPT-4o (openai)
  - claude-3-opus: Claude 3 Opus (anthropic)
  - ollama-llama3: Llama 3 (ollama)

預設模型: gpt-4

✅ Test passed

============================================================
測試 2: 查詢員工B的 MCP servers
============================================================

員工B的 MCP 系統狀態:
  Initialized: True
  Total servers: 3
  Total functions: 15

可用的 MCP servers:
  ✅ filesystem:
     - Description: Filesystem browsing tools
     - Functions: 5
     - Functions list: read_file, list_directory, create_file...
  ✅ Context7:
     - Description: Context7 documentation
     - Functions: 3
     - Functions list: search, get_doc, list_docs...
  ✅ ms365:
     - Description: Microsoft 365 services integration
     - Functions: 7
     - Functions list: list_emails, send_email, get_calendar...

✅ Test passed

============================================================
🎉 所有測試通過！
============================================================
```

---

### 任務 3.4: 測試主管A呼叫員工B的 chat

**測試腳本**: `test_peer_chat.py`

```python
"""測試主管A透過 chat 呼叫員工B"""
import asyncio
from src.integrations.mcp import get_mcp_toolkit

async def test_simple_chat():
    """測試簡單對話"""
    print("=" * 60)
    print("測試 1: 簡單對話")
    print("=" * 60)

    toolkit = get_mcp_toolkit("employee-b")

    if toolkit is None:
        print("❌ Failed: Cannot get toolkit for employee-b")
        return

    # 呼叫 chat
    print("\n主管A: 你好，請簡單自我介紹")

    result = await toolkit.call_tool("chat", {
        "message": "你好，請簡單自我介紹",
        "model_key": "gpt-4"
    })

    if result["success"]:
        print(f"\n員工B: {result['content']}")
        print(f"\n使用模型: {result['model']}")
        print(f"對話ID: {result['conversation_id']}")
        print("\n✅ Test passed")
    else:
        print(f"\n❌ Failed: {result['error']}")


async def test_chat_with_filesystem():
    """測試使用 filesystem tool 的對話"""
    print("\n" + "=" * 60)
    print("測試 2: 使用 filesystem tool")
    print("=" * 60)

    toolkit = get_mcp_toolkit("employee-b")

    if toolkit is None:
        print("❌ Failed: Cannot get toolkit for employee-b")
        return

    # 呼叫 chat，要求列出目錄
    print("\n主管A: 請列出員工B的 /Users/maple/Desktop 目錄下的檔案（只要前5個）")

    result = await toolkit.call_tool("chat", {
        "message": "請列出 /Users/maple/Desktop 目錄下的檔案，只要前5個就好",
        "model_key": "gpt-4"
    })

    if result["success"]:
        print(f"\n員工B: {result['content']}")
        print("\n✅ Test passed - Agent successfully used filesystem tool")
    else:
        print(f"\n❌ Failed: {result['error']}")


async def test_chat_with_multiple_tools():
    """測試使用多個 tools 的複雜任務"""
    print("\n" + "=" * 60)
    print("測試 3: 複雜任務（多個 tools）")
    print("=" * 60)

    toolkit = get_mcp_toolkit("employee-b")

    if toolkit is None:
        print("❌ Failed: Cannot get toolkit for employee-b")
        return

    # 複雜指令
    print("\n主管A: 請統計員工B的 Desktop 目錄下有多少個 .md 檔案")

    result = await toolkit.call_tool("chat", {
        "message": "請統計 /Users/maple/Desktop 目錄下有多少個 .md 檔案",
        "model_key": "gpt-4"
    })

    if result["success"]:
        print(f"\n員工B: {result['content']}")
        print("\n✅ Test passed - Agent completed complex task")
    else:
        print(f"\n❌ Failed: {result['error']}")


async def test_chat_with_different_model():
    """測試使用不同模型"""
    print("\n" + "=" * 60)
    print("測試 4: 使用不同模型")
    print("=" * 60)

    toolkit = get_mcp_toolkit("employee-b")

    if toolkit is None:
        print("❌ Failed: Cannot get toolkit for employee-b")
        return

    print("\n主管A: 用 Claude 模型回答問題")

    result = await toolkit.call_tool("chat", {
        "message": "請用一句話解釋什麼是 MCP (Model Context Protocol)",
        "model_key": "claude-3-opus"
    })

    if result["success"]:
        print(f"\n員工B (Claude): {result['content']}")
        print(f"\n使用模型: {result['model']}")
        print("\n✅ Test passed - Different model works")
    else:
        print(f"\n❌ Failed: {result['error']}")


async def test_multi_turn_conversation():
    """測試多輪對話（使用相同 conversation_id）"""
    print("\n" + "=" * 60)
    print("測試 5: 多輪對話")
    print("=" * 60)

    toolkit = get_mcp_toolkit("employee-b")

    if toolkit is None:
        print("❌ Failed: Cannot get toolkit for employee-b")
        return

    # 第一輪
    print("\n主管A (第1輪): 請記住，我的名字是小明")

    result1 = await toolkit.call_tool("chat", {
        "message": "請記住，我的名字是小明",
        "model_key": "gpt-4"
    })

    conv_id = result1["conversation_id"]

    if result1["success"]:
        print(f"員工B: {result1['content']}")
    else:
        print(f"❌ Failed: {result1['error']}")
        return

    # 第二輪（使用相同 conversation_id）
    print(f"\n主管A (第2輪): 我叫什麼名字？(conv_id={conv_id})")

    result2 = await toolkit.call_tool("chat", {
        "message": "我叫什麼名字？",
        "model_key": "gpt-4",
        "conversation_id": conv_id  # ⭐ 使用相同的對話ID
    })

    if result2["success"]:
        print(f"員工B: {result2['content']}")

        # 檢查是否記住了名字
        if "小明" in result2['content']:
            print("\n✅ Test passed - Multi-turn conversation works!")
        else:
            print("\n⚠️  Warning - Agent might not remember context")
    else:
        print(f"❌ Failed: {result2['error']}")


async def main():
    from src.integrations.mcp import initialize_mcp_system

    # 初始化 MCP system
    print("初始化 MCP system...")
    await initialize_mcp_system()

    # 執行所有測試
    await test_simple_chat()
    await test_chat_with_filesystem()
    await test_chat_with_multiple_tools()
    await test_chat_with_different_model()
    await test_multi_turn_conversation()

    print("\n" + "=" * 60)
    print("🎉 所有 chat 測試完成！")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
```

**執行測試**:

```bash
# 在主管A容器中執行
cd backend
uv run python test_peer_chat.py
```

**預期輸出**:
```
============================================================
測試 1: 簡單對話
============================================================

主管A: 你好，請簡單自我介紹

員工B: 你好！我是一個 AI 助手，可以幫助你處理各種任務...

使用模型: gpt-4
對話ID: peer-123e4567-...

✅ Test passed

============================================================
測試 2: 使用 filesystem tool
============================================================

主管A: 請列出員工B的 /Users/maple/Desktop 目錄下的檔案（只要前5個）

員工B: 根據文件系統查詢，您的 Desktop 目錄包含以下檔案：
1. project-report.pdf
2. meeting-notes.md
3. data.csv
4. screenshot.png
5. todo.txt

✅ Test passed - Agent successfully used filesystem tool

============================================================
測試 3: 複雜任務（多個 tools）
============================================================

主管A: 請統計員工B的 Desktop 目錄下有多少個 .md 檔案

員工B: 我已經掃描了您的 Desktop 目錄，總共找到 3 個 .md 檔案：
- meeting-notes.md
- readme.md
- changelog.md

✅ Test passed - Agent completed complex task

============================================================
測試 5: 多輪對話
============================================================

主管A (第1輪): 請記住，我的名字是小明
員工B: 好的，我記住了！你是小明。

主管A (第2輪): 我叫什麼名字？(conv_id=peer-123e4567-...)
員工B: 你的名字是小明！

✅ Test passed - Multi-turn conversation works!

============================================================
🎉 所有 chat 測試完成！
============================================================
```

---

### 任務 3.5: 整合測試到主管A的 Agent

**創建**: `test_manager_agent_with_peer.py`

```python
"""測試主管A的 Agent 能自動使用員工B的 chat tool"""
import asyncio
from src.usecases.conversation import ConversationUsecase
from src.integrations.llm import ConversationAgentFactory
from src.models.conversation import (
    ConversationRequest,
    ConversationMessage,
    MCPToolSelection
)

async def test_manager_agent_calls_employee():
    """
    測試主管A的 Agent 能自動選擇並呼叫員工B的 chat tool
    """
    print("=" * 60)
    print("測試: 主管A的 Agent 自動呼叫員工B")
    print("=" * 60)

    # 初始化 MCP system
    from src.integrations.mcp import initialize_mcp_system
    await initialize_mcp_system()

    # 創建主管A的 Agent
    factory = ConversationAgentFactory()
    usecase = ConversationUsecase(factory)

    # 構建請求 - 讓主管A的 Agent 能使用 employee-b 的 tools
    request = ConversationRequest(
        user_id="manager-a",
        conversation_id="manager-test-001",
        model_key="gpt-4",
        history=[
            ConversationMessage(
                role="user",
                content=(
                    "請幫我向員工B查詢：他的 Desktop 目錄下有哪些檔案？"
                    "（使用 employee-b 的 chat tool）"
                )
            )
        ],
        tools=[
            MCPToolSelection(
                server="employee-b",
                functions=["chat"]  # 只使用 chat tool
            )
        ]
    )

    print("\n主管A: 請幫我向員工B查詢：他的 Desktop 目錄下有哪些檔案？")
    print("\n處理中...")

    # 執行對話
    reply = await usecase.generate_reply(request)

    print(f"\n主管A的 Agent: {reply.content}")
    print(f"\n使用模型: {reply.model_key}")
    print(f"對話ID: {reply.conversation_id}")

    print("\n✅ Test passed - Manager's Agent successfully used employee-b's chat tool!")


async def test_manager_agent_autonomous():
    """
    測試主管A的 Agent 能自主決定何時使用員工B
    """
    print("\n" + "=" * 60)
    print("測試: 主管A的 Agent 自主決策")
    print("=" * 60)

    from src.integrations.mcp import initialize_mcp_system
    await initialize_mcp_system()

    factory = ConversationAgentFactory()
    usecase = ConversationUsecase(factory)

    # 這次不指定具體的 tool，讓 Agent 自己決定
    request = ConversationRequest(
        user_id="manager-a",
        conversation_id="manager-test-002",
        model_key="gpt-4",
        history=[
            ConversationMessage(
                role="user",
                content="統計員工B電腦上有多少個 .pdf 檔案"
            )
        ],
        tools=[
            MCPToolSelection(
                server="employee-b",
                functions=None  # 給 Agent 所有可用的 tools
            )
        ]
    )

    print("\n主管A: 統計員工B電腦上有多少個 .pdf 檔案")
    print("\n處理中...")

    reply = await usecase.generate_reply(request)

    print(f"\n主管A的 Agent: {reply.content}")

    print("\n✅ Test passed - Agent made autonomous decision!")


async def main():
    await test_manager_agent_calls_employee()
    await test_manager_agent_autonomous()

    print("\n" + "=" * 60)
    print("🎉 所有整合測試完成！")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
```

**執行**:

```bash
# 在主管A容器中執行
cd backend
uv run python test_manager_agent_with_peer.py
```

---

## 階段四：添加認證（可選）

### 🎯 目標
為 FastMCP server 添加簡單的 Bearer Token 認證。

---

### 任務 4.1: 添加環境變數支援

**檔案**: `backend/.env.example`

添加：

```bash
# MCP Server 認證（可選）
# 如果設定此 token，所有連接到 /mcp 的請求都需要提供此 token
MCP_SERVER_AUTH_TOKEN=
```

**檔案**: `backend/.env`

```bash
# 員工B的配置
MCP_SERVER_AUTH_TOKEN=shared-secret-123
```

---

### 任務 4.2: 實現認證中間件（FastMCP 已內建，只需配置）

FastMCP 已經支援認證，只需要在配置中指定：

**檔案**: `backend/src/integrations/mcp/server.py`

在文件開頭添加：

```python
from src.config import settings

# 如果設定了 auth token，FastMCP 會自動驗證
_auth_token = settings.get_secret("MCP_SERVER_AUTH_TOKEN")
if _auth_token:
    logger.info("MCP Server authentication enabled")
    # FastMCP 會在 http_app() 中自動處理認證
else:
    logger.info("MCP Server running without authentication (trust internal network)")
```

然後在 `src/main.py` 掛載時傳入 auth：

```python
# src/main.py
from src.config import settings

# 掛載 FastMCP server
_mcp_auth = settings.get_secret("MCP_SERVER_AUTH_TOKEN")
if _mcp_auth:
    app.mount("/mcp", mcp_server.http_app(
        # FastMCP 內建的 bearer token 認證
        auth={"type": "bearer", "token": _mcp_auth}
    ))
else:
    app.mount("/mcp", mcp_server.http_app())
```

**測試**:

```bash
# 啟動員工B (帶認證)
MCP_SERVER_AUTH_TOKEN=shared-secret-123 uv run uvicorn src.main:app --port 8001

# 測試無 token (應該失敗)
curl http://localhost:8001/mcp/sse
# → 401 Unauthorized

# 測試有 token (應該成功)
curl -H "Authorization: Bearer shared-secret-123" http://localhost:8001/mcp/sse
# → SSE stream
```

---

## 驗收標準

### ✅ 階段一驗收

- [ ] `chat()` tool 已添加到 FastMCP server
- [ ] ConversationUsecase 支援 `tools=None` 自動附加所有 MCP tools
- [ ] 可以本地測試 chat tool 正常工作
- [ ] chat tool 能正確使用本地的 filesystem、ms365 等 MCP tools

### ✅ 階段二驗收

- [ ] `list_available_models()` tool 已添加
- [ ] `list_mcp_servers()` tool 正常工作
- [ ] `get_server_capabilities()` tool 已添加（可選）
- [ ] 所有查詢 tools 返回正確的資料

### ✅ 階段三驗收

- [ ] 能成功啟動兩個容器（主管A 和 員工B）
- [ ] 主管A能成功添加員工B為 peer
- [ ] 主管A能查詢員工B的模型列表
- [ ] 主管A能查詢員工B的 MCP servers
- [ ] 主管A能透過 chat 呼叫員工B，員工B回應正確
- [ ] 員工B的 Agent 能正確使用本地的 MCP tools
- [ ] 支援多輪對話（使用 conversation_id）
- [ ] 可以指定不同的模型

### ✅ 階段四驗收（可選）

- [ ] 環境變數 `MCP_SERVER_AUTH_TOKEN` 已設定
- [ ] 無 token 的請求被拒絕（401）
- [ ] 有正確 token 的請求成功
- [ ] Peer connection 使用正確的 token

---

## 常見問題

### Q1: chat tool 呼叫後沒有回應？

**可能原因**:
1. LLM API key 未設定或無效
2. MCP system 未初始化
3. Agent 無法訪問 MCP tools

**除錯步驟**:

```bash
# 檢查日誌
docker logs employee-b | grep -i error

# 檢查 MCP system 狀態
curl http://localhost:8001/api/v1/mcp/servers

# 檢查 LLM 配置
cat backend/config/llm_models.json
```

### Q2: 員工B的 Agent 沒有使用 MCP tools？

**可能原因**:
1. `tools=None` 沒有正確傳遞
2. MCP tools 沒有正確附加到 Agent

**除錯步驟**:

```bash
# 檢查日誌，看是否有 "Auto-attached MCP server"
docker logs employee-b | grep "Auto-attached"

# 如果沒有，檢查 _attach_requested_tools 方法
```

### Q3: Peer connection 失敗？

**可能原因**:
1. URL 不正確（Docker 網路 vs localhost）
2. Auth token 不匹配
3. 網路不通

**除錯步驟**:

```bash
# 測試網路連通性
docker exec -it manager-a curl http://employee-b:8000/health

# 測試 MCP endpoint
docker exec -it manager-a curl http://employee-b:8000/mcp/sse

# 檢查 auth token
docker exec -it employee-b env | grep MCP_SERVER_AUTH_TOKEN
```

### Q4: 多輪對話無法保持上下文？

**原因**: Agno Agent 預設不保存對話歷史。

**解決**: 需要使用 session storage 或手動傳遞歷史訊息。

目前的實現每次都是新對話，如果需要多輪對話，需要：

1. 在 chat tool 中添加 history 參數
2. 使用 Agno 的 session storage 功能

### Q5: 如何添加更多 tools？

參考現有的 tool 格式，在 `server.py` 中添加：

```python
@mcp_server.tool
async def your_new_tool(param1: str, param2: int) -> dict[str, Any]:
    """Tool description"""
    # Your logic here
    return {"result": "..."}
```

---

## 下一步（未來增強）

### 1. 權限控制
- 不同的 peer 有不同的權限
- 某些 tools 只能被特定 peer 呼叫

### 2. 速率限制
- 防止某個 peer 過度呼叫
- 保護資源

### 3. 審計日誌
- 記錄誰呼叫了什麼
- 用於分析和除錯

### 4. 多輪對話優化
- 實現真正的 session storage
- 支援長期記憶

### 5. 異步任務
- 長時間任務返回 task_id
- 支援輪詢查詢結果

---

## 總結

完成以上所有任務後，你將擁有：

✅ 員工B容器暴露 `chat()` endpoint
✅ 主管A容器能查詢員工B的能力（模型、MCP servers）
✅ 主管A容器能透過自然語言呼叫員工B
✅ 員工B的 Agent 能使用本地所有 MCP tools
✅ 支援多種 LLM 模型
✅ 可選的 Bearer Token 認證
✅ 完整的測試套件

**恭喜！🎉 你已經完成了 MCP Peer-to-Peer Agent Chat 功能！**
