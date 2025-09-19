# API Layer Guide

API 層（`backend/src/api/`）負責處理 HTTP 介面，將外部請求轉換為應用層可以消化的輸入，並把服務結果轉換成統一的回應。

## 主要責任
- 宣告路由與 HTTP 方法，掛載到 FastAPI `APIRouter`。
- 驗證請求輸入：路由函式只接收已驗證的 Pydantic 模型或基本型別。
- 呼叫對應的 Application Service（`services/`），並處理回傳資料。
- 統一回應格式：使用 `create_success_response()`、`create_paginated_response()` 產生標準 JSON。
- 依賴注入：在 router 層決定 service/repository 的組合方式。

## 禁止事項
- 不自行編寫業務邏輯或資料存取邏輯。
- 不直接產生 HTTP 回應字典（請透過 shared response helper）。
- 不在路由內部抓取資料庫連線或第三方 client，請透過 services/repositories 處理。

## 命名與結構
```
backend/src/api/
└── v1/
    ├── __init__.py
    └── conversation_router.py   # 文字對話 / LLM 相關路由
```
- 建議以版本號（例如 `v1`）分層，方便未來版本並存。
- 單一 router 檔案專注於一個 bounded context（這裡以 LLM 對話為例）。
- 檔案內可宣告 `router = APIRouter(prefix="/conversations", tags=["Conversations"])`，並在 `main.py` 統一掛載。

## 依賴注入範例
```python
# backend/src/api/v1/conversation_router.py
from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse

from src.models.conversation import ConversationRequest
from src.services.conversation.service import ConversationService
from src.shared.response import create_success_response

router = APIRouter(prefix="/conversations", tags=["Conversations"])


def get_conversation_service() -> ConversationService:
    # 目前直接建構；若日後需要其他依賴，可改為 Depends factory
    return ConversationService()


@router.post("/messages")
async def send_message(
    payload: ConversationRequest,
    service: ConversationService = Depends(get_conversation_service),
    stream: bool = Query(False, description="是否以串流方式回傳回覆"),
):
    if stream:
        # 建議使用 Server-Sent Events (SSE) 方便前端瀏覽器直接串流文字
        async def event_source():
            async for chunk in service.stream_reply(payload):
                yield f"data: {chunk.model_dump_json()}\n\n"

        return StreamingResponse(event_source(), media_type="text/event-stream")

    reply = await service.generate_reply(payload)
    return create_success_response(data=reply, message="Reply generated")
```
- `Depends` 用於提供 service 實例，後續可替換測試 double 或加上 cache。
- 串流情境建議採用 **Server-Sent Events (SSE)**，透過 `text/event-stream` 在瀏覽器端最容易處理。若未來需要雙向即時通訊，再評估 WebSocket。
- 非串流情境回傳標準 JSON，以 `create_success_response` 保持 `success/data/message/trace_id` 結構。

## 錯誤處理策略
- 路由函式不應自行 try/except；讓 service 拋出的 `BaseAppException` 交給已註冊的 handler (`backend/src/api/exception_handlers.py:20-233`)。
- 參數驗證失敗會由 FastAPI 自動拋出 `RequestValidationError`，以及我們的 handler 轉換為統一格式。

## 測試建議
- **單元測試**：可利用 FastAPI 的 `TestClient` 測試路由是否呼叫正確的 use case（透過 Mock service）。
- **整合測試**：在 `tests/integration/api/` 使用實際 service/repository 來確保流程完整。

## 接下來怎麼做
1. 建立版本化 router 資料夾 `api/v1/`。
2. 實作第一個 router 範例（例如 `mcp_router.py`），並在 `main.py` 掛載。
3. 隨著功能擴充，針對 router 補上對應的測試與文件。
