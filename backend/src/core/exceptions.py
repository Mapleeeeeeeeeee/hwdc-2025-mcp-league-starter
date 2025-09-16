from typing import Any

from fastapi import HTTPException


class BaseAppException(HTTPException):
    """
    Base application exception class.

    All custom application exceptions should inherit from this class.
    Provides standardized error handling with i18n support and context.
    """

    def __init__(
        self,
        detail: str,
        status_code: int = 500,
        headers: dict[str, Any] | None = None,
        i18n_key: str | None = None,
        context: dict[str, Any] | None = None,
    ):
        super().__init__(status_code=status_code, detail=detail, headers=headers)
        self.i18n_key = i18n_key or f"errors.{self.__class__.__name__.lower()}"
        self.context = context or {}

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
        super().__init__(detail=detail, status_code=503, **kwargs)


class GatewayTimeoutError(ServerError):
    """504 Gateway Timeout"""

    def __init__(self, detail: str = "Gateway timeout", **kwargs):
        super().__init__(detail=detail, status_code=504, **kwargs)
