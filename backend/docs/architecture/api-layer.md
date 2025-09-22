# API 層責任

API 層（`backend/src/api/`）只處理輸入輸出：解析 HTTP、校驗資料、交給 application service，最後用標準格式傳回結果。

## 定位
- 路由只負責宣告 HTTP 介面與依賴注入（透過 `Depends` 從 `core/container.py` 取得 service 介面）。
- JSON 進來先交給 Pydantic 2.x DTO 驗證，確保 runtime/i18n/預設值都被處理。
- 驗證後可轉為 domain value object，再交給 application service；API 不做任何業務決策。
- Service 回傳 domain model 或 primitive 後，API 以 Response DTO (`APIBaseModel.model_validate(...)`) 加上 `create_success_response()` / `create_paginated_response()` 統一回應。

## 強型別與命名
- 所有 Request/Response DTO (Data Transfer Objects) 都放在 `src/models/`，繼承專案共用 `APIBaseModel`。
- 這些 DTOs 也常被稱為 **Schemas**，兩者在本專案中可視為同義詞，專指 API 的資料合約。
- `APIBaseModel` 定義於 `src/models/base.py`，統一設定：
  ```python
  from pydantic import BaseModel, ConfigDict
  from src.shared.naming import to_camel

  class APIBaseModel(BaseModel):
      model_config = ConfigDict(
          populate_by_name=True,
          alias_generator=to_camel,
      )
  ```
- 繼承後自動開啟 `alias` 與駝峰對應：
  ```python
  from src.models.base import APIBaseModel

  class ConversationRequest(APIBaseModel):
      conversation_id: str
      history: list[Message]
  ```
- FastAPI router 需在參數上加 `Body(...)` 或直接型別註記，確保 runtime 驗證會被觸發。
- 回傳時使用 `model_dump(by_alias=True)`，避免在 API 層手動處理 key 命名。
- 這些 DTO 屬於 application 層的 transport 合約，請在進入 service 前轉為 domain value object 或內部資料結構，維持核心邏輯獨立於 HTTP 命名。

## 邊界守則
- **禁止** 在 router 內寫業務邏輯、資料存取、第三方呼叫或手工建構 JSON。
- **禁止** 捕捉服務層例外；統一由 `exception_handlers.py` 和 `BaseAppException` 處理。
- **允許** 的副作用只有依賴注入、權限或節流等純 transport concern。

## 資料流摘要
1. FastAPI 解析請求 → Pydantic DTO 驗證並進行 camelCase ↔ snake_case 映射。
2. 取得依賴（service、repository 介面）。
3. 將 DTO 傳給 service；service 回傳 typed 結果或 async generator。
4. API 層呼叫 shared response helper，附上 trace_id 與 meta，輸出 JSON。

## 結構建議
```
backend/src/api/
└── v1/
    ├── __init__.py
    └── conversation_router.py
```
- 版本資料夾保持向後相容；每個 router 聚焦單一 bounded context。
- 測試應透過 FastAPI `TestClient` 或 `httpx.AsyncClient`，驗證 DTO 驗證與回應格式是否符合上述約定。
