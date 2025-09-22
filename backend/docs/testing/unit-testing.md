# 單元測試原則與實務（Unit Testing Guide）

> 目標：用最小可驗證單元的自動化測試，穩定支撐重構與快速迭代。

## 目錄
- [核心目的](#核心目的)
- [範圍界定](#範圍界定)
- [原則：FIRST / AAA / TDD](#原則first--aaa--tdd)
- [該做 / 不該做](#該做--不該做)
- [命名與結構](#命名與結構)
- [Test Double 規範](#test-double-規範)
- [覆蓋率與品質門檻](#覆蓋率與品質門檻)
- [本機與 CI 執行](#本機與-ci-執行)
- [Code Review 清單](#code-review-清單)

## 核心目的
- 驗證最小單元（函式/類別）的**行為**是否正確。
- 形成**重構安全網**，避免回歸。
- 以測試可行性回饋設計（可測試性、低耦合）。


## 範圍界定
- 不觸及外部 I/O（DB、HTTP、FS、時鐘、亂數）；必要時以假件隔離。
- API/Infra 的協議與 I/O 放在整合測。

## 原則（FIRST / AAA / TDD）
- **FIRST**：Fast／Isolated／Repeatable／Self‑validating／Timely
- **AAA**：Arrange → Act → Assert
- **Red‑Green‑Refactor**：先失敗、再最小通過、最後重構

## 該做 / 不該做
**✅ 該做**
- 測**行為**（輸入→輸出/副作用），避免驗證實作細節
- 單測彼此獨立、可重複、秒級完成
- 對外依賴全部以 **Dummy/Stub/Mock/Fake/Spy** 隔離

**❌ 不該做**
- 依賴外部 I/O／框架啟動
- 追求覆蓋率而寫無意義測試
- 測太多內部實作，導致重構即壞
- 發現太難測，選擇用更簡單的測試執行（需要重新思考是否責任邊界清晰，是否符合分層思維）

## 命名與結構

tests/
unit/
application/
test_<use_case_or_service>.py

domain/
test_<aggregate_or_value_object_or_domain_service>.py

api/            # 只有當有可抽離的純邏輯（例如 DTO 驗證/mapping）才放
test_<dto_or_mapper>.py

infra/          # 只有當有可抽離的純邏輯（例如 retry 策略/批次切片）才放
test_<strategy_or_mapper>.py
conftest.py

- **檔名**：`test_<subject>.py`（例：`test_create_order_usecase.py`、`test_price_rules.py`）
- **類別**：`Test<Subject>`（例：`TestCreateOrderUseCase`）
- **測試方法**：`test_<行為>__<情境>__<預期>`
  例：`test_calc_discount__vip_customer__applies_highest_rule`
- **夾具（fixtures）**：集中於 `tests/unit/conftest.py`，避免重複樣板

## Test Double 規範
- **Dummy**：僅為滿足型別/參數（不被使用）
- **Stub**：回傳固定資料，消除不確定性（不可含邏輯）
- **Fake**：輕量可運作實作（如 in‑memory repo；僅限測試）
- **Mock**：驗證互動（呼叫次數/參數），僅對「協作契約」做斷言
- **Spy**：記錄呼叫以供事後驗證
**時間/亂數/ID** → 以注入（`clock/rng/id_gen`）方式固定化，避免 flakiness

### 範例：Stub 與 Mock (專案實例)

**情境：**
我們要測試 `AdminUserService` 的 `get_user` 方法。此方法會依賴 `UserRepository` 來從資料庫取得資料。在單元測試中，我們不希望真的連線資料庫，因此我們將建立一個 `StubUserRepository` 來回傳固定的假資料。

**被測試的程式碼：**
```python
# src/application/admin/user_service.py

from infrastructure.repositories.user.user_repository import UserRepository
# ... 其他 import

class AdminUserService:
    def __init__(self, user_repo: UserRepository, ...):
        self.user_repo = user_repo
        # ...

    async def get_user(self, user_id: str) -> Dict[str, Any]:
        # ...
        user = await self.user_repo.get_by_id(user_id)
        if not user:
            raise NotFoundException(f"用戶 {user_id} 不存在")

        user_with_role = await self.user_repo.get_by_email(user.email, include_role=True)
        # ...
        # (此處省略了將 user model 轉換為 dict 的程式碼)
        return formatted_user_dict
```

**Stub 範例（以固定回傳隔離 DB 依賴）**
```python
# tests/unit/application/admin/test_user_service.py

import pytest
from types import SimpleNamespace
from src.application.admin.user_service import AdminUserService

# 1. 建立 Stub Repository
class StubUserRepository:
    def __init__(self, user_data, user_with_role_data):
        self._user = user_data
        self._user_with_role = user_with_role_data

    async def get_by_id(self, user_id: str):
        # 回傳一個類似 SQLAlchemy model 的物件
        return SimpleNamespace(**self._user) if self._user else None

    async def get_by_email(self, email: str, include_role: bool = False):
        # 回傳一個包含角色的假物件
        return SimpleNamespace(**self._user_with_role) if self._user_with_role else None

# 2. 撰寫測試
@pytest.mark.asyncio
async def test_get_user__user_exists__returns_user_dict():
    # Arrange: 準備假資料和 Stub Repo
    fake_user = {"id": "user-123", "name": "Ada", "email": "ada@example.com"}
    fake_role = {"id": "role-456", "name": "Admin"}
    fake_user_with_role = {**fake_user, "role": SimpleNamespace(**fake_role)}

    stub_repo = StubUserRepository(
        user_data=fake_user,
        user_with_role_data=fake_user_with_role
    )

    # 注入 Stub Repo 來建立 Service
    user_service = AdminUserService(user_repo=stub_repo)

    # Act: 執行被測試的方法
    # (注意：為了簡化範例，我們假設 get_user 最後會返回一個包含 role_name 的 dict)
    result = await user_service.get_user("user-123")

    # Assert: 驗證結果是否符合預期
    assert result["id"] == "user-123"
    assert result["name"] == "Ada"
    assert result["role_name"] == "Admin"
```

**Mock 範例（驗證互動契約：呼叫次數與參數）**
```python
# tests/unit/application/admin/test_user_service_mock.py

import pytest
from unittest.mock import AsyncMock  # 使用 AsyncMock 來模擬 async 方法
from src.application.admin.user_service import AdminUserService

@pytest.mark.asyncio
async def test_get_user__user_exists__calls_repo_with_correct_id_and_email():
    # Arrange: 準備 Mock 和返回值
    mock_repo = AsyncMock()

    # 設定 get_by_id 的返回值
    mock_repo.get_by_id.return_value = AsyncMock(
        id="user-123",
        email="ada@example.com"
    )
    # 設定 get_by_email 的返回值
    mock_repo.get_by_email.return_value = AsyncMock(
        id="user-123",
        name="Ada Lovelace",
        email="ada@example.com",
        role=AsyncMock(id="role-456", name="Admin")
    )

    user_service = AdminUserService(user_repo=mock_repo)

    # Act: 執行
    await user_service.get_user("user-123")

    # Assert: 驗證與 Mock 的互動是否符合預期
    mock_repo.get_by_id.assert_called_once_with("user-123")
    mock_repo.get_by_email.assert_called_once_with("ada@example.com", include_role=True)
```

## 覆蓋率與品質門檻
- **Domain + Application** 的單元測行數覆蓋率建議 **≥ 85%**
- 以**情境覆蓋**（正常/邊界/錯誤）優先於追數字
- 覆蓋率**不是唯一 KPI**：同步觀察回歸缺陷率、缺陷攔截率

## 本機與 CI 執行
```bash
# 本機快速回饋（只跑單元測）
uv run pytest -q tests/unit

# 指定跑 Application/Domain 單元測（建議 CI 也這樣分層）
uv run pytest -m "unit and (application or domain)" -q

# 嚴格模式（第一個失敗即停止）
uv run pytest -m "unit" --maxfail=1 -q
```

## Code Review 清單
	•	僅驗證行為（輸入/輸出或可觀測副作用），未綁內部實作
	•	測試獨立、可重複、秒級完成（無外部 I/O）
	•	名稱能表達情境/預期，可讀性良好，失敗訊息清晰
	•	關鍵規則具備正常/邊界/錯誤三類情境
	•	對外依賴以 Stub/Mock/Fake 隔離；時間/亂數/ID 皆可注入
	•	重構不改對外行為時，測試不應大量壞掉


本專案測試分層適用範圍（重點：Unit Test 只針對 Application & Domain）

為避免測試漂移與維護成本膨脹，單元測試的主力戰場限定在 Application 與 Domain。
API/Infra 僅在有「可抽離的純邏輯」時才寫單元測，其餘以整合測守護。

## ✅ Unit Test 覆蓋重點
	•	Application 層
	•	用例流程（happy path / 分支 / 異常）
	•	與協作物（Repository、外部服務介面）的互動契約（以 Mock/Stub 驗證參數/次數）
	•	Domain 層
	•	業務規則與計算（含不變式、規則組合）
	•	值物件/聚合根/領域服務的行為與邊界

## ⚠️ Unit Test 僅在「可抽離純邏輯」時適用
	•	API 層：DTO 驗證（Pydantic validators）、序列化/反序列化 mapping、錯誤碼對照表
    路由/狀態碼/Headers/Middleware 請以 整合測 驗證

    •	Infra 層：retry/退避/熔斷策略、批次切片、mapper（如 ORM row → domain）
    真實 I/O/Schema/交易/連線池請以 整合測 驗證（建議用 Testcontainers）

## ❌ Unit Test 不覆蓋的內容（改由整合/E2E）
	•	任何需要啟動框架或外部 I/O才能驗證的行為（路由、中介層生命週期、真實 DB/HTTP/Queue）
	•	OpenAPI 相容性、錯誤回應結構 → 整合測（可用 Schema Diff / Snapshot）
	•	跨系統用戶旅程 → E2E
