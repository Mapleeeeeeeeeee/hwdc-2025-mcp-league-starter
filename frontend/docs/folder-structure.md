# 前端目錄規劃（App Router）

此文件定義前端專案在 `frontend/src` 下的建議結構，參考 Next.js 官方 App Router 最佳實踐：

- 路由由資料夾定義，相關 UI/邏輯可共置。
- 依功能領域拆分 `feature` 區域，減少跨層依賴。
- 透過清楚的段落 (segment) 與特殊檔案 (`page.tsx`、`layout.tsx` 等) 管理 UI、資料取得、錯誤處理。

## 目錄概觀

```
frontend/
  src/
    app/
      (public)/            # 不需登入即可瀏覽的路由群組
        layout.tsx         # 公用 layout（導覽列、底部資訊等）
        page.tsx           # Landing page
        about/
          page.tsx
      (dashboard)/         # 登入後操作介面（可整合 MCP 工具）
        layout.tsx
        page.tsx
        mcp/               # MCP 工具瀏覽、啟用設定
          page.tsx
          loading.tsx
          error.tsx
      api/                 # 僅供 App Router 使用的 route handlers（必要時）
        mcp/
          route.ts
      layout.tsx           # Root layout：字體、Theme Provider、全域樣式
      template.tsx         # (選用) 用於強制重新渲染的 layout
      error.tsx            # 全域錯誤邊界
      loading.tsx          # 初始載入 skeleton
    components/            # 可重用的共用元件（純 UI）
      ui/
      layout/
    features/              # 功能域模組：服務整合、hooks、特殊元件
      mcp/
        components/
        hooks/
        services/          # API Client、型別定義
    lib/                   # 跨域工具函式、型別、常數
    styles/                # 非 Tailwind 的額外樣式或 tokens
    test/                  # （選用）前端測試共用工具
```

### Segments 與 Route Groups

- 利用 `()` 包住的資料夾定義 Route Group，不會影響 URL，但可將公共 layout 分組。
- 例如 `(public)` 與 `(dashboard)`，可在各自 `layout.tsx` 中注入不同的導覽列 / 權限檢查。

### 特殊檔案使用

| 檔案           | 用途                                                                           |
| -------------- | ------------------------------------------------------------------------------ |
| `layout.tsx`   | 定義當前 segment 的共用框架（Navigation、Providers）。                         |
| `page.tsx`     | 對應實際的 URL 頁面。Server Component 為預設。                                 |
| `loading.tsx`  | segment 的載入狀態元件，適合顯示 skeleton。                                    |
| `error.tsx`    | segment 的錯誤邊界，可搭配 `useEffect` 回報錯誤。                              |
| `route.ts`     | App Router 的 API Route handler，取代舊 `pages/api` 概念。                     |
| `template.tsx` | 與 `layout` 類似，但在切換路由時會重新渲染（適用於需要重新初始化狀態的場景）。 |

## 命名規則

- **檔案**：以 kebab-case 命名 React 元件以外的檔案，例如 `use-mcp-tools.ts`。共用元件使用 PascalCase 如 `ToolCard.tsx`。
- **資料夾**：依角色命名，如 `components/ui`, `hooks`, `services`。
- **型別**：集中於 `features/*/services/types.ts` 或 `lib/types.ts`，保持 API 契約一致。

## 功能模組建議

每個 feature 建議內含：

```
features/<feature>/
  components/
  hooks/
  services/
    client.ts   # fetch wrapper
    types.ts    # DTO / Schema
  utils/
  index.ts      # 導出對外 API
```

這樣在 `app/(dashboard)/mcp/page.tsx` 中可透過 `import { useMcpServers } from '@/features/mcp'` 獲得整合邏輯。

## 後續 TODO

- `features/mcp` 需對應後端 `/api/v1/mcp/servers` 與對話工具 API，實作 hooks + cache 策略。
- `components/ui` 可導入 UI kit（如 shadcn/ui 或自定設計系統），並在 `ui-guidelines.md` 補充。
- 製作 `data-flow.md` 描述 Server Component 與 Client Component 如何分享狀態、錯誤處理。

> 依此結構逐步落實，可保持目錄清晰且便於擴充、測試。後續若需調整，再同步更新本文件。

## 職責邊界

以下條目說明各層級的責任與實作準則，協助維持「薄頁面、厚模組」的設計：

### `app/*/page.tsx`

- 路由進入點，聚合所需的 layout / feature 元件即可。
- 不直接處理資料解包或複雜商業邏輯；若要取得資料，呼叫 `features/*/services` 的函式或在子元件內使用 hooks。
- 保持為 Server Component（除非需要互動），利於 SEO 與快取。

### `app/*/layout.tsx`

- 定義 segment 的共用 UI、元資訊與 Providers。
- 可進行權限檢查或注入導航列，但避免放入可重複使用的 UI（移至 `components/layout`）。
- 若需重新渲染，可搭配 `template.tsx`。

### `components/ui`

- 純展示元件，無 domain 邏輯，接受 props 後直接渲染。
- 保持 stateless、可測試，方便跨功能重用。

### `components/layout`

- 應用共用骨架（Header、Sidebar、Shell 等），由 app layout 引入即可。
- 不依賴特定 domain 狀態，必要資料透過 props 傳入。

### `features/<domain>/components`

- 與領域邏輯密切的 UI；內部可以使用 `features/<domain>/hooks`。
- 透過 `features/<domain>/index.ts` 對外導出公開元件，避免散落 import。

### `features/<domain>/hooks`

- 將資料流程與狀態管理（React Query/SWR/Signals）集中於此。
- 向下呼叫 `services` 取得資料，向上吐給頁面/元件；不要直接操作 DOM。
- Server Component 通常直接呼叫 `services` 函式即可；Client Component 若需快取/重試/錯誤提示，應優先透過共用 hooks（例如 `useApi`, `useApiMutation`）封裝，以維持 loading/error 處理一致。

### `features/<domain>/services`

- 集中 API client、型別定義、資料映射與錯誤轉換。
- 以純函式實作，避免耦合 React，方便在 Server Component 或 Node 腳本重用。
- 推薦目錄：
  - `client.ts`：封裝 `fetch` / axios 並處理信封式回應。
  - `types.ts`：維護 DTO 與回傳型別。
  - `mapper.ts`：將 API response 轉換為前端 ViewModel。

### `lib`

- 放置跨 domain 的工具函式、常數、型別、錯誤映射。
- 包含 `config.ts`：統一管理環境變數與應用配置，提供型別安全存取。
- 不得引用 `features`，維持依賴單向性。

### `styles`

- Tailwind 自訂設定、CSS 變數、非 tailwind 的共用樣式。
- 若導入設計系統（例如 Mantine/NextUI），相關主題設定可放在此或 `lib/theme`。
