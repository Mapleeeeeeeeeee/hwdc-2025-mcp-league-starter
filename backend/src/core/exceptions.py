from typing import Any

from fastapi import HTTPException


class BaseAppException(HTTPException):
    """
    Base application exception class.

    All custom application exceptions should inherit from this class.
    Provides standardized error handling with i18n support, context,
    and retry capabilities.

    Args:
        detail: Human-readable error message
        status_code: HTTP status code
        headers: Optional HTTP headers to include in response
        i18n_key: Internationalization key for error message
        i18n_params: Parameters for i18n message interpolation
        context: Additional context information for debugging
        retryable: Whether this error can be retried
        retry_after: Suggested retry delay in seconds
        max_retries: Maximum number of retry attempts
    """

    def __init__(
        self,
        detail: str,
        status_code: int = 500,
        headers: dict[str, Any] | None = None,
        i18n_key: str | None = None,
        i18n_params: dict[str, Any] | None = None,
        context: dict[str, Any] | None = None,
        retryable: bool = False,
        retry_after: int | None = None,
        max_retries: int = 3,
    ):
        super().__init__(status_code=status_code, detail=detail, headers=headers)
        self.i18n_key = i18n_key or f"errors.{self.__class__.__name__.lower()}"
        self.i18n_params = i18n_params or {}
        self.context = context or {}
        self.retryable = retryable
        self.retry_after = retry_after
        self.max_retries = max_retries

    def get_i18n_message(self, lang: str = "en") -> str:
        """
        Get internationalized error message.

        Args:
            lang: Language code (e.g., 'en', 'zh-TW')

        Returns:
            Localized error message or fallback to detail
        """
        # TODO: Implement i18n lookup when i18n module is ready
        return self.detail


class ClientError(BaseAppException):
    """Base class for 4XX client errors."""

    def __init__(self, detail: str, status_code: int = 400, **kwargs):
        super().__init__(detail=detail, status_code=status_code, **kwargs)


class ServerError(BaseAppException):
    """Base class for 5XX server errors."""

    def __init__(self, detail: str, status_code: int = 500, **kwargs):
        super().__init__(detail=detail, status_code=status_code, **kwargs)


# Common 4XX Client Errors
class BadRequestError(ClientError):
    """400 Bad Request"""

    def __init__(self, detail: str = "Bad request", **kwargs):
        super().__init__(detail=detail, status_code=400, **kwargs)


class UnauthorizedError(ClientError):
    """401 Unauthorized"""

    def __init__(self, detail: str = "Unauthorized", **kwargs):
        super().__init__(detail=detail, status_code=401, **kwargs)


class ForbiddenError(ClientError):
    """403 Forbidden"""

    def __init__(self, detail: str = "Forbidden", **kwargs):
        super().__init__(detail=detail, status_code=403, **kwargs)


class NotFoundError(ClientError):
    """404 Not Found"""

    def __init__(self, detail: str = "Resource not found", **kwargs):
        super().__init__(detail=detail, status_code=404, **kwargs)


class ConflictError(ClientError):
    """409 Conflict"""

    def __init__(self, detail: str = "Resource conflict", **kwargs):
        super().__init__(detail=detail, status_code=409, **kwargs)


class UnprocessableEntityError(ClientError):
    """422 Unprocessable Entity"""

    def __init__(self, detail: str = "Unprocessable entity", **kwargs):
        super().__init__(detail=detail, status_code=422, **kwargs)


class TooManyRequestsError(ClientError):
    """429 Too Many Requests"""

    def __init__(self, detail: str = "Too many requests", **kwargs):
        # Rate limit errors are typically retryable
        kwargs.setdefault("retryable", True)
        kwargs.setdefault("retry_after", 60)  # Default 1 minute retry delay
        kwargs.setdefault("max_retries", 5)
        super().__init__(detail=detail, status_code=429, **kwargs)


# Common 5XX Server Errors
class InternalServerError(ServerError):
    """500 Internal Server Error"""

    def __init__(self, detail: str = "Internal server error", **kwargs):
        super().__init__(detail=detail, status_code=500, **kwargs)


class BadGatewayError(ServerError):
    """502 Bad Gateway"""

    def __init__(self, detail: str = "Bad gateway", **kwargs):
        super().__init__(detail=detail, status_code=502, **kwargs)


class ServiceUnavailableError(ServerError):
    """503 Service Unavailable"""

    def __init__(self, detail: str = "Service temporarily unavailable", **kwargs):
        # Service unavailable errors are typically retryable
        kwargs.setdefault("retryable", True)
        kwargs.setdefault("retry_after", 30)  # Default 30 seconds retry delay
        kwargs.setdefault("max_retries", 3)
        super().__init__(detail=detail, status_code=503, **kwargs)


class GatewayTimeoutError(ServerError):
    """504 Gateway Timeout"""

    def __init__(self, detail: str = "Gateway timeout", **kwargs):
        # Timeout errors are typically retryable
        kwargs.setdefault("retryable", True)
        kwargs.setdefault("retry_after", 30)  # Default 30 seconds retry delay
        kwargs.setdefault("max_retries", 3)
        super().__init__(detail=detail, status_code=504, **kwargs)


class TooManyToolsError(BadRequestError):
    """400 Bad Request - Too many tools"""

    def __init__(
        self,
        detail: str = (
            "The number of active tools has exceeded the provider's limit. "
            "Please disable some tools and try again."
        ),
        **kwargs,
    ):
        kwargs.setdefault("i18n_key", "errors.tooManyTools")
        super().__init__(detail=detail, **kwargs)
