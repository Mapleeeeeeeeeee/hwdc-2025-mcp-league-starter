# 測試策略

## 目標

- 以 **單元測試 (UT)** + **整合測試 (IT)** 檢查核心邏輯。
- 針對聊天流程、MCP 工具選取與串流呈現建立 **端對端測試 (E2E)**。
- 在 CI 中維持基本 coverage（語法 + 關鍵流程），避免回歸。

## 工具選擇

| 層級     | 工具                                                                                                            | 說明                                                                                    |
| -------- | --------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------- |
| 單元測試 | [Vitest](https://vitest.dev) + [Testing Library](https://testing-library.com/docs/react-testing-library/intro/) | 與 Vite 生態兼容，執行速度快，與 React Testing Library 配合進行元件測試。               |
| 整合測試 | Vitest + React Testing Library                                                                                  | 針對 hooks（例如 `useApi`、`useToolSelection`）與組件組合（ChatShell + ToolSelector）。 |
| 端對端   | [Playwright](https://playwright.dev)                                                                            | 模擬瀏覽器場景，覆蓋對話送出、串流顯示、MCP 勾選與錯誤提示。                            |

安裝指令（待專案導入 Vite 測試設定後）：

```bash
pnpm add -D vitest @testing-library/react @testing-library/jest-dom
pnpm add -D playwright @playwright/test
```

## Coverages 與最低要求

- 單元測試：
  - 目標 coverage 行數 70% 以上，尤其是資料處理與錯誤映射。
  - 對 `api-client`、`ApiError`、`useApi`、`useToolSelection` 必須撰寫測試。
- 整合測試：
  - `ChatShell`：對話送出成功、對話送出失敗（顯示錯誤 toast）、模型切換。
  - `SettingsDrawer`：MCP 勾選後儲存、localStorage 同步、Reduced Motion 模式。
- 端對端測試：
  - Flow 1：使用者進站 → 看到預設對話框 → 送出訊息 → 接收串流 delta。
  - Flow 2：MCP 伺服器啟動失敗 → 顯示錯誤 → 使用者點擊重新整理 → 成功恢復。
  - Flow 3：語言切換 → UI 文字更新 → 再切回原語系。

## CI 整合

- 於 `.github/workflows/ci.yml` 新增 frontend job 步驟：
  ```yaml
  - name: Install frontend deps
    run: pnpm install --filter frontend...
  - name: Lint
    run: pnpm --filter frontend lint
  - name: Unit tests
    run: pnpm --filter frontend test
  - name: Playwright tests
    run: pnpm --filter frontend test:e2e -- --reporter=list
  ```
- Playwright job 可設定僅在 `main` / `release` branch 執行，或於 PR 標記 `e2e` label 時觸發。

## Mock 與測試資料

- API：使用 MSW (Mock Service Worker) 或 Vitest mock `fetch`，回傳 `APIResponse` 造假資料。
- SSE：利用 Playwright `page.addInitScript` 或自訂 `MockEventSource` 測試串流。
- localStorage：測試前清空，並驗證 key `mcp:selectedServers`、`chat:modelKey` 的行為。

## 未來 TODO

- 建立 `pnpm` script：`test`, `test:watch`, `test:e2e`, `lint`。
- 加入 pre-commit 钩子（Husky 或 Lefthook）在本機先跑 lint + UT。
- 建置自動化測試報告（Coverage + Playwright HTML）。
