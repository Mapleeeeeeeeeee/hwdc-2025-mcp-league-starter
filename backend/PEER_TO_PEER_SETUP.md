# MCP Peer-to-Peer Setup Guide

本指南說明如何設定兩個容器進行 MCP peer-to-peer 通訊：
- **Container A (Manager/Local)**: 本地測試容器，負責呼叫 Container B
- **Container B (Employee/Deployed)**: 部署容器，提供 MCP tools 給 Container A 使用

## 架構概覽

```
┌─────────────────────────────────────────────────────────────────┐
│ Container A (Manager/Local)                                     │
│                                                                  │
│  Agent A → calls peer "employee-b" → HTTP /mcp endpoint         │
│            uses chat() tool                                      │
└──────────────────────────┬──────────────────────────────────────┘
                           │ HTTP + Bearer Token
                           │ POST https://deployed-url/mcp
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│ Container B (Employee/Deployed)                                 │
│                                                                  │
│  FastMCP Server (/mcp) → Agent B → MCP Tools (filesystem, etc.) │
│  - Validates Bearer token                                       │
│  - Executes chat() tool                                         │
│  - Auto-attaches all local MCP servers                          │
└─────────────────────────────────────────────────────────────────┘
```

## 前置準備

### 1. 共享的 Authentication Token

**生成的 Token** (已為你生成):
```
Dguvb+W8eYoiEJjWPs0le06kJDsm6ZzAx5fh1Bus0mI=
```

**重要**: 兩個容器都必須使用相同的 token。

## Container B (Employee/Deployed) 設定

### 1. 環境變數設定

部署容器時，設定以下環境變數：

```bash
# .env 或部署配置
MCP_SERVER_AUTH_TOKEN=Dguvb+W8eYoiEJjWPs0le06kJDsm6ZzAx5fh1Bus0mI=
OPENAI_API_KEY=your-openai-api-key
ENABLE_MCP_SYSTEM=true
ENVIRONMENT=production
HOST=0.0.0.0
PORT=8000
```

### 2. 確認部署 URL

假設你的部署 URL 是：
```
https://your-deployed-app.run.app
```

那麼 MCP endpoint 會在：
```
https://your-deployed-app.run.app/mcp
```

### 3. 驗證部署

部署後，可以透過 health check 驗證：
```bash
curl https://your-deployed-app.run.app/health
```

預期回應：
```json
{
  "success": true,
  "data": {
    "status": "healthy",
    "environment": "production",
    "version": "2.0.0"
  }
}
```

## Container A (Manager/Local) 設定

### 1. 環境變數設定

已更新本地 `.env` 檔案，使用相同的 token：
```bash
MCP_SERVER_AUTH_TOKEN=Dguvb+W8eYoiEJjWPs0le06kJDsm6ZzAx5fh1Bus0mI=
OPENAI_API_KEY=your-openai-api-key
ENABLE_MCP_SYSTEM=true
ENVIRONMENT=development
HOST=0.0.0.0
PORT=8000
```

### 2. 啟動本地容器

```bash
cd backend
uv run fastapi dev src/main.py --port 8000
```

### 3. 新增 Peer Connection

使用 API 將部署容器新增為 peer：

```bash
# 替換 YOUR_DEPLOYED_URL 為實際的部署 URL
curl -X POST http://localhost:8000/api/v1/mcp/peers \
  -H "Content-Type: application/json" \
  -d '{
    "peer_name": "employee-b",
    "peer_url": "https://YOUR_DEPLOYED_URL/mcp",
    "auth_token": "Dguvb+W8eYoiEJjWPs0le06kJDsm6ZzAx5fh1Bus0mI="
  }'
```

預期回應：
```json
{
  "success": true,
  "data": {
    "success": true,
    "peer_name": "employee-b",
    "peer_url": "https://YOUR_DEPLOYED_URL/mcp",
    "function_count": 8,
    "message": "Peer node 'employee-b' added successfully"
  },
  "message": "Peer node 'employee-b' connected"
}
```

### 4. 驗證 Peer Connection

列出所有已連接的 peers：
```bash
curl http://localhost:8000/api/v1/mcp/peers
```

預期回應：
```json
{
  "success": true,
  "data": {
    "peers": [
      {
        "name": "employee-b",
        "url": "https://YOUR_DEPLOYED_URL/mcp",
        "description": "Peer node at https://YOUR_DEPLOYED_URL/mcp",
        "connected": true,
        "function_count": 8
      }
    ]
  },
  "message": "Found 1 peer node(s)"
}
```

## 測試 Peer-to-Peer Chat

### 方式 1: 透過 REST API (推薦用於測試)

使用本地容器的 conversation API，並指定使用 peer tools：

```bash
curl -X POST http://localhost:8000/api/v1/conversation \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "manager-a",
    "conversation_id": "test-peer-chat-001",
    "history": [
      {
        "role": "user",
        "content": "請使用 employee-b 的 chat tool 來問他：你有哪些 MCP servers 可用？"
      }
    ],
    "tools": [
      {
        "server": "employee-b",
        "functions": ["chat", "list_mcp_servers", "get_server_capabilities"]
      }
    ]
  }'
```

### 方式 2: 透過前端 UI

1. 啟動前端：
```bash
cd ../frontend
pnpm dev
```

2. 在 UI 中：
   - 選擇 MCP Tools
   - 勾選 `employee-b` server
   - 勾選 `chat` tool
   - 輸入訊息：「請幫我查詢 employee-b 有哪些 MCP servers」

### 預期行為

Container A 的 Agent 會：
1. 收到用戶指令
2. 發現需要使用 `employee-b` 的 `chat` tool
3. 透過 HTTP 呼叫 `https://YOUR_DEPLOYED_URL/mcp` 並附上 Bearer token
4. Container B 驗證 token 後執行 `chat()` tool
5. Container B 的 Agent 自動附加所有本地 MCP tools (filesystem, ms365, etc.)
6. Container B 執行查詢並回傳結果
7. Container A 收到結果並回應給用戶

## 可用的 Peer Tools

Container B 透過 FastMCP server 暴露以下 tools：

### 1. `chat` - 執行自然語言對話
```python
await chat(
    message="List all files in /project directory",
    model_key="gpt-4o-mini",  # optional
    conversation_id="conv-123",  # optional
    user_id="peer-caller"  # optional
)
```

### 2. `list_available_models` - 列出可用模型
```python
list_available_models()
```

### 3. `get_server_capabilities` - 取得完整能力資訊
```python
get_server_capabilities()
```

### 4. `list_mcp_servers` - 列出 MCP servers
```python
list_mcp_servers()
```

### 5. `reload_mcp_server` - 重新載入 MCP server
```python
await reload_mcp_server(server_name="filesystem")
```

### 6. `reload_all_mcp_servers` - 重新載入所有 MCP servers
```python
await reload_all_mcp_servers()
```

### 7. `get_mcp_server_functions` - 取得特定 server 的 functions
```python
get_mcp_server_functions(server_name="filesystem")
```

### 8. `get_available_mcp_servers` - 取得所有已連接的 servers
```python
get_available_mcp_servers()
```

## 管理 Peer Connections

### 列出所有 peers
```bash
curl http://localhost:8000/api/v1/mcp/peers
```

### 移除 peer
```bash
curl -X DELETE http://localhost:8000/api/v1/mcp/peers/employee-b
```

### 重新新增 peer
重複「新增 Peer Connection」步驟

## 故障排除

### 1. Connection Failed
**錯誤**: `Failed to add peer node: Connection refused`

**解決方式**:
- 確認部署容器正在運行
- 檢查 URL 是否正確 (包含 `/mcp` 路徑)
- 確認防火牆/網路設定允許連線

### 2. Authentication Failed
**錯誤**: `401 Unauthorized`

**解決方式**:
- 確認兩個容器使用相同的 `MCP_SERVER_AUTH_TOKEN`
- 檢查 token 沒有多餘的空白或換行
- 確認 `auth_token` 參數有正確傳遞

### 3. No Functions Available
**錯誤**: `function_count: 0`

**解決方式**:
- 檢查 Container B 的 MCP system 是否成功初始化
- 查看 Container B 的 logs: `ENABLE_MCP_SYSTEM=true`
- 確認 `src/integrations/mcp/server.py` 中的 tools 有正確定義

### 4. Chat Tool Returns Error
**錯誤**: `{"success": false, "error": "..."}`

**解決方式**:
- 檢查 Container B 的 `OPENAI_API_KEY` 是否正確
- 查看 Container B 的應用程式 logs
- 確認 Container B 有可用的 MCP servers

## 安全注意事項

1. **Token 管理**:
   - 使用強隨機 token (至少 32 bytes)
   - 不要將 token 提交到版本控制
   - 定期輪換 token

2. **網路安全**:
   - 生產環境必須使用 HTTPS
   - 考慮使用 VPN 或私有網路
   - 實施 IP 白名單 (如果可行)

3. **監控**:
   - 記錄所有 peer connections
   - 監控異常的 API 呼叫
   - 設定 rate limiting

## 進階配置

### 多個 Peer Connections

可以同時連接多個 peers：

```bash
# 新增 Employee B
curl -X POST http://localhost:8000/api/v1/mcp/peers \
  -H "Content-Type: application/json" \
  -d '{
    "peer_name": "employee-b",
    "peer_url": "https://employee-b.run.app/mcp",
    "auth_token": "token-for-b"
  }'

# 新增 Employee C
curl -X POST http://localhost:8000/api/v1/mcp/peers \
  -H "Content-Type: application/json" \
  -d '{
    "peer_name": "employee-c",
    "peer_url": "https://employee-c.run.app/mcp",
    "auth_token": "token-for-c"
  }'
```

### 環境特定配置

不同環境使用不同 peers：

```bash
# .env.development
MCP_PEER_EMPLOYEE_B_URL=http://localhost:9000/mcp

# .env.production
MCP_PEER_EMPLOYEE_B_URL=https://employee-b.run.app/mcp
```

## 完整測試流程

```bash
# 1. 確認本地容器運行
curl http://localhost:8000/health

# 2. 確認部署容器運行
curl https://YOUR_DEPLOYED_URL/health

# 3. 新增 peer connection
curl -X POST http://localhost:8000/api/v1/mcp/peers \
  -H "Content-Type: application/json" \
  -d '{
    "peer_name": "employee-b",
    "peer_url": "https://YOUR_DEPLOYED_URL/mcp",
    "auth_token": "Dguvb+W8eYoiEJjWPs0le06kJDsm6ZzAx5fh1Bus0mI="
  }'

# 4. 驗證 peer 已連接
curl http://localhost:8000/api/v1/mcp/peers

# 5. 測試 peer chat
curl -X POST http://localhost:8000/api/v1/conversation \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "test-user",
    "conversation_id": "test-001",
    "history": [
      {
        "role": "user",
        "content": "Call employee-b chat tool to list their available models"
      }
    ],
    "tools": [
      {
        "server": "employee-b",
        "functions": ["chat", "list_available_models"]
      }
    ]
  }'
```

## 相關文件

- FastMCP Server 實作: `src/integrations/mcp/server.py`
- Peer Management API: `src/api/v1/mcp_router.py`
- MCP Manager: `src/integrations/mcp/manager.py`
- Authentication 配置: `.env.example`

## 總結

這個設定讓你能夠：
- ✅ Container A (本地) 可以透過自然語言呼叫 Container B (部署)
- ✅ Container B 自動使用所有本地配置的 MCP tools
- ✅ 安全的 Bearer token 認證
- ✅ 動態新增/移除 peer connections
- ✅ 支援多個 peer nodes 同時連接

下一步可以考慮：
- 實作 peer discovery (自動發現其他 containers)
- 加入 peer health monitoring
- 實作 load balancing across multiple peers
- 加入 request caching for frequently used peer tools
