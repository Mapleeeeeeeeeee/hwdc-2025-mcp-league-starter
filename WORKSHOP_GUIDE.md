# HWDC 2025 工作坊操作指南

> **目標：30 分鐘內體驗 MCP 基礎功能 + Peer-to-Peer 連線**

---

## 📋 課前準備檢查清單

請在工作坊開始前確認以下項目：

### ✅ 必備軟體（請提前安裝）

- [ ] **Node.js 20+** - [下載連結](https://nodejs.org/)
- [ ] **Python 3.12+** - [下載連結](https://www.python.org/downloads/)
- [ ] **pnpm 9+** - [安裝指令](https://pnpm.io/installation)
  ```bash
  npm install -g pnpm
  ```
- [ ] **uv** (Python 包管理工具) - [安裝指南](https://docs.astral.sh/uv/getting-started/installation/)
  ```bash
  # Mac / Linux
  curl -LsSf https://astral.sh/uv/install.sh | sh

  # Windows (PowerShell)
  powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
  ```
- [ ] **Git** - [下載連結](https://git-scm.com/downloads)
- [ ] **VS Code** 或任何文字編輯器

### ✅ 必備資料

- [ ] **OpenAI API Key** - [申請連結](https://platform.openai.com/api-keys)
  - 格式：`sk-proj-xxxxxxxx...`
  - 請確保有足夠額度（建議至少 $5 USD）
- [ ] **找到你的配對夥伴** - 工作坊現場會兩兩一組

### 💡 環境確認指令

開啟終端機（Terminal / Command Prompt），執行以下指令確認安裝成功：

```bash
# 確認 Node.js 已安裝
node --version
# 應該看到：v20.x.x 或更高版本

# 確認 Python 已安裝
python3 --version
# 應該看到：Python 3.12.x 或更高版本

# 確認 pnpm 已安裝
pnpm --version
# 應該看到：9.x.x 或更高版本

# 確認 uv 已安裝
uv --version
# 應該看到：uv x.x.x 或類似版本號

# 確認 Git 已安裝
git --version
# 應該看到：git version 2.x.x 或更高版本
```

**❌ 如果出現 "command not found" 錯誤：**
- 請重新安裝對應軟體
- Mac/Linux 使用者可能需要重啟終端機或執行 `source ~/.bashrc` / `source ~/.zshrc`
- Windows 使用者可能需要重新開啟終端機或檢查環境變數

---

## 🚀 Part 1: 環境設定與功能示範（預計 17 分鐘）

### 步驟 1：下載專案（1 分鐘）

```bash
# 複製專案到你的電腦
git clone https://github.com/Mapleeeeeeeeeee/hwdc-2025-mcp-league-starter.git

# 進入專案資料夾
cd hwdc-2025-mcp-league-starter
```

**✅ 檢查點：**
- 終端機顯示目前路徑包含 `hwdc-2025-mcp-league-starter`
- 執行 `ls` 應該看到 `README.md`、`package.json` 等檔案

---

### 步驟 2：安裝依賴套件（4 分鐘）

```bash
# 一鍵安裝前端 + 後端所有依賴
pnpm run install:all
```

**⏳ 首次執行需要 3-5 分鐘下載套件，請耐心等待...**

**✅ 成功標誌 - 你應該看到類似這樣的訊息：**

```
dependencies:
+ @next/...
+ react 19.x.x
...

✓ Backend dependencies synced
✓ All dependencies installed successfully
```

**⚠️ 如果安裝失敗：**

| 錯誤類型 | 解決方法 |
|---------|---------|
| `pnpm: command not found` | 執行 `npm install -g pnpm` 安裝 pnpm |
| `uv: command not found` | 參考「課前準備」重新安裝 uv |
| `Python version mismatch` | 確認 Python 版本為 3.12+ |
| 權限錯誤 | Mac/Linux 使用者可能需要 `sudo` |

---

### 步驟 3：設定環境變數（3 分鐘）

```bash
# 設置本地開發環境變數
pnpm run setup:env:local
```

這個指令會自動在 `backend/` 資料夾建立 `.env` 檔案。

**接下來用文字編輯器開啟 `backend/.env` 檔案：**

```bash
# Mac / Linux
open backend/.env

# Windows
notepad backend/.env

# 或用 VS Code
code backend/.env
```

**📝 必填欄位（只需改這兩行）：**

找到第 42 行，將你的 OpenAI API Key 貼上：

```bash
# 改之前：
OPENAI_API_KEY="your-openai-api-key-here"

# 改之後（範例）：
OPENAI_API_KEY="sk-proj-0KKa2YPRlz3oVVj..."
```

找到第 65 行，設定一個測試用的 Token：

```bash
# 可以隨便設定，例如：
MCP_SERVER_AUTH_TOKEN=test-workshop-token-123

# 或使用 openssl 生成：
# openssl rand -base64 32
```

**💡 重要：**
- 記下這個 Token，稍後要告訴配對夥伴！
- **Alice 和 Bob 要約定使用同一個 Token**（例如都用 `workshop-2025`）
- 或者各自設定，但交換時要告訴對方自己的 Token

**💾 記得儲存檔案！**

**✅ 檢查點：**
- `backend/.env` 檔案存在
- 第 42 行有你的 API Key（以 `sk-` 開頭）
- 第 65 行有生成的 Token（一串看起來隨機的字符）
- 檔案已儲存（關閉編輯器前確認）

---


### 步驟 3.5：設定 Filesystem 路徑（2 分鐘）

**設定 filesystem MCP server 指向你的桌面：**

```bash
# 設置本地開發預設檔案
pnpm run setup:config
```

1. **開啟 MCP 配置檔：**
   ```bash
   code backend/config/mcp_servers.json
   ```

2. **找到 `filesystem` 區塊，修改 `args` 的路徑：**

   ```json
   "filesystem": {
     "type": "stdio",
     "command": "npx",
     "args": [
       "-y",
       "@modelcontextprotocol/server-filesystem",
       "/Users/你的使用者名稱/Desktop/"
     ],
     "enabled": true
   }
   ```

3. **取得你的桌面路徑：**

   **Mac / Linux:**
   ```bash
   echo ~/Desktop/
   # 會顯示類似：/Users/maple/Desktop/
   ```

   **Windows:**
   ```bash
   echo %USERPROFILE%\Desktop\
   # 會顯示類似：C:\Users\YourName\Desktop\
   ```

4. **將路徑貼到 `args` 的最後一個元素**

5. **儲存檔案：**

**✅ 檢查點：**
- `args` 的第三個元素是你的桌面完整路徑
- 路徑最後要有斜線 `/` 或 `\`
- 重啟後終端機沒有 filesystem 相關錯誤

---

### 步驟 4：啟動開發伺服器（2 分鐘）

```bash
# 同時啟動前端 + 後端開發伺服器
pnpm dev
```

**✅ 成功標誌 - 你應該在終端機看到：**

```
[1]    ▲ Next.js 15.5.3 (Turbopack)
[1]    - Local:        http://localhost:3001
[1]    - Network:      http://192.168.31.79:3001
[1] 
[1]  ✓ Starting...
[1]  ✓ Compiled middleware in 125ms
[1]  ✓ Ready in 1119ms

...

[0] 2025-10-14 06:03:32,375 | INFO | src.integrations.mcp.manager:87 | MCP system initialisation complete
[0] 2025-10-14 06:03:32,375 | INFO | uvicorn.error:62 | Application startup complete.
```

**⚠️ 常見錯誤處理：**

| 錯誤訊息 | 解決方法 |
|---------|---------|
| `Port 3001 is already in use` | 前端端口被佔用，關閉其他 Node.js 程序或修改 `frontend/package.json` 的端口 |
| `Port 8000 is already in use` | 後端端口被佔用，修改 `backend/.env` 的 `PORT=8080` |
| `OPENAI_API_KEY not found` | 檢查 `backend/.env` 是否正確設定 |
| `ModuleNotFoundError` | 重新執行 `cd backend && uv sync` |

**💡 提示：不要關閉這個終端機視窗！讓伺服器繼續運行**

---

### 步驟 5：開啟應用程式（1 分鐘）

**打開瀏覽器，訪問：**

```
http://localhost:3001
```

**✅ 你應該看到：**
- 一個聊天介面
- 左側有對話歷史列表
- 右側有聊天輸入框
- 頂部可能有 MCP 工具設定選項

---

### 步驟 6：跟著講師示範操作（5 分鐘）

**講師會依序示範以下功能，請跟著操作：**

#### 📂 示範 1：File System 操作

**先在桌面建立測試檔案：**
```bash
# Mac / Linux
echo "Hello MCP Workshop" > ~/Desktop/test.txt

# Windows (PowerShell)
echo "Hello MCP Workshop" > $env:USERPROFILE\Desktop\test.txt
```

**在聊天框輸入：**
```
請列出我桌面上的所有檔案
```

**✅ 成功標誌：**
- AI 會使用 `filesystem` MCP server
- 返回桌面檔案清單（應該包含 test.txt）

**進階測試：**
```
請讀取我桌面上 test.txt 的內容
```

---

#### 📧 示範 2：MS365 整合

**在聊天框輸入：**
```
請列出我的前 3 封郵件內容 幫我快速整理重點
```

**✅ 成功標誌：**
- AI 會使用 `ms365` MCP server
- 返回郵件清單（需要登入授權）

**💡 如果是第一次使用 MS365：**
- 系統會提示你進行 OAuth 授權
- 跟著瀏覽器指示完成登入

---

#### 🔍 示範 3：網路搜尋

**在聊天框輸入：**
```
幫我搜尋 Model Context Protocol 的最新消息
```

**✅ 成功標誌：**
- AI 會使用網路搜尋工具
- 返回相關搜尋結果

#### 示範4: 請幫我最近找到關鍵字為 "AI" 的所有信件 整理完之後在桌面寫成一份word檔案 並寄送一份給 test@test.com

---

## 🤝 Part 2: Peer-to-Peer MCP 連線實作（預計 15 分鐘）

> **目標：兩兩一組，互相連接對方的 MCP Server，體驗分散式 AI 協作**

### 🎯 情境說明

講師會用容器示範呼叫 `/chat` API：
- 請 AI 讀取桌面的文件
- 整合 MS365 內容
- 最後寄信到講師信箱

**現在輪到你們了！**
- 你們將兩兩一組
- A 可以透過 AI 操作 B 的電腦（反之亦然）
- 體驗真正的分散式 MCP 協作

---

### 步驟 1：尋找配對夥伴（1 分鐘）

**請在現場找一位夥伴，並決定角色：**

- 👤 **角色 A**：Alice（主動連線方）
- 👤 **角色 B**：Bob（被連線方）

**💡 建議坐在一起，方便溝通！**

---

### 步驟 2：使用 VSCode DevTunnel 暴露端口（3 分鐘）

**⚠️ 重要：兩人都要執行這個步驟！**

#### 在 VSCode 中建立 DevTunnel

1. **開啟 VSCode 的 Port 面板：**
   - 按 `Cmd + Shift + P`（Mac）或 `Ctrl + Shift + P`（Windows）
   - 輸入 `Ports: Focus on Ports View`
   - 或直接點擊 VSCode 底部狀態列的「PORTS」分頁

2. **轉發 8000 端口：**
   - 點擊「Forward a Port」按鈕（或右鍵 → Forward Port）
   - 輸入：`8000`
   - 按 Enter

3. **設定為 Public：**
   - 找到剛建立的 8000 端口
   - 右鍵點擊 → **Port Visibility** → 選擇 **Public**
   - **非常重要：必須設為 Public，否則對方無法連線！**

4. **複製 DevTunnel URL：**
   - 在 8000 端口的 **Forwarded Address** 欄位
   - 會看到類似：`https://abc123xyz-8000.asse.devtunnels.ms`
   - 右鍵點擊 → **Copy Local Address**

**✅ 成功標誌：**
- PORTS 面板顯示 8000 端口狀態為「Running」
- Visibility 顯示為「Public」（🌐 圖示）
- 已複製到 DevTunnel URL

---

#### 約定共用 Token 並交換 URL

**⚠️ 重點：兩人要約定使用同一個 Token！**

**推薦做法（簡單）：**
```
約定的共用 Token: workshop-2025

兩人都在 backend/.env 設定：
MCP_SERVER_AUTH_TOKEN=workshop-2025
```

**交換 DevTunnel URL：**

Bob 告訴 Alice：
```
Bob 的 URL: https://abc123xyz-8000.asse.devtunnels.ms
```

Alice 告訴 Bob：
```
Alice 的 URL: https://def456uvw-8000.asse.devtunnels.ms
```

**💡 為什麼要用同一個 Token？**
- Alice 呼叫 Bob 時，會用 Bob 的 Token 認證
- Bob 呼叫 Alice 時，會用 Alice 的 Token 認證
- 如果兩人約定用同一個（例如 `workshop-2025`），就不用記兩個不同的 Token
- 這是測試用的，實際生產環境才需要各自的安全 Token

---

### 步驟 3：啟用 MCP Server 模式（3 分鐘）

**⚠️ 重要：兩人都要執行這個步驟！**

1. **停止開發伺服器：**
   - 在運行 `pnpm dev` 的終端機按 `Ctrl + C`

2. **編輯環境變數：**

```bash
# 開啟 backend/.env
code backend/.env

# 找到最後一行（或新增一行），改為：
AS_A_MCP_SERVER=true
```

**💾 記得儲存檔案！**

3. **重新啟動伺服器：**

```bash
pnpm dev
```

**✅ 檢查點：**
- 終端機顯示 `[backend] MCP Server enabled at /mcp`
- 前端和後端都正常啟動

---

### 步驟 4：Alice 連接 Bob 的 MCP Server（4 分鐘）

**Alice 在 VSCode 編輯配置檔：**

1. **開啟 MCP 伺服器配置檔：**
   ```bash
   code backend/config/mcp_servers.json
   ```

2. **在 `mcpServers` 區塊新增 Bob 的設定：**

   找到檔案中的 `"mcpServers": {` 部分，在裡面新增：

   ```json
   "bob-peer": {
     "type": "http",
     "url": "https://abc123xyz-8000.asse.devtunnels.ms/mcp",
     "auth": {
       "type": "bearer",
       "token": "test-workshop-token-123"
     },
     "timeout_seconds": 180,
     "enabled": true,
     "description": "Bob's MCP Server"
   }
   ```

   **完整範例（注意 JSON 格式與逗號）：**
   ```json
   {
     "mcpServers": {
       "filesystem": {
         "type": "stdio",
         "command": "npx",
         "args": ["-y", "@modelcontextprotocol/server-filesystem", "/app"],
         "enabled": true
       },
       "bob-peer": {
         "type": "http",
         "url": "https://abc123xyz-8000.asse.devtunnels.ms/mcp",
         "auth": {
           "type": "bearer",
           "token": "test-workshop-token-123"
         },
         "timeout_seconds": 180,
         "enabled": true,
         "description": "Bob's MCP Server"
       }
     }
   }
   ```

3. **記得替換成 Bob 實際的資訊：**
   - `url`: Bob 的 DevTunnel URL + `/mcp`
   - `token`: **和 Bob 約定的共用 Token**（例如 `workshop-2025`）

**⚠️ 重要：這裡的 token 必須和 Bob 的 `backend/.env` 中的 `MCP_SERVER_AUTH_TOKEN` 一致！**

4. **儲存檔案**

5. **重新啟動後端伺服器：**
   - 終端機按 `Ctrl + C` 停止
   - 執行 `pnpm dev` 重新啟動

**✅ 成功標誌：**
- 終端機顯示載入了 bob-peer 伺服器
- 沒有出現 connection 錯誤

---

### 步驟 5：Alice 操作 Bob 的電腦（3 分鐘）

**確保 Bob 的桌面也有 test.txt：**
```bash
# Bob 在自己電腦執行
echo "This is Bob's file" > ~/Desktop/test.txt
```

**Alice 在聊天框輸入：**

```
請使用 bob-peer 的 /chat 給予對方使用 filesystem 工具，請他幫我列出他桌面上的部分檔案
```

**或者更明確指定：**

```
請使用 bob-peer 伺服器讀取桌面上 test.txt 的內容
```

**進階任務（整合多個工具）：**

```
請透過 bob-peer：
1. 讀取他桌面上名為 test.txt 的檔案內容
2. 查詢他最近 3 封郵件的主旨
3. 用他的信箱寄一封郵件給我，內容包含以上資訊
```

**✅ 成功標誌：**
- 成功返回 Bob 電腦上的資訊
- （如果寄信）Alice 收到來自 Bob 信箱的郵件

**💡 觀察終端機日誌：**
- Alice 的終端機會顯示「Calling peer: bob」
- Bob 的終端機會顯示「[backend] POST /mcp」（收到請求）

---

### 步驟 6：角色互換（3 分鐘）

**現在換 Bob 連接 Alice！**

1. Bob 重複「步驟 4」，填入 Alice 的 url 和 Token
2. Bob 在聊天框嘗試操作 Alice 的電腦
3. 兩人互相體驗分散式協作的感覺

**💬 可以嘗試的有趣任務：**
```
請同時使用我的 MCP 和 alice 的 MCP：
1. 讀取我桌面上的 report.txt
2. 讀取 alice 桌面上的 data.txt
3. 整合兩份資料後，用我的郵箱寄給 alice
```

---

## 🔍 Part 3: 進階功能探索（選做）

### 查看 API 文檔

訪問：http://localhost:8000/docs

**你可以看到：**
- 所有後端 API 端點
- 特別注意 `/api/v1/mcp/peers` 相關端點
- 可以直接在網頁上測試 API 呼叫

---

### 驗證 Peer 連接

**檢查後端日誌：**
- 重新啟動後端後，終端機應該顯示載入了 `bob-peer`
- 如果看到 connection error，代表 URL 或 Token 有問題

**測試 Bob 的 DevTunnel 是否可訪問：**
```bash
# 在 Alice 的電腦測試
curl https://abc123xyz-8000.asse.devtunnels.ms/health

# 應該看到：{"success": true, "data": {...}}
```

**如果需要修改配置：**
1. 編輯 `backend/config/mcp_servers.json`
2. 修改 `bob-peer` 的設定
3. 重新啟動後端伺服器

---

### 停止開發伺服器

```bash
# 在運行 pnpm dev 的終端機按下：
Ctrl + C

# 確認所有程序已停止
# 前端和後端都會自動關閉
```

---

## ❓ 快速故障排除指引

### 問題 1：無法連接到 Peer

**症狀：**
- `Connection refused` 或 `Timeout`
- Peer 連接失敗

**檢查清單：**

1. **確認 DevTunnel 設定正確**
   - VSCode PORTS 面板確認 8000 端口存在
   - Visibility 必須是 **Public**（🌐 圖示）
   - 狀態顯示為「Running」

2. **確認 DevTunnel URL 正確**
   ```
   ✅ 正確：https://abc123xyz-8000.asse.devtunnels.ms/mcp
   ❌ 錯誤：https://abc123xyz-8000.asse.devtunnels.ms （缺少 /mcp）
   ❌ 錯誤：http://abc123xyz-8000.asse.devtunnels.ms/mcp （http 而非 https）
   ```

3. **確認 Bob 的伺服器有啟用 MCP Server 模式**
   - 檢查 `backend/.env` 的 `AS_A_MCP_SERVER=true`
   - 檢查終端機有顯示 `MCP Server enabled at /mcp`

4. **測試 DevTunnel 是否可訪問**
   ```bash
   # 在 Alice 的電腦測試 Bob 的 DevTunnel
   curl https://abc123xyz-8000.asse.devtunnels.ms/health

   # 應該看到：{"success": true, "data": {...}}
   ```

5. **重新建立 DevTunnel**
   - 在 VSCode PORTS 面板刪除 8000 端口
   - 重新 Forward Port 並設為 Public
   - 複製新的 URL 給對方

---

### 問題 2：Authentication Failed (401)

**症狀：**
- `401 Unauthorized`
- `Invalid token`

**解決方法：**

1. **確認 Token 完全一致（最常見問題）**
   ```bash
   # Alice 檢查 config/mcp_servers.json 的 bob-peer.auth.token
   # Bob 檢查 backend/.env 的 MCP_SERVER_AUTH_TOKEN
   # 兩者必須 100% 相同
   ```

2. **重新約定共用 Token**
   - 兩人都停止伺服器
   - 約定一個簡單的 Token（例如 `workshop-2025`）
   - Alice 修改 `backend/.env` 的 `MCP_SERVER_AUTH_TOKEN=workshop-2025`
   - Bob 也修改 `backend/.env` 的 `MCP_SERVER_AUTH_TOKEN=workshop-2025`
   - Alice 修改 `config/mcp_servers.json` 的 `bob-peer.auth.token` 為 `workshop-2025`
   - 兩人都重新啟動伺服器

3. **確認 Token 沒有多餘空格或引號**
   - 環境變數：`MCP_SERVER_AUTH_TOKEN=workshop-2025`（不要有引號）
   - JSON 配置：`"token": "workshop-2025"`（要有引號）

---

---

### 問題 3：MS365 授權失敗

**症狀：**
- `Authentication required`
- `OAuth flow failed`

**解決方法：**

1. **首次使用需要授權**
   - 跟著瀏覽器彈出視窗完成 Microsoft 登入
   - 授權後會自動儲存 token

2. **確認是使用「個人」Microsoft 帳號**
   - 工作或學校帳號可能有權限限制
   - 建議使用 Outlook.com / Hotmail 等個人帳號

---

## 📚 延伸閱讀

完成工作坊後，你可以繼續探索：

- **[README.md](./README.md)** - 完整專案文檔
- **[PEER_TO_PEER_SETUP.md](./backend/PEER_TO_PEER_SETUP.md)** - 詳細 P2P MCP 設定指南
- **[AGNO_TOOLS_PROMPTS.md](./backend/docs/AGNO_TOOLS_PROMPTS.md)** - 自定義工具與提示詞
- **API 文檔**
  - 本地開發：http://localhost:8000/docs
  - MCP Peers API：`/api/v1/mcp/peers`

---

## 🎓 工作坊完成檢查清單

### Part 1: 基礎功能
- [ ] 成功安裝所有依賴套件
- [ ] 成功啟動開發伺服器（前端 + 後端）
- [ ] 能夠訪問 http://localhost:3001
- [ ] 測試過 File System MCP 工具
- [ ] 測試過 MS365 MCP 工具（或至少看過示範）
- [ ] 測試過網路搜尋功能

### Part 2: P2P 連線
- [ ] 找到配對夥伴並交換 Token
- [ ] 成功啟用 `AS_A_MCP_SERVER=true`
- [ ] 成功連接到夥伴的 MCP Server
- [ ] 成功透過 AI 操作夥伴的電腦
- [ ] 角色互換也成功連接
- [ ] 理解 P2P MCP 的運作原理

**🎉 恭喜你完成工作坊！你已經掌握 MCP 的核心概念與分散式協作能力！**

---

## 💬 需要協助？

- **GitHub Issues**: https://github.com/Mapleeeeeeeeeee/hwdc-2025-mcp-league-starter/issues
- **工作坊現場**: 舉手發問或尋找助教協助

---

## 🐳 附錄：使用 Docker 部署（備用方案）

如果本地開發環境遇到困難，可以改用 Docker 方式快速啟動。

### 前置需求

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) 已安裝並啟動

### 快速啟動步驟

```bash
# 1. 複製 Docker 環境變數模板
cp .env.docker.example .env.docker

# 2. 編輯 .env.docker（設定 API Key 和 Token）
code .env.docker
# 需修改：
# - 第 14 行：OPENAI_API_KEY="你的-api-key"
# - 第 18 行：MCP_SERVER_AUTH_TOKEN=生成的-token
# - 第 19 行：AS_A_MCP_SERVER=true

# 3. 啟動容器
docker compose up --build

# 4. 訪問應用程式
# 瀏覽器開啟：http://localhost:8080
```

### Docker 與本地開發的差異

| 項目 | 本地開發 | Docker |
|------|---------|--------|
| 前端訪問 | http://localhost:3001 | http://localhost:8080 |
| 後端訪問 | http://localhost:8000 | http://localhost:8080/api |
| 環境變數檔案 | `backend/.env` | `.env.docker` |
| 熱更新 | ✅ 支援 | ❌ 需重新建置 |
| 安裝依賴 | 需手動安裝 Node.js/Python | ✅ 容器內已包含 |
| 啟動速度 | 快（2-3 秒） | 慢（首次 3-5 分鐘） |
| 適用場景 | 開發與調試 | 快速體驗/生產部署 |
| P2P 連線方式 | VSCode DevTunnel | 需設定外部網路 |
| P2P URL 格式 | `https://xxx.devtunnels.ms/mcp` | `http://IP:8080/api/mcp` |

### 停止 Docker 容器

```bash
# 停止容器（保留資料）
docker compose down

# 完全清理（包含資料庫）
docker compose down -v
```

---
