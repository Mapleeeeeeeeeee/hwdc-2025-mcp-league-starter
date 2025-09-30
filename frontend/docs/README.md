# 前端整體規劃

本章節整理現有 Next.js 前端的基礎狀況與後續規劃方向，作為實作前的共識文件。

## 現況速覽

- 使用 Next.js 15（App Router）+ TypeScript，維持 `create-next-app` 初始化範本。
- 目前僅有 `app/layout.tsx` / `app/page.tsx` / `app/globals.css`，尚未整合後端 API 或 MCP 工具。
- 無額外的 UI 元件、路由、狀態管理或資料取得層。

## 規劃目標

1. **明確的路由與模組切分**：遵循 Next.js 官方建議，路由段 (route segment) 與 UI/邏輯共置，依功能領域拆分。
2. **以後端契約為核心**：前端應能依 MCP 伺服器工具清單動態調整 UI 與可用操作，與後端 API 契約保持同步。
3. **易於測試與擴充**：確保頁面、元件、hooks 的目錄結構清晰，方便 UT / IT / E2E 覆蓋。
4. **文件優先**：所有重大設計決策（路由、狀態、樣式、資料流）需在 docs 中留痕，便於 onboarding。

## 後續文檔

| 文件                                           | 說明                                        |
| ---------------------------------------------- | ------------------------------------------- |
| [`folder-structure.md`](./folder-structure.md) | 路由與檔案目錄規劃、命名規則                |
| [`data-flow.md`](./data-flow.md)               | 前端資料取得策略：API 封裝、Cache、錯誤處理 |
| [`i18n.md`](./i18n.md)                         | 語系支援、翻譯檔案結構與命名規範            |
| [`mcp-integration.md`](./mcp-integration.md)   | 前端與 MCP 工具互動流程、狀態管理方案       |
| [`ui-guidelines.md`](./ui-guidelines.md)       | UI/UX 原則、組件來源、Tailwind Token        |
| [`testing.md`](./testing.md)                   | 測試策略與工具選擇                          |

> 後續文檔依此架構增補，保持與後端 docs 的調性一致（繁體中文、重點式撰寫）。
