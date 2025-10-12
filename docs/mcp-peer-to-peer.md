# MCP Peer-to-Peer 功能文檔

## 概述

此應用現在同時支援作為 **MCP Client** 和 **MCP Server**，實現容器之間的點對點（peer-to-peer）通訊。

## 架構

```
Container A (Node 1)          Container B (Node 2)
┌─────────────────────┐      ┌─────────────────────┐
│ MCP Client ←────────┼──────┤ MCP Server (/mcp)  │
│                     │ HTTP │                     │
│ MCP Server (/mcp)   ├──────┼→ MCP Client         │
│                     │      │                     │
│ FastAPI REST API    │      │ FastAPI REST API    │
└─────────────────────┘      └─────────────────────┘
```

## 主要功能

### 1. MCP Server 端點

每個容器在 `/mcp` 路徑暴露 MCP server，提供以下 tools：

- `list_mcp_servers()` - 列出所有配置的 MCP servers 及其狀態
- `reload_mcp_server(server_name)` - 重新載入特定 MCP server
- `reload_all_mcp_servers()` - 重新載入所有啟用的 MCP servers
- `get_mcp_server_functions(server_name)` - 獲取特定 server 的函數列表
- `get_available_mcp_servers()` - 獲取所有已連接的 server 名稱

以及 resources：

- `config://app` - 應用程式配置資訊
- `health://system` - 系統健康狀態

### 2. Peer Node 管理 API

#### 列出所有 peer nodes

```http
GET /api/v1/mcp/peers
```

**回應範例：**
```json
{
  "success": true,
  "data": {
    "peers": [
      {
        "name": "node-2",
        "url": "http://node2:8000/mcp",
        "description": "Peer node at http://node2:8000/mcp",
        "connected": true,
        "function_count": 5
      }
    ]
  },
  "message": "Found 1 peer node(s)"
}
```

#### 添加 peer node

```http
POST /api/v1/mcp/peers
Content-Type: application/json

{
  "peer_name": "node-2",
  "peer_url": "http://node2:8000/mcp",
  "auth_token": "optional-bearer-token"
}
```

**回應範例：**
```json
{
  "success": true,
  "data": {
    "success": true,
    "peer_name": "node-2",
    "peer_url": "http://node2:8000/mcp",
    "function_count": 5,
    "message": "Peer node 'node-2' added successfully"
  },
  "message": "Peer node 'node-2' connected"
}
```

#### 移除 peer node

```http
DELETE /api/v1/mcp/peers/{peer_name}
```

**回應範例：**
```json
{
  "success": true,
  "data": {
    "success": true,
    "peer_name": "node-2",
    "message": "Peer node 'node-2' removed successfully"
  },
  "message": "Peer node 'node-2' disconnected"
}
```

## 使用場景

### 場景 1：Docker Compose 部署

```yaml
version: '3.8'

services:
  node1:
    build: .
    environment:
      - HOST=0.0.0.0
      - PORT=8000
    ports:
      - "8001:8000"

  node2:
    build: .
    environment:
      - HOST=0.0.0.0
      - PORT=8000
    ports:
      - "8002:8000"
```

**連接兩個節點：**

```bash
# 從 node1 連接到 node2
curl -X POST http://localhost:8001/api/v1/mcp/peers \
  -H "Content-Type: application/json" \
  -d '{
    "peer_name": "node-2",
    "peer_url": "http://node2:8000/mcp"
  }'

# 從 node2 連接到 node1
curl -X POST http://localhost:8002/api/v1/mcp/peers \
  -H "Content-Type: application/json" \
  -d '{
    "peer_name": "node-1",
    "peer_url": "http://node1:8000/mcp"
  }'
```

### 場景 2：使用 MCP Client 連接

使用 FastMCP client 連接到任何節點：

```python
from fastmcp import Client
from fastmcp.client.transports import StreamableHttpTransport

async with Client(
    transport=StreamableHttpTransport("http://localhost:8001/mcp")
) as client:
    # 列出所有可用的 tools
    tools = await client.list_tools()
    print(f"Available tools: {[t.name for t in tools]}")

    # 呼叫 tool
    result = await client.call_tool("list_mcp_servers", {})
    print(result)
```

## 技術實現

### 核心元件

1. **`src/integrations/mcp/server.py`**
   - FastMCP server 實例
   - 暴露應用功能為 MCP tools 和 resources

2. **`src/integrations/mcp/manager.py`**
   - `add_peer_node()` - 動態添加 peer 連接
   - `remove_peer_node()` - 移除 peer 連接
   - `list_peer_nodes()` - 列出所有 peer

3. **`src/api/v1/mcp_router.py`**
   - REST API 端點管理 peer nodes

4. **`src/main.py`**
   - 掛載 FastMCP server 到 `/mcp` 路徑

### 傳輸協議

- 使用 **HTTP/SSE** (Streamable HTTP) 傳輸
- 支援 Bearer Token 認證
- 持久化連接管理
- 自動重連機制

## 安全考量

1. **認證**：支援可選的 Bearer Token 認證
2. **CORS**：透過 FastAPI middleware 控制
3. **網路隔離**：建議在私有網路中部署
4. **輸入驗證**：所有 API 端點使用 Pydantic 驗證

## 監控與除錯

### 檢查 MCP server 狀態

```bash
curl http://localhost:8000/api/v1/mcp/servers
```

### 檢查 peer connections

```bash
curl http://localhost:8000/api/v1/mcp/peers
```

### 查看日誌

所有 MCP 操作都會記錄在應用日誌中：

```bash
docker logs <container-name> | grep MCP
```

## 常見問題

### Q: Peer node 無法連接？

A: 檢查：
1. 目標 URL 是否正確
2. 網路是否可達（防火牆、DNS）
3. 目標容器是否正在運行
4. 是否需要 auth_token

### Q: 如何查看 peer node 提供哪些 tools？

A:
```bash
curl http://localhost:8000/api/v1/mcp/servers | jq '.data.servers[] | select(.name=="peer-name")'
```

### Q: Peer node 斷線後會自動重連嗎？

A: 目前不支援自動重連，需要手動移除後重新添加。未來版本會加入此功能。

## 進階使用

### 動態服務發現

可以結合 Consul、etcd 等服務發現工具，自動註冊和發現 peer nodes：

```python
# 範例：使用 Consul 服務發現
import consul

async def discover_and_connect_peers():
    c = consul.Consul()
    services = c.catalog.service('mcp-node')

    for service in services:
        peer_url = f"http://{service['ServiceAddress']}:{service['ServicePort']}/mcp"
        await add_peer_node(
            peer_name=service['ServiceID'],
            peer_url=peer_url
        )
```

### 負載均衡

使用多個 peer nodes 實現負載分散：

```python
import random

async def call_tool_with_lb(tool_name, params):
    peers = list_peer_nodes()
    peer = random.choice(peers)
    toolkit = get_mcp_toolkit(peer['name'])
    return await toolkit.call_tool(tool_name, params)
```

## 相關文件

- [FastMCP 官方文檔](https://gofastmcp.com)
- [MCP 協議規範](https://modelcontextprotocol.io)
- [本專案 API 文檔](../README.md)
