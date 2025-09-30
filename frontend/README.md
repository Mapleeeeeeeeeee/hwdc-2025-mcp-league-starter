# Frontend (Next.js 15)

本目錄為講座 MVP 的前端專案，採用 Next.js 15（App Router）+ TypeScript + Tailwind。以下整理常用指令、環境設定與文件索引。

## 需求條件

- Node.js 20+
- pnpm 9+
- 後端 API 服務（預設 http://localhost:8000）

## 安裝與啟動

```bash
pnpm install
pnpm dev
```

瀏覽器開啟 `http://localhost:3000/zh-TW`（未指定語系時會由 middleware 導向預設語系）。

### 常用指令（預計導入）

| 指令            | 說明                                 |
| --------------- | ------------------------------------ |
| `pnpm dev`      | 開發模式，含熱重載                   |
| `pnpm build`    | 建置產生 `.next`                     |
| `pnpm lint`     | ESLint / Stylelint（導入後更新腳本） |
| `pnpm test`     | Vitest 單元測試                      |
| `pnpm test:e2e` | Playwright 端對端測試                |

> 測試與 lint 指令會在導入對應工具後寫入 `package.json`。

## 環境變數

| 變數                       | 預設                    | 說明                                   |
| -------------------------- | ----------------------- | -------------------------------------- |
| `NEXT_PUBLIC_API_BASE_URL` | `http://localhost:8000` | 後端 FastAPI base URL                  |
| `NEXT_LOCALE`              | -                       | 指定預設語系（通常由 middleware 決定） |

專案根目錄已有 `.env.template`，在前端僅需填寫上述變數即可啟動。

## 操作流程

1. 啟動後端 API 服務。
2. 執行 `pnpm dev` 啟動前端。
3. 首頁直接呈現對話介面，點選右上角齒輪可開啟設定 Drawer。
4. 在設定中調整模型、MCP 伺服器以及語系後即可開始互動。

## 相關文件

- [前端資料流設計](docs/data-flow.md)
- [i18n 架構](docs/i18n.md)
- [MCP 整合規劃](docs/mcp-integration.md)
- [UI / 設計規範](docs/ui-guidelines.md)
- [測試策略](docs/testing.md)

更多內容請參考 `frontend/docs/README.md`。
