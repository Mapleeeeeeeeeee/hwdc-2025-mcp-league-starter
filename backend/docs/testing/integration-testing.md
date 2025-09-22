# 整合測試原則與實務（Integration Testing Guide）

> 目標：以少量高價值整合測，覆蓋框架啟動、跨模組協作與對外依賴，守護 API 契約、錯誤轉譯與資料一致性。

## 目錄
- [核心目的](#核心目的)
- [範圍界定](#範圍界定)
- [原則](#原則)
- [該做 / 不該做](#該做--不該做)
- [命名與結構](#命名與結構)
- [依賴與環境啟動策略](#依賴與環境啟動策略)
- [契約測試](#契約測試)
- [故障注入與恢復](#故障注入與恢復)
- [交易與資料一致性（回滾）](#交易與資料一致性回滾)
- [測試資料與 fixtures 策略](#測試資料與-fixtures-策略)
- [執行與標記](#執行與標記)
- [CI Gate 與品質門檻](#ci-gate-與品質門檻)
- [安全與祕密管理](#安全與祕密管理)
- [可觀測性與量化指標](#可觀測性與量化指標)
- [常見範例](#常見範例)
- [Code Review 清單](#code-review-清單)
- [品質門檻](#品質門檻)

## 核心目的
- 驗證系統組件在真實框架與 I/O 下的**協作行為**：FastAPI 中間件、依賴注入、路由、資料庫交易。
- 以**API 契約**與**錯誤轉譯**為主，確保 `core.errors` 的標準化錯誤包在各層一致。
- 補足單元測無法覆蓋的跨模組風險，提供升級（FastAPI/SQLAlchemy/httpx）與重構的安全網。

## 範圍界定
- 需要啟動 FastAPI 應用或其子路由，包含中間件鏈：
  - `src/api/server.py`（完整應用）或特定路由模組（如 `src/api/router/admin/role_router.py`）。
- 涉及真實 I/O 或框架功能：
  - 資料庫：`src/infrastructure/database/postgresql.py`（SQLAlchemy + asyncpg/psycopg2-binary）。
  - 中間件：`exception_middleware`、`jwt_middleware`、`rate_limit_middleware`、`https_middleware`、`security_headers_middleware`。
  - 對外服務邊界：Google OAuth（`infrastructure/auth/google_oauth_client.py`）、GCP KMS/Secret Manager、OpenAI/Anthropic/Gemini（Domain 層）。
- 不做瀏覽器端到端流程，該類測試歸 E2E。

## 原則
- 可重現：測試資料與外部依賴由 fixture 控制（容器化 DB、依賴注入或 monkeypatch）。
- 與開發環境隔離：用 Testcontainers 啟動臨時 Postgres；不依賴本機 DB/雲端資源。
- 少量高價值：集中在契約穩定性、錯誤轉譯、交易一致性、關鍵中間件行為。
- 契約為先：OpenAPI schema 與錯誤包（`core.errors`）優先防守，禁止破壞性變更未經審核合併。

## 該做 / 不該做
**✅ 該做**
- 啟動 FastAPI 應用（含中間件）驗證路由與錯誤處理（例：`/admin/roles`、`/ratings`）。
- 以 Testcontainers 啟動 Postgres，跑 Repository ↔ DB 實作（`SQLAlchemyAgentRepository`、`SessionEvaluationRatingRepository`）。
- 對外呼叫以依賴注入/monkeypatch 模擬（例：`GoogleOAuthClient.get_user_info_from_callback`）。
- 驗證 `exception_middleware` 與 `ExceptionHandlers` 的錯誤包與 `X-Trace-ID`、`X-Process-Time` 標頭。

**❌ 不該做**
- 實連第三方雲服務（Google OAuth、KMS、OpenAI 等）；請以測試 doubles 或超時/錯誤注入替代。
- 在整合測中覆蓋細節邏輯（那是單元測範疇）。
- 依賴本機長期 state（每次測試需可獨立重跑）。

## 命名與結構

tests/
integration/
api/
admin/
roles/
middleware/
repo/
external/
contract/
conftest.py

- 子目錄建議：
  - `api/`：路由整合（例：`admin/roles/`、`rating/`、`stages/`）。
  - `middleware/`：`exception_middleware`、`jwt_middleware`、`rate_limit_middleware` 行為。
  - `repo/`：Repository ↔ DB（migration/seed + 操作 + 交易驗證）。
  - `external/`：對外 HTTP/SDK 的 CDC 或故障注入。
  - `contract/`：OpenAPI schema snapshot/diff 與錯誤包 snapshot。
- 測試函式命名：`test_<行為>__<情境>__<預期>` 例：`test_list_roles__authorized__returns_200_and_schema_ok`（與 unit-testing 命名規則對齊）。

## 依賴與環境啟動策略

本專案使用 Python 3.12、FastAPI（pyproject 指定 >=0.115.12）、SQLAlchemy 2.x、asyncpg/psycopg2-binary；資料庫為 PostgreSQL。建議以 Testcontainers 啟動 Postgres，避免污染本機環境。

## 如何執行
```bash
uv run pytest -q tests/integration
```

- 建議開發相依（dev）：
  - `testcontainers[postgresql]`
  - `syrupy`（契約/錯誤回應 snapshot）

範例：Session-scope Postgres 容器 + migration/seed（以實際模型）

```python
# tests/integration/conftest.py（建議新增）
import os
import asyncio
import pytest
from testcontainers.postgres import PostgresContainer
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from src.api.server import app
from src.infrastructure.database.models import Base

@pytest.fixture(scope="session")
def pg_container():
    # 選用與本地/雲端一致的版本（README 要求 PG >=12；建議 15）
    with PostgresContainer("postgres:15-alpine") as pg:
        os.environ["DATABASE_URL_SYNC"] = pg.get_connection_url().replace("postgresql://", "postgresql+psycopg2://")
        os.environ["DATABASE_URL_ASYNC"] = pg.get_connection_url().replace("postgresql://", "postgresql+asyncpg://")
        yield pg

@pytest.fixture(scope="session")
async def async_engine(pg_container):
    engine = create_async_engine(os.environ["DATABASE_URL_ASYNC"], future=True)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()

@pytest.fixture(scope="function")
async def db_session(async_engine):
    SessionLocal = async_sessionmaker(async_engine, class_=AsyncSession, expire_on_commit=False)
    async with SessionLocal() as session:
        yield session
        # 清理資料（依測試策略，可選擇每測清理/每 worker schema）
        await session.rollback()
