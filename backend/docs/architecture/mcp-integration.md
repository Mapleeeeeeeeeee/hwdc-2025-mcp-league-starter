# MCP 整合設計指南

此文件說明 `src/integrations/mcp` 封裝的 Model Context Protocol（MCP）啟動、設定與與代理互動方式，協助開發者調整伺服器清單與前端工具選擇。

## 架構概觀
- `MCPManager`：單例，負責載入設定、檢查環境需求、啟動每一個 MCP server，並提供生命週期管理（`initialize_mcp_system` / `graceful_mcp_cleanup`）。
- `MCPParamsManager`：解析 JSON 設定，產出 `MCPServerParams`。會套用專案層級預設，例如 `npx` 指令與逾時秒數。
- `MCPToolkit`：把遠端 MCP 伺服器公開的函式包裝成 Agno `Toolkit`，供對話代理在推理流程中呼叫。
- `GET /api/v1/mcp/servers`：對外曝光目前所有伺服器的啟用狀態、連線情形與函式清單，方便前端 UI 顯示。

## 設定檔與 JSON 格式

預設會從 `backend/config/mcp_servers.json` 載入客製化設定；若檔案不存在，則回退為 `backend/src/integrations/mcp/default_servers.json`。

```jsonc
{
  "mcpServers": {
    "filesystem": {
      "command": "npx",
      "args": ["-y", "mcp-fs-server"],
      "env": {
        "ROOT": "{BASE_PATH}/backend"
      },
      "enabled": true,
      "timeout_seconds": 60,
      "description": "Filesystem browsing tools"
    },
    "context7": {
      "command": "npx",
      "args": ["-y", "@upstash/context7-mcp@latest"],
      "enabled": false
    }
  }
}
```

### 欄位說明
- `command`：要執行的命令（例如 `npx`、`python`），**必填**。完全由 JSON 配置決定，不再依賴環境變數。
- `args`：傳給指令的參數陣列；採用字串列表。
- `env`：啟動子行程時要加上的環境變數，所有值會轉為字串。
- `enabled`：布林值，控制是否在啟動流程中載入；預設 `true`。
- `timeout_seconds`：單一伺服器啟動逾時秒數，預設繼承 `MCP_TIMEOUT_SECONDS`。
- `description`：顯示在 `/mcp/servers` 回傳中的描述文字，方便前端標示。

> 備註：先前透過環境變數個別控制伺服器（如 `BRAVE_API_KEY`、`POSTGRES_DATABASE_URL`）的邏輯已移除，如需額外驗證請於對應的 MCP server 實作中處理。

## 前端工具選擇流程
1. 前端可呼叫 `GET /api/v1/mcp/servers` 取得可用伺服器與函式清單。
2. 在送出 `POST /api/v1/conversation` 或 `/conversation/stream` 時，於 payload 增加 `tools` 欄位：

   ```jsonc
   {
     "conversationId": "conv-1",
     "history": [...],
     "tools": [
       {
         "server": "filesystem",
         "functions": ["search_files", "read_file"]
       }
     ]
   }
   ```

3. `ConversationUsecase` 根據選擇呼叫 `get_mcp_toolkit(server, allowed_functions=...)`，並把回傳的 `MCPToolkit` 掛載到代理上。
4. 若 `functions` 空白或所有函式在 MCP 端不可用，將略過註冊並寫入 debug log，不會中斷整體對話流程。

## API 契約摘要
- `GET /api/v1/mcp/servers`
  - 回傳 `ListMCPServersResponse`，包含 `initialized` 狀態與每個伺服器的 `connected`、`enabled`、`functionCount` 等資訊。
  - 回應頭會附帶 `X-Trace-ID` 與 `X-Process-Time`，方便追蹤。
- `POST /api/v1/conversation` / `/stream`
  - 多了 `tools` 欄位，型別為 `list[MCPToolSelection]`。
  - 回傳仍維持原先的 `ConversationReply`/SSE chunk 格式。

## 測試策略
- 整合測試：`backend/tests/integration/api/test_conversation_router.py`、`test_mcp_router.py` 模擬前端請求，覆蓋工具注入與伺服器列表 API。
- 單元測試：可另外針對 `MCPToolkit` 或 `MCPParamsManager` 撰寫純邏輯測試，確保 JSON 解析與白名單過濾正確。

如需延伸更多 MCP server，只要在 JSON 加上新項目並重新啟動服務即可，無需修改 Python 程式碼。
