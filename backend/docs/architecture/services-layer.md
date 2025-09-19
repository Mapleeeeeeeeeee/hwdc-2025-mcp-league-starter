# Services Layer Guide

Services 層（`backend/src/services/`）承擔 Application Service/Use Case 的角色：
整合多個資料來源、執行業務流程、決定應拋出的應用層例外，並回傳 domain 模型給 API。

## 主要責任
- 實作單一用例的業務流程，協調 repositories、integrations 或 domain services。
- 將外部錯誤轉換為專案自訂的 `BaseAppException` 子類（例如 `NotFoundError`、`ConflictError`）。
- 回傳經過整理的資料模型（來自 `src/models/` 或 `src/shared/response` 所需結構）。
- 維持與 transport 層（HTTP、任務佇列等）解耦，方便重複利用。

## 禁止事項
- 不處理 HTTP 細節（如 status code、request/response 物件）。
- 不直接與 FastAPI 互動或存取 `Request`/`Response` 物件。
- 不顯式管理交易或連線（交給 repository 或外層管理）。

## 建議結構
```
backend/src/services/
└── conversation/
    ├── __init__.py
    └── service.py       # LLM 對話相關流程
```
- 依照 bounded context / domain 分資料夾。
- 單檔內可匯出多個 use case，但若流程複雜建議一個 class 對一個主題。

## 建構方式
- 以 class 型式封裝可重複利用的依賴。
- 依賴透過建構子注入，預設可使用具體 repository，測試時可以改為 stub/mock。

- 建議把與供應商相關的設定封裝在 `src/integrations/`，例如 `src/integrations/agno.py`。

```python
# backend/src/services/conversation/service.py
from collections.abc import AsyncIterator

from agno.agent import Agent, RunOutput
from agno.run.agent import RunOutputEvent
from agno.run.events import RunContentEvent
from agno.models.openai import OpenAIChat

from src.core.exceptions import ServiceUnavailableError
from src.models.conversation import (
    ConversationReply,
    ConversationRequest,
    ConversationStreamChunk,
)


class ConversationService:
    """封裝與 Agno Agent 的互動，支援非串流與串流回覆。"""

    def __init__(self, agent: Agent | None = None) -> None:
        # 預設使用 OpenAI Chat 模型，可依設定注入其他 Agent
        self._agent = agent or Agent(
            model=OpenAIChat(id="gpt-4o-mini"),
            markdown=True,
        )

    async def generate_reply(self, payload: ConversationRequest) -> ConversationReply:
        run_output: RunOutput = await self._agent.arun(
            input=payload.history,
            user_id=payload.user_id,
            session_id=payload.conversation_id,
        )

        if run_output.output is None:
            raise ServiceUnavailableError(
                detail="LLM 未回傳結果",
                context={"conversation_id": payload.conversation_id},
            )

        return ConversationReply.model_validate(
            {
                "conversation_id": payload.conversation_id,
                "message_id": run_output.run_id,
                "content": run_output.output,
            }
        )

    async def stream_reply(
        self, payload: ConversationRequest
    ) -> AsyncIterator[ConversationStreamChunk]:
        stream = await self._agent.arun(
            input=payload.history,
            stream=True,
            user_id=payload.user_id,
            session_id=payload.conversation_id,
            yield_run_response=False,
        )

        async for event in stream:
            if isinstance(event, RunContentEvent) and event.content:
                yield ConversationStreamChunk.model_validate(
                    {
                        "conversation_id": payload.conversation_id,
                        "message_id": event.run_id,
                        "delta": event.content,
                    }
                )
```
- Service 可回傳 Pydantic 模型或 async generator，讓 API 層決定如何輸出（JSON 或 SSE）。
- 透過自訂例外讓 API handler 轉換成統一錯誤 JSON。

## 例外處理準則
- 資料不存在：拋 `NotFoundError`。
- 輸入不合法但已通過 API 驗證：視情境拋 `BadRequestError` 或 `UnprocessableEntityError`。
- 外部資源衝突：拋 `ConflictError`。
- 依賴服務故障：拋 `ServiceUnavailableError` 或自訂子類。

## 測試建議
- **單元測試**：以 Fake/Stubs 取代 repository，驗證流程（`tests/unit/services/`）。
- **整合測試**：搭配真實 repository/資料庫或嵌套的外部服務 double，確保資料流正確。

## 與其它層的互動
- Repository：處理資料存取與轉換；Service 只透過公開介面使用。
- Models：定義 input/output schema，維持純資料結構。
- API：唯一直接呼叫 Service 的層級，其他傳輸層（如 CLI、Batch）也可以重用這些 Service。

## 接下來怎麼做
1. 在 `services/` 底下建立對應的 domain 目錄（例如 `mcp/`）。
2. 為每個用例撰寫 Service 類別或函式，並撰寫對應單元測試。
3. 搭配 API 層 router 範例，實際串接成可運作的端點。
