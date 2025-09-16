# Contributing Guide

歡迎為 HWDC 2025 MCP League Starter 貢獻！此文件說明如何參與專案開發。

## 🤝 參與方式

### Issues
- 報告 Bug 或提出功能建議
- 詳細描述問題或需求
- 提供重現步驟或使用案例

### Pull Requests
- Fork 專案到你的 GitHub 帳號
- 建立功能分支：`git checkout -b feature/your-feature`
- 遵循編碼規範進行開發
- 確保測試通過
- 提交 Pull Request

## 📝 Commit Message 規範

我們使用 [Conventional Commits](https://www.conventionalcommits.org/en/v1.0.0/) 規範。

### 格式
```
<type>(<scope>): <description>

[optional body]

[optional footer(s)]
```

### 常用類型
- **feat**: 新功能
- **fix**: 修復問題
- **docs**: 文檔更新
- **style**: 程式碼格式（不影響功能）
- **refactor**: 重構（非新功能或修復）
- **test**: 測試相關
- **chore**: 建置工具或輔助工具變動

### 範例
```bash
feat: add user authentication endpoint
fix: correct pagination logic in list_users
docs: update API documentation
chore: update dependencies
```

## 🔧 開發流程

### 1. 環境設置
```bash
# 1. Clone 專案
git clone https://github.com/your-username/hwdc-2025-mcp-league-starter.git
cd hwdc-2025-mcp-league-starter

# 2. 安裝依賴
pnpm install

# 3. 安裝 pre-commit hooks
pnpm run prepare
```

### 2. 開發
```bash
# 啟動開發環境
pnpm dev

# 執行測試
pnpm test

# 程式碼檢查
pnpm lint
pnpm type-check
```

### 3. 提交
```bash
# pre-commit hooks 會自動執行格式化和檢查
git add .
git commit -m "feat: your feature description"
```

## 📋 程式碼品質

### Pre-commit Hooks
專案配置了 pre-commit hooks 自動檢查：
- 程式碼格式化（Prettier, Ruff）
- 類型檢查
- Lint 檢查
- Commit message 格式驗證

### 編碼規範
- **Backend**: 參考 `backend/docs/CODING_STANDARDS.md`
- **Frontend**: 遵循 TypeScript + React 最佳實踐

## 🔍 Code Review

### Pull Request 要求
- [ ] 功能完整且測試通過
- [ ] 遵循編碼規範
- [ ] 包含適當的測試
- [ ] 更新相關文檔
- [ ] Commit message 符合規範

### Review 標準
- 功能是否符合需求
- 程式碼可讀性和可維護性
- 效能和安全性考量
- 測試覆蓋率

## 📚 其他資源

- [後端開發指南](backend/README.md)
- [後端編碼規範](backend/docs/CODING_STANDARDS.md)
- [專案架構說明](README.md)

## 🆘 尋求幫助

遇到問題？
- 查看現有 [Issues](https://github.com/Mapleeeeeeeeeee/hwdc-2025-mcp-league-starter/issues)
- 建立新的 Issue 描述問題
- 參與 [Discussions](https://github.com/Mapleeeeeeeeeee/hwdc-2025-mcp-league-starter/discussions)

感謝你的貢獻！🎉