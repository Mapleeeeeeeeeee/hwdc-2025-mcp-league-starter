# Error Handling Development Guide

## 系統架構

### 已自動配置
- **TraceMiddleware**: 自動生成 trace_id
- **Exception Handlers**: 統一錯誤響應格式
- **API Response Wrappers**: 標準化成功響應
- **重試機制**: 自動處理可重試錯誤
- **i18n 支援**: 預留國際化鍵值和參數插值

### 關鍵必看檔案
- `core/exceptions.py` - 基礎異常類定義 (查看可用錯誤類型)
- `api/exception_handlers.py` - 全域異常處理器
- `shared/response.py` - 統一響應格式
- `shared/exceptions/` - 通用業務異常類

## 開發模式

### Service 層
```python
# 推薦使用 shared/exceptions 中的通用異常
from shared.exceptions import UserNotFoundError, ResourceAlreadyExistsError

class UserService:
    def get_user_by_id(self, user_id: int) -> User:
        user = self.repository.find_by_id(user_id)
        if not user:
            raise UserNotFoundError(user_id=user_id)
        return user

    def create_user(self, email: str) -> User:
        if self.repository.exists_by_email(email):
            raise ResourceAlreadyExistsError(
                resource_type="User",
                identifier=email
            )
        return self.repository.create(email)

# 或者使用 core/exceptions 中的基礎異常
from core.exceptions import NotFoundError, ConflictError

class DocumentService:
    def get_document(self, doc_id: str) -> Document:
        document = self.repository.find_by_id(doc_id)
        if not document:
            raise NotFoundError(
                f"Document {doc_id} not found",
                context={"document_id": doc_id},
                i18n_key="errors.document.not_found"
            )
        return document
```

### API 層
```python
from shared.response import create_success_response, APIResponse

@router.get("/users/{user_id}")
async def get_user(user_id: int) -> APIResponse[User]:
    user = user_service.get_user_by_id(user_id)  # 錯誤自動處理
    return create_success_response(data=user)
```

### 第三方 API 包裝
```python
import openai
from core.exceptions import ServiceUnavailableError, TooManyRequestsError

async def call_llm(prompt: str) -> str:
    try:
        response = await openai.ChatCompletion.acreate(...)
        return response.choices[0].message.content
    except openai.RateLimitError:
        raise TooManyRequestsError(
            "LLM quota exceeded",
            context={"provider": "openai"},
            i18n_key="errors.llm.quota_exceeded"
        )
    except openai.ServiceUnavailableError:
        raise ServiceUnavailableError(
            "LLM service unavailable",
            context={"provider": "openai"},
            i18n_key="errors.llm.service_unavailable"
        )
```

## 自定義錯誤

### 通用業務異常 (shared/exceptions/)
```python
# shared/exceptions/__init__.py
from shared.exceptions import UserNotFoundError, DocumentNotFoundError

# 這些是跨模組共用的通用異常
raise UserNotFoundError(user_id="123")
raise DocumentNotFoundError(document_id="doc-456")
```

### 業務特定錯誤 (功能模組下)
```python
# services/document/exceptions.py
from core.exceptions import ConflictError, ServiceUnavailableError

class DocumentProcessingConflictError(ConflictError):
    """文件正在處理中衝突"""
    def __init__(self, doc_id: str, current_status: str, **kwargs):
        super().__init__(
            detail=f"Document {doc_id} is currently being processed",
            context={
                "document_id": doc_id,
                "current_status": current_status,
                "suggestion": "Wait for current processing to complete"
            },
            i18n_key="errors.document.processing_conflict",
            i18n_params={"document_id": doc_id, "status": current_status},
            **kwargs
        )

class LLMServiceUnavailableError(ServiceUnavailableError):
    """LLM 服務不可用"""
    def __init__(self, provider: str, **kwargs):
        super().__init__(
            detail=f"LLM service from {provider} is temporarily unavailable",
            context={"provider": provider, "estimated_recovery": "5 minutes"},
            i18n_key="errors.llm.service_unavailable",
            i18n_params={"provider": provider},
            **kwargs
        )
```

### 使用方式
```python
class DocumentService:
    def summarize_document(self, doc_id: str) -> DocumentSummary:
        doc = self.get_document(doc_id)

        # 檢查文件狀態衝突
        if doc.status == "processing":
            raise DocumentProcessingConflictError(doc_id, doc.status)

        try:
            return await llm_service.summarize(doc.content)
        except ConnectionError:
            raise LLMServiceUnavailableError("openai")
```

## 異常類型選擇

### 🎯 **優先使用 shared/exceptions/ - 更好的前端本地化支援**

#### ✅ **推薦：使用繼承重寫 i18n key 的異常**
```python
# ✅ 推薦：具體異常 + 精準 i18n
from shared.exceptions import UserNotFoundError, PermissionDeniedError

def get_user(user_id: int):
    user = repo.find_by_id(user_id)
    if not user:
        raise UserNotFoundError(user_id=user_id)
        # i18n_key: "errors.user.not_found"
        # i18n_params: {"user_id": "123"}
    return user

def check_permission(user_id: int, resource: str):
    if not has_permission(user_id, resource):
        raise PermissionDeniedError(
            resource=resource,
            action="access",
            user_id=user_id
        )
        # i18n_key: "errors.permission.denied"
        # i18n_params: {"resource": "document", "action": "access"}
```

#### ❌ **避免：使用基礎通用異常**
```python
# ❌ 不推薦：泛用異常，難以本地化
from core.exceptions import NotFoundError

def get_user(user_id: int):
    user = repo.find_by_id(user_id)
    if not user:
        raise NotFoundError("User not found")
        # i18n_key: "errors.notfounderror" (太泛用)
        # 前端難以區分是用戶不存在還是其他資源不存在
    return user
```

#### 🎨 **前端本地化優勢**
```javascript
// 前端可以精準處理不同錯誤類型
if (error.type === 'UserNotFoundError') {
    // 顯示用戶不存在的特定UI
    showUserNotFoundDialog(error.i18n_params.user_id);
    // 中文: "找不到用戶 123"
    // 英文: "User 123 was not found"
} else if (error.type === 'DocumentNotFoundError') {
    // 顯示文件不存在的特定UI
    showDocumentNotFoundDialog(error.i18n_params.document_id);
} else if (error.type === 'PermissionDeniedError') {
    // 顯示權限不足的特定UI
    showPermissionDeniedDialog(
        error.i18n_params.resource,
        error.i18n_params.action
    );
}
```

### 特定場景使用 core/exceptions/
```python
# ✅ 適用：業務特定的錯誤邏輯
from core.exceptions import BadRequestError, UnprocessableEntityError

def validate_file(file):
    if not file:
        raise BadRequestError("File is required")

    if file.size > MAX_SIZE:
        raise UnprocessableEntityError(
            f"File too large: {file.size} > {MAX_SIZE}",
            context={"file_size": file.size, "max_size": MAX_SIZE}
        )
```

## 國際化 (i18n) 支援

### 🎯 **繼承重寫 i18n key - 更好的前端本地化**

#### ✅ **推薦：使用 shared/exceptions/ 的具體異常**
```python
# 自動提供精準的 i18n key 和參數
from shared.exceptions import UserNotFoundError, PermissionDeniedError

raise UserNotFoundError(user_id="123")
# i18n_key: "errors.user.not_found"
# i18n_params: {"user_id": "123"}
# 前端可以精準本地化： "找不到用戶 123"

raise PermissionDeniedError(resource="document", action="delete", user_id="456")
# i18n_key: "errors.permission.denied"
# i18n_params: {"resource": "document", "action": "delete"}
# 前端可以精準本地化： "權限不足：無法刪除文件"
```

#### ❌ **避免：手動設定泛用 i18n key**
```python
# 不推薦：需要手動設定，容易出錯
from core.exceptions import NotFoundError

raise NotFoundError(
    detail="User 123 not found",
    i18n_key="errors.user.not_found",  # 需要手動設定
    i18n_params={"user_id": "123"}     # 需要手動設定
)
# 容易忘記設定或設定錯誤
```

### 📋 **i18n 訊息範例**

#### **英文訊息範本**
```json
{
  "errors.user.not_found": "User {user_id} was not found",
  "errors.document.not_found": "Document {document_id} was not found",
  "errors.permission.denied": "Permission denied: cannot {action} {resource}",
  "errors.resource.already_exists": "{resource_type} with identifier '{identifier}' already exists"
}
```

#### **中文訊息範本**
```json
{
  "errors.user.not_found": "找不到用戶 {user_id}",
  "errors.document.not_found": "找不到文件 {document_id}",
  "errors.permission.denied": "權限不足：無法{action} {resource}",
  "errors.resource.already_exists": "{resource_type} 識別碼 '{identifier}' 已存在"
}
```

### 🔧 **自定義異常的 i18n**
```python
# services/document/exceptions.py
from core.exceptions import ConflictError

class DocumentProcessingConflictError(ConflictError):
    """文件正在處理中衝突"""
    def __init__(self, doc_id: str, current_status: str, **kwargs):
        super().__init__(
            detail=f"Document {doc_id} is currently being processed",
            i18n_key="errors.document.processing_conflict",
            i18n_params={
                "document_id": doc_id,
                "status": current_status
            },
            context={
                "document_id": doc_id,
                "current_status": current_status,
                "suggestion": "Wait for current processing to complete"
            },
            **kwargs
        )
```

### ⚡ **參數插值規則**
- 所有參數值都會轉換為字串
- 使用 `{param_name}` 語法進行插值
- 支援巢狀參數和複雜的訊息格式

## 重試機制

### 自動重試設定
```python
# 這些異常預設為可重試
from core.exceptions import TooManyRequestsError, ServiceUnavailableError

# TooManyRequestsError (429) - 預設 60秒後重試，最多5次
raise TooManyRequestsError("Rate limit exceeded")

# ServiceUnavailableError (503) - 預設 30秒後重試，最多3次
raise ServiceUnavailableError("Service temporarily unavailable")
```

### 自定義重試配置
```python
raise ServiceUnavailableError(
    "Database connection failed",
    retryable=True,
    retry_after=10,    # 10秒後重試
    max_retries=5      # 最多重試5次
)

# 不可重試的錯誤
raise BadRequestError(
    "Invalid input format",
    retryable=False    # 明確標記為不可重試
)
```

## 重要提醒

1. **🎯 優先使用 shared/exceptions/** - 提供精準的 i18n key 和參數，讓前端更好地本地化
2. **🔍 具體異常類型** - 使用 `UserNotFoundError` 而非泛用的 `NotFoundError`，前端可以區分處理
3. **🌐 i18n 參數完整性** - 確保所有變數都包含在 `i18n_params` 中，支援動態訊息插值
4. **📱 前端友好** - 異常類型和 i18n 參數設計應考慮前端的處理需求
5. **Context 安全** - 不包含密碼、token 等敏感資訊
6. **重試設定** - 只對可恢復錯誤設定 `retryable=True`
7. **Trace ID** - 系統自動處理，可用 `request.state.trace_id` 取得
8. **統一響應** - API 成功響應使用 `create_success_response()`

## 錯誤響應格式

系統自動生成：
```json
{
  "success": false,
  "data": null,
  "error": {
    "type": "UserNotFoundError",
    "message": "User 123 not found",
    "trace_id": "abc-123-def-456",
    "context": {"user_id": 123}
  },
  "retry_info": {
    "retryable": false,
    "retry_after": null,
    "max_retries": 0
  }
}
```

## 架構決策

### shared/exceptions/ vs 各模組 exceptions/
- **shared/exceptions/**: 放跨模組通用異常，避免重複定義，提供精準的 i18n 支援
- **各模組 exceptions/**: 放該模組特有的業務邏輯異常，需要自定義 i18n key
- **core/exceptions/**: 保持HTTP基礎異常，專注於狀態碼映射，i18n 支援有限

### 🎨 **i18n 設計原則**
- **具體異常類型**: 使用 `UserNotFoundError` 而非 `NotFoundError`，提供精準的 i18n key
- **完整參數支援**: 所有變數都應包含在 `i18n_params` 中，支援動態訊息插值
- **前端友好**: 設計時考慮前端的錯誤處理和本地化需求
- **一致性**: 遵循 `errors.{module}.{action}` 的鍵值命名規範

### 選擇原則
- 如果錯誤可能被多個模組使用 → `shared/exceptions/` (最佳 i18n 支援)
- 如果錯誤只屬於特定業務邏輯 → 模組內部 `exceptions.py`
- 如果只是簡單的HTTP狀態碼映射 → `core/exceptions/`
- 如果需要精準的前端本地化 → 必須使用具體異常類型
