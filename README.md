# HWDC 2025 - MCP League Starter

> HWDC 2025「Hello World」工作坊範例：MCP 大聯盟全端樣板

## 🚀 快速開始

### 環境需求
- Node.js 20+
- Python 3.12+
- pnpm 9+

### 安裝

```bash
# 1. 複製專案
git clone https://github.com/Mapleeeeeeeeeee/hwdc-2025-mcp-league-starter.git
cd hwdc-2025-mcp-league-starter

# 2. 安裝依賴
pnpm install
```

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
├── frontend/          # Next.js 前端
├── backend/           # FastAPI 後端
├── .github/workflows/ # CI/CD
├── .editorconfig     # 編輯器設定
├── .pre-commit-config.yaml
└── package.json      # Workspace 根設定
```

## 💻 開發指令

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

# Docker 操作
pnpm docker:up       # 啟動 Docker 環境
pnpm docker:down     # 停止 Docker 環境
pnpm docker:build    # 重新建置映像檔
```

## 🤝 貢獻

歡迎提交 Issue 和 Pull Request！

## 📄 License

Apache License 2.0 - 詳見 [LICENSE](LICENSE) 文件