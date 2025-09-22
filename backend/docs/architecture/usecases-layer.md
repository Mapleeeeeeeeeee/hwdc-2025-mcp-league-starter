# Use Cases Layer Guide

Use Cases 層（`backend/src/usecases/`）承擔 Application Service 的角色：
整合多個資料來源、執行業務流程、決定應拋出的應用層例外，並回傳 domain 模型給 API。

## 主要責任
- 實作單一用例的業務流程，協調 repositories、integrations 或 domain services。
- 接收已驗證的輸入物件（API DTO 轉換後的 domain value object 或純 domain model），將外部錯誤轉換為專案自訂 `BaseAppException` 子類。
- 僅回傳 domain model / value object / primitive，不回傳 API DTO，保持對 transport 解耦。
- 維持與 transport 層（HTTP、任務佇列等）解耦，方便重複利用。

## 禁止事項
- 不處理 HTTP 細節（如 status code、request/response 物件）。
- 不直接與 FastAPI 互動或存取 `Request`/`Response` 物件。
- 不顯式管理交易或連線（交給 repository 或外層管理）。

## 建議結構
```
backend/src/usecases/
└── conversation/
    ├── __init__.py
    └── usecase.py       # LLM 對話相關流程
```
- 依照 bounded context / domain 分資料夾。
- 單檔內可匯出多個 use case，但若流程複雜建議一個 class 對一個主題。

## 建構方式
- 以 class 型式封裝可重複利用的依賴。
- 所有 repository / integration 必須透過建構子注入（constructor injection）；禁止在方法內直接 `new` 具體實作。
- FastAPI 端由 dependency provider 或 `core/container.py` 決定注入的具體實作，以利測試替換或動態設定。

- 建議把與供應商相關的設定封裝在 `src/integrations/`，例如 `src/integrations/agno.py`。

### 架構決策：為貢獻者優化的務實方法

本專案旨在作為一個易於理解和擴充的範本。為了達到這個目標，我們在架構上做出了一個關鍵的務實決策：

**我們推薦 Use Case 層直接使用在 `src/models/` 中定義的 API DTOs (Data Transfer Objects) 作為其輸入和輸出。**

這個選擇是為了**降低新貢獻者的入門門檻**。

- **優點**：貢獻者可以快速理解從 API 到 Use Case 的資料流，無需編寫或理解 DTO 與內部 Domain Model 之間轉換的樣板程式碼。這讓新增或修改功能變得更直接、更快速。
- **取捨**：這意味著 Use Case 層與 API 的公開資料格式有一定程度的耦合。

我們相信，對於一個旨在鼓勵社群參與和擴充的專案來說，降低認知負擔和開發阻力的好處，遠大於追求架構絕對純粹性的好處。

### 給貢獻者的指引：如何處理資料模型

為了讓您能清晰地貢獻程式碼，請遵循以下指引：

1.  **預設情況：直接使用 DTO**
    對於大多數功能，請直接在 Use Case 的方法中接收和回傳定義在 `src/models/` 中的 DTO 模型。這是本專案推薦的標準做法。

2.  **進階情況：重構為 Domain Model**
    當您遇到以下情況時，是一個將部分邏輯重構為使用純粹 Domain Model 的好時機：
    - 某個 Use Case 的**業務邏輯變得異常複雜**。
    - 您需要從一個**完全不同的入口點**（例如背景任務、CLI 命令）來重用同一個 Use Case。

    在這種情況下，您可以在 `src/domain/` 中建立自己的模型，然後在 Use Case 的開頭將傳入的 DTO 轉換為您的 Domain Model。這為複雜的、核心的業務邏輯提供了一條通往更穩健、更解耦的架構路徑。

### 程式碼範例

以下範例展示了我們的標準做法：`ConversationUsecase` 直接使用 `ConversationRequest` 這個 DTO。

```python
# backend/src/usecases/conversation/usecase.py
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


class ConversationUsecase:
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
- Use Case 可回傳 Pydantic 模型或 async generator，讓 API 層決定如何輸出（JSON 或 Server-Sent Events）。
- 透過自訂例外讓 API handler 轉換成統一的錯誤 JSON。

## 例外處理準則
- 資料不存在：拋 `NotFoundError`。
- 輸入不合法但已通過 API 驗證：視情境拋 `BadRequestError` 或 `UnprocessableEntityError`。
- 外部資源衝突：拋 `ConflictError`。
- 依賴服務故障：拋 `ServiceUnavailableError` 或自訂子類。

## 與其它層的互動
- **Repository**：處理資料存取與轉換；Use Case 只透過其公開介面互動。
- **Models**：定義 Use Case 的輸入/輸出資料合約 (DTOs)。
- **API**：是 Use Case 的主要消費者。其他傳輸層（如 CLI、背景任務）也可以重用這些 Use Case。

## 接下來怎麼做
1. 在 `src/usecases/` 底下建立對應您功能的目錄（例如 `mcp/`）。
2. 為每個用例撰寫 Use Case 類別或函式，並為其撰寫單元測試。
3. 在 `src/api/` 中建立對應的 router，並在其中呼叫您的 Use Case。
