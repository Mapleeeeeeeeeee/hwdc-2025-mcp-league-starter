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
# 目前可用指令
pnpm install          # 安裝依賴
```

## 🤝 貢獻

歡迎提交 Issue 和 Pull Request！

## 📄 License

Apache License 2.0 - 詳見 [LICENSE](LICENSE) 文件