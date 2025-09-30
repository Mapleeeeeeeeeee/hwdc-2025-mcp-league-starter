# UI / 設計規範

## 設計方向概要

- **Landing Page**：採用 [Aceternity UI](https://ui.aceternity.com/) 的高對比、強動畫組件（如 Lamp Effect、Background Beams、3D Card）。
- **互動亮點**：混搭 [Magic UI](https://magicui.design/) 的動畫原子元件（Shimmer Button、Orbiting Circles、Hyper Text），點綴對話入口與設定 Drawer。
- **產品內容頁**：沿用 [Untitled UI React](https://www.untitledui.com/react) 的設計 Token（排版、色票、間距、陰影）與 Dashboard 模組，確保表單、表格與設定頁一致性。

> 專案定位為一次性講座 MVP，可優先透過開源組件加速開發；授權條款需再確認是否符合使用情境。

## 組件來源與安裝

| 套件              | 安裝指令                                                                                      | 備註                                                                                                     |
| ----------------- | --------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------- |
| Aceternity UI     | `pnpm dlx aceternity ui install`<br>`pnpm add motion clsx tailwind-merge`                     | 個別組件可能需要 `@tabler/icons-react`、`@tsparticles/react`、`three` 等副依賴，導入前請檢視官方頁面。   |
| Magic UI          | `pnpm add next-intl` (既有)<br>`npx shadcn@latest add "https://magicui.design/r/<component>"` | 多數組件依賴 `tailwindcss-animate`、`class-variance-authority`、`lucide-react`；請先安裝後再拖入程式碼。 |
| Untitled UI React | `pnpm dlx untitledui@latest init --next`（僅做為參考，實際導入以既有專案為主）                | 從 CLI 匯入的設計 Token、Tailwind 設定可手動整合至 `tailwind.config.ts` 與 `globals.css`。               |

## Tailwind 設定與 Token

- 字體：
  - Display / Body：`"Inter", sans-serif`。
  - Mono：`"Roboto Mono", monospace`。
- 色彩：
  - 引入 Untitled UI `brand` 級距（25 → 950），並透過 CSS Variables 定義於 `theme.css`。
  - 暗色模式以 `.dark-mode` variant 控制，沿用 Untitled UI 的 `--color-...` 配色。
- 間距 / 圓角 / 陰影：
  - 採用 Untitled UI 預設 Token（`--radius-xl`, `--shadow-modern-mockup-outer-lg` 等），再由 Tailwind `@theme` 映射成 `rounded-xl`、`shadow-lg`。

## 版面佈局

| 區塊         | 描述                                                                                   | 建議組件                                                 |
| ------------ | -------------------------------------------------------------------------------------- | -------------------------------------------------------- |
| 首屏 Hero    | 直上對話卡片，背景使用 Aceternity `Lamp Effect` + `Background Beams`，右上角為設定按鈕 | `components/landing/HeroShell.tsx` + Aceternity snippets |
| 對話卡片     | 以 Untitled UI 的卡片樣式擴充，加入 Magic UI `Hyper Text` 顯示問候字串                 | `components/chat/ConversationCard.tsx`                   |
| 設定 Drawer  | Untitled UI `Sheet` 結構，內部搭配 Magic UI `Shimmer Button`（儲存）                   | `components/chat/SettingsDrawer.tsx`                     |
| MCP 伺服器表 | 使用 Untitled UI 表格 + 狀態 Chip，必要時加入 Magic UI `Orbiting Circles` 表示連線中   | `components/mcp/ServerTable.tsx`                         |

## 可用性（Accessibility）

- 色彩對比至少符合 WCAG AA（文字對背景 4.5:1）。Aceternity 元件導入後需以 Tailwind utility 調整。
- 所有動畫提供 `prefers-reduced-motion` 判斷：
  ```ts
  const shouldReduceMotion = useReducedMotion();
  if (shouldReduceMotion) return <StaticHero />;
  ```
- 對話輸入框與設定 Drawer 的互動需支援鍵盤操作（`Tab`、`Enter`、`Esc`）。
- 圖示加上 `aria-hidden` 或 `aria-label`。

## 命名與檔案結構

```
frontend/src/
  components/
    landing/
      HeroShell.tsx
      AnimatedBackground.tsx
    chat/
      ChatShell.tsx
      ConversationCard.tsx
      SettingsDrawer.tsx
    mcp/
      ServerTable.tsx
      ToolSelector.tsx
    ui/
      Button.tsx
      Card.tsx
      Badge.tsx
```

- `components/ui`：存放被多處引用的原子元件，通常衍生自 Untitled UI / Magic UI。
- `components/<domain>`：放業務相關組件，包裹 UI 元件與業務邏輯。
- 動畫相關檔案可放在 `components/landing/animations/` 以利共享。

## 未來待辦

- 確認 Aceternity 與 Untitled UI 的授權條款，決定最終可上線的組件清單。
- 建立 `themes/light.css` / `themes/dark.css`，集中管理 CSS Variables。
- 規劃元件 Storybook（或 Ladle）以協助 Demo 與視覺驗收。
- 將常用動畫封裝成可調整 props 的元件，減少重複貼片程式碼。
