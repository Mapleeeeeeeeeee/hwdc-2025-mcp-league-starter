# Integrations Layer Guide

`integrations` 層是應用程式與「外部世界」溝通的橋樑。它封裝了所有與外部系統（如資料庫、第三方 API、檔案系統等）互動的技術細節，使應用程式的核心邏輯（`usecases` 和 `domain`）可以保持純粹和獨立。

## 核心原則：實現細節的隔離

`integrations` 層的主要職責是作為外部世界的「適配器 (Adapter)」。它負責處理所有髒活累活，例如：

- 如何建立資料庫連線。
- 如何編寫 SQL 查詢或使用 ORM。
- 如何對第三方 API 進行 HTTP 呼叫、處理認證和解析回應。
- 如何讀寫本地檔案。

**`usecases` 層不應該關心這些細節。** 它只需要呼叫一個由 `integrations` 層實現的、定義清晰的介面。

## 組成部分

`integrations` 層通常根據其整合的外部系統類型進行組織。

### 1. 資料庫互動：倉儲模式 (Repository Pattern)

對於資料庫存取，我們強烈推薦使用「倉儲模式」。這個模式將資料的存取和儲存邏輯抽象化，提供一個類似記憶體中集合（in-memory collection）的介面來操作領域物件。

- **職責**：
  - 封裝資料查詢、新增、更新、刪除的邏輯。
  - 將資料庫的原始資料格式（如 SQL row）轉換為應用程式的**領域模型 (Domain Model)**，反之亦然。
- **位置**：`src/integrations/db/`

**範例**：一個 `UserRepository` 的實現。

```python
# src/integrations/db/user_repository.py
from ...domain.user.models import User # 依賴 domain model

class UserRepository:
    def __init__(self, db_session):
        self._session = db_session

    def get_by_id(self, user_id: int) -> User | None:
        # 假設使用 ORM
        user_row = self._session.query(UserRow).filter_by(id=user_id).first()
        if not user_row:
            return None

        # 將資料庫行轉換為領域模型
        return User(
            id=user_row.id,
            name=user_row.name,
            email=user_row.email
        )

    def save(self, user: User) -> None:
        # 將領域模型轉換為資料庫行並儲存
        user_row = UserRow(id=user.id, name=user.name, email=user.email)
        self._session.add(user_row)
        self._session.commit()

# 注意：UserRepository 的介面 (interface) 可以在 usecases 層或 domain 層定義，
# 以符合依賴倒置原則，但其具體實現則位於 integrations 層。
```

### 2. 第三方 API 客戶端 (API Clients)

當應用程式需要與外部服務（如 LLM、金流服務、郵件服務）溝通時，應為每個服務建立一個專門的客戶端。

- **職責**：
  - 處理對外部 API 的 HTTP 請求和回應。
  - 管理 API Keys、認證和連線細節。
  - 處理特定於該 API 的錯誤，並可選擇將其轉換為應用程式的自訂例外（`shared/exceptions.py`）。
- **位置**：`src/integrations/llm/`, `src/integrations/payment/` 等。

**範例**：一個與 LLM 服務溝通的客戶端。

```python
# src/integrations/llm/openai_client.py
import openai
from ...core.config import settings
from ...shared.exceptions import ServiceUnavailableError

class OpenAIClient:
    def __init__(self):
        openai.api_key = settings.OPENAI_API_KEY

    def generate_text(self, prompt: str) -> str:
        try:
            response = openai.Completion.create(
                engine="text-davinci-003",
                prompt=prompt
            )
            return response.choices[0].text
        except openai.error.APIError as e:
            # 將外部 API 錯誤轉換為應用程式內部的標準錯誤
            raise ServiceUnavailableError(detail=f"OpenAI API error: {e}")
```

## 目標與收益

1.  **隔離變化**：外部系統是最不穩定、最可能變化的部分。將它們隔離在 `integrations` 層，意味著當第三方 API 更新、或公司決定更換資料庫時，我們只需要修改這一層的程式碼，而不會影響到核心的 `usecases` 和 `domain` 層。
2.  **可替換性**：由於 `usecases` 層依賴的是抽象介面而不是具體實現，我們可以輕易地替換掉一個整合的實現。例如，在測試中，我們可以提供一個「假的」`MockUserRepository`，它在記憶體中操作資料而不是真的去連線資料庫，這讓測試變得非常快速和可靠。
3.  **關注點分離**：讓 `usecases` 層專注於「做什麼」（業務流程），而 `integrations` 層專注於「怎麼做」（技術細節），使整個系統的職責劃分更加清晰。
