# HWDC 2025 - MCP League Starter

> HWDC 2025「Hello World」工作坊範例：MCP 大聯盟全端樣板

## 🚀 快速開始

### 環境需求
- Node.js 20+
- Python 3.12+
- pnpm 9+
- uv (Python 包管理工具)

> **安裝 uv**: 如果尚未安裝 uv，請參考 [uv 安裝指南](https://docs.astral.sh/uv/getting-started/installation/)

### 安裝與設置

```bash
# 1. 複製專案
git clone https://github.com/Mapleeeeeeeeeee/hwdc-2025-mcp-league-starter.git
cd hwdc-2025-mcp-league-starter

# 2. 一鍵安裝所有依賴（前端 + 後端）
pnpm run install:all

# 或者手動安裝：
# pnpm install                    # 前端依賴
# cd backend && uv sync && cd ..  # 後端 Python 依賴

# 3. （可選）設置 pre-commit hooks
pre-commit install

# 4. 設置環境變數
## Docker 部署（推薦）：
pnpm run setup:env

## 或本地開發：
pnpm run setup:env:local

## 或手動設置：
### Docker 部署：
cp .env.docker.example .env.docker
# 編輯 .env.docker，設置 OPENAI_API_KEY 和 MCP_SERVER_AUTH_TOKEN
# 可選：設置 AS_A_MCP_SERVER=true 如果需要將後端作為 MCP 服務器運行

### 本地開發：
cd backend && cp .env.example .env && cd ..
# 編輯 backend/.env，設置 OPENAI_API_KEY 和 MCP_SERVER_AUTH_TOKEN
# 可選：設置 AS_A_MCP_SERVER=true 如果需要將後端作為 MCP 服務器運行

# 5. （可選）設置自定義配置
## 如果您需要自定義 LLM 模型、提示詞或工具配置：
pnpm run setup:config
## 或者手動複製：
cd backend && mkdir -p config && for file in defaults/default_*.json; do base=$(basename "$file" | sed 's/^default_//'); target="config/$base"; if [ ! -f "$target" ]; then cp "$file" "$target"; fi; done && cd ..
## 然後編輯 config/ 下的檔案來自定義配置
```

### 啟動開發環境

```bash
# 啟動前後端開發伺服器
pnpm dev

# 訪問應用程式
# 前端: http://localhost:3001
# 後端 API: http://localhost:8000
# API 文檔: http://localhost:8000/docs
```

### 故障排除

**如果遇到權限問題：**
```bash
# 確保腳本有執行權限
chmod +x start.sh
```

**如果遇到端口衝突：**
- 前端預設使用 3001 端口
- 後端預設使用 8000 端口
- 可以修改 `frontend/package.json` 或 `backend/.env` 中的端口設置

**如果遇到依賴安裝問題：**
```bash
# 清除快取並重新安裝
rm -rf node_modules pnpm-lock.yaml
pnpm install

# 清除 Python 快取
cd backend && rm -rf .venv uv.lock
uv sync
cd ..
```

**如果遇到環境變數問題：**
- 確保已正確設置 `OPENAI_API_KEY`（從 [OpenAI 官網](https://platform.openai.com/api-keys) 獲取）
- 對於 MCP 功能，需要設置 `MCP_SERVER_AUTH_TOKEN`（使用 `openssl rand -base64 32` 生成）
- 如果需要將後端作為 MCP 服務器運行，設置 `AS_A_MCP_SERVER=true`
- 檢查 `.env` 文件是否在正確位置（Docker 用 `.env.docker`，本地開發用 `backend/.env`）
- 確保環境變數文件沒有被提交到 Git（檢查 `.gitignore`）

## 📋 目前技術棧

### Frontend
- **Next.js 15.5.3** - React 19 + App Router + TypeScript
- **Tailwind CSS 4** - 原子化 CSS 框架
- **Turbopack** - 開發模式（生產用 webpack）

### Backend
- **FastAPI** - Python Web 框架
- **uv** - Python 包管理工具
- **Python 3.12**

### 開發工具
- **pnpm workspace** - Monorepo 管理
- **GitHub Actions** - CI/CD
- **Pre-commit hooks** - 程式碼品質
- **EditorConfig** - 編輯器統一設定

## 📁 專案結構

```
├── frontend/              # Next.js 前端應用
├── backend/               # FastAPI 後端服務
│   ├── config/            # 運行時配置檔案（已忽略 git）
│   │   ├── defaults/      # 預設配置模板
│   │   │   ├── default_llm_models.json
│   │   │   ├── default_active_llm_model.json
│   │   │   ├── default_agno_prompts.json
│   │   │   └── default_agno_tools.json
│   │   ├── mcp_servers.json # MCP 伺服器配置
│   │   └── ...            # 其他配置檔案
│   └── src/
├── docs/                  # 專案文檔
├── scripts/               # 部署和工具腳本
├── .github/
│   ├── workflows/         # GitHub Actions CI/CD
│   └── pull_request_template.md
├── .editorconfig         # 編輯器統一設定
├── .pre-commit-config.yaml # Pre-commit hooks 配置
├── CHANGELOG.md          # 版本更新日誌
├── CONTRIBUTING.md       # 貢獻指南
├── CLOUD_RUN_DEPLOYMENT.md # Cloud Run 部署指南
├── docker-compose.yaml   # Docker Compose 配置
├── Dockerfile            # Docker 映像檔建置
├── nginx.conf            # Nginx 配置
├── package.json          # Workspace 根設定
├── pnpm-workspace.yaml   # pnpm workspace 配置
└── start.sh              # Cloud Run 啟動腳本
```

## ⚙️ 配置檔案說明

本專案採用「預設值 + 自定義配置」的設計模式：

### 📋 配置檔案結構

- **`backend/defaults/`** - 預設配置模板（已提交到 Git）
  - `default_llm_models.json` - LLM 模型配置模板
  - `default_active_llm_model.json` - 預設啟用模型配置
  - `default_agno_prompts.json` - 提示詞配置模板
  - `default_agno_tools.json` - 工具配置模板

- **`backend/defaults/default_mcp_servers.json`** - MCP 伺服器預設配置模板

- **`backend/config/`** - 用戶自定義配置（已忽略 Git）
  - 當這些檔案不存在時，系統會自動從 `defaults/` 或 `src/integrations/mcp/` 複製預設值
  - 用戶可以安全修改這些檔案來自定義配置
  - 修改不會影響版本控制

### 🔄 配置載入邏輯

1. **首次運行**：如果 `config/` 下的檔案不存在，自動從 `defaults/` 複製
2. **後續運行**：直接載入 `config/` 下的檔案
3. **模板保持**：`defaults/` 檔案始終作為原始模板，不會被修改

### 🛠️ 自定義配置

要自定義配置，請編輯 `backend/config/` 下的對應檔案：

```bash
# 編輯 LLM 模型配置
vim backend/config/llm_models.json

# 編輯提示詞配置
vim backend/config/agno_prompts.json

# 編輯工具配置
vim backend/config/agno_tools.json

# 編輯 MCP 伺服器配置
vim backend/config/mcp_servers.json
```

**注意**：`backend/config/` 目錄已被加入 `.gitignore`，您的自定義配置不會被提交到版本控制系統。

## 💻 開發指令

### 專案設置

```bash
pnpm run install:all    # 安裝所有依賴（前端 + 後端）
pnpm run setup:env      # 設置 Docker 環境變數
pnpm run setup:env:local # 設置本地開發環境變數
pnpm run setup:config   # 設置配置檔案模板（可選）
```

### 本地開發模式

```bash
# 開發模式
pnpm dev              # 同時啟動前後端開發伺服器
pnpm dev:frontend     # 只啟動前端 (http://localhost:3001)
pnpm dev:backend      # 只啟動後端 (http://localhost:8080)

# 建置與測試
pnpm build           # 建置所有專案
pnpm test            # 執行所有測試
pnpm lint            # 程式碼檢查
pnpm type-check      # 類型檢查
```

## 🐳 Docker 部署

### 快速啟動

```bash
# 1. 複製環境變數模板
cp .env.docker .env

# 2. 編輯 .env 填入你的 OpenAI API key
# OPENAI_API_KEY=sk-your-actual-key-here

# 3. 啟動容器
pnpm docker:up

# 4. 訪問應用程式
# 前端和後端: http://localhost:8080
# 健康檢查: http://localhost:8080/health
# API 文檔: http://localhost:8080/api/docs
```

### Docker 操作指令

```bash
pnpm docker:up       # 啟動 Docker 環境
pnpm docker:down     # 停止 Docker 環境
pnpm docker:build    # 重新建置映像檔

# 查看容器日誌
docker logs -f hwdc-mcp-league

# 進入容器 shell
docker exec -it hwdc-mcp-league sh
```

### 環境變數配置

本專案支援兩種環境變數配置方式：

#### 1. Docker 部署環境變數（推薦用於生產）
```bash
# 複製 Docker 環境變數模板
cp .env.docker.example .env.docker

# 編輯 .env.docker 文件
# 必須設置的變數：
# - OPENAI_API_KEY: 從 https://platform.openai.com/api-keys 獲取
# - MCP_SERVER_AUTH_TOKEN: 生成安全令牌（建議使用 openssl rand -base64 32）
#
# 可選設置的變數：
# - AS_A_MCP_SERVER: 是否將後端作為 MCP 服務器運行（預設 false）
```

#### 2. 本地開發環境變數
```bash
# 複製後端環境變數模板
cd backend && cp .env.example .env && cd ..

# 編輯 backend/.env 文件
# 主要變數：
# - OPENAI_API_KEY: OpenAI API 金鑰
# - MCP_SERVER_AUTH_TOKEN: MCP 服務器認證令牌
# - PORT: 後端服務端口（預設 8000）
# - ENVIRONMENT: 環境類型（development/production）
# - AS_A_MCP_SERVER: 是否作為 MCP 服務器運行（預設 false）
```

#### 🔑 必填環境變數

| 變數名稱 | 說明 | 如何獲取 | 範例 |
|---------|------|---------|------|
| `OPENAI_API_KEY` | OpenAI API 金鑰 | [OpenAI 官網](https://platform.openai.com/api-keys) | `sk-...` |
| `MCP_SERVER_AUTH_TOKEN` | MCP 服務器認證令牌 | `openssl rand -base64 32` | `abc123...` |

#### 📋 可選環境變數

| 變數名稱 | 預設值 | 說明 |
|---------|--------|------|
| `PORT` | `8000` | 後端服務端口 |
| `ENVIRONMENT` | `development` | 運行環境 |
| `LOG_LEVEL` | `INFO` | 日誌等級 |
| `CORS_ALLOWED_ORIGINS` | 環境相關 | CORS 允許來源 |
| `ENABLE_MCP_SYSTEM` | `true` | 是否啟用 MCP 系統 |
| `MCP_TIMEOUT_SECONDS` | `60` | MCP 請求超時時間 |
| `AS_A_MCP_SERVER` | `false` | 是否將後端作為 MCP 服務器運行 |

#### � MCP 服務器配置

`AS_A_MCP_SERVER` 變數控制後端是否作為 MCP (Model Context Protocol) 服務器運行：

- **`false`** (預設): 後端作為普通 Web API 服務器運行
- **`true`**: 後端額外啟用 MCP 服務器功能，可處理 `/mcp` 端點的請求

**使用場景：**
- 設為 `true` 當您需要將此應用作為 MCP 服務器供其他 MCP 客戶端連接時
- 設為 `false` 用於標準的 Web 應用場景

**注意：** 無論此設定為何，MCP 客戶端功能 (`ENABLE_MCP_SYSTEM`) 都可以正常使用。

#### 🛠️ 快速生成安全令牌

```bash
# 生成 MCP_SERVER_AUTH_TOKEN
openssl rand -base64 32

# 或者使用 Node.js
node -e "console.log(require('crypto').randomBytes(32).toString('base64'))"
```

#### ⚠️ 安全注意事項

- 從不將 `.env` 文件提交到版本控制系統
- 生產環境使用強密碼的 API 金鑰
- MCP 認證令牌應定期輪換
- 確保 `.env` 文件在 `.gitignore` 中

## 🤝 貢獻

歡迎提交 Issue 和 Pull Request！

## 📄 License

Apache License 2.0 - 詳見 [LICENSE](LICENSE) 文件