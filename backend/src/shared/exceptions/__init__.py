# Import all business exceptions from their respective modules
from .document import (
    DocumentAccessDeniedError,
    DocumentLockedError,
    DocumentNotFoundError,
)
from .llm import (
    LLMProviderNotConfiguredError,
    LLMProviderUnsupportedError,
)
from .permission import (
    AuthenticationRequiredError,
    PermissionDeniedError,
)
from .resource import (
    QuotaExceededError,
    ResourceAlreadyExistsError,
)
from .user import (
    UserAccessDeniedError,
    UserAlreadyExistsError,
    UserNotFoundError,
)
from .validation import (
    InvalidInputError,
    ValidationError,
)

# ============================================================================
# 📤 EXPORT ALL EXCEPTIONS
# ============================================================================

__all__ = [
    # User-related exceptions
    "UserNotFoundError",
    "UserAlreadyExistsError",
    "UserAccessDeniedError",
    # Document-related exceptions
    "DocumentNotFoundError",
    "DocumentAccessDeniedError",
    "DocumentLockedError",
    # LLM provider exceptions
    "LLMProviderNotConfiguredError",
    "LLMProviderUnsupportedError",
    # Permission & Authorization exceptions
    "PermissionDeniedError",
    "AuthenticationRequiredError",
    # Resource & Quota exceptions
    "ResourceAlreadyExistsError",
    "QuotaExceededError",
    # Validation exceptions
    "InvalidInputError",
    "ValidationError",
]
