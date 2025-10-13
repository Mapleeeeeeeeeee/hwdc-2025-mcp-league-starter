"""
Global exception handlers for FastAPI application.

This module provides centralized error handling following FastAPI best practices.
All exceptions are transformed into consistent JSON responses with trace IDs.
"""

from logging import getLogger
from typing import Any

from fastapi import HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from src.core.exceptions import BaseAppException

logger = getLogger(__name__)


async def base_app_exception_handler(
    request: Request, exc: BaseAppException
) -> JSONResponse:
    """
    Handle custom application exceptions.

    Transforms BaseAppException and its subclasses into consistent JSON responses
    with proper HTTP status codes, trace IDs, and context information.
    """
    trace_id = getattr(request.state, "trace_id", None)

    # Log the exception for monitoring
    logger.error(
        "Application exception occurred",
        extra={
            "trace_id": trace_id,
            "exception_type": exc.__class__.__name__,
            "status_code": exc.status_code,
            "detail": exc.detail,
            "context": exc.context,
            "path": request.url.path,
            "method": request.method,
        },
        exc_info=True,
    )

    # Prepare retry information if applicable
    retry_info: dict[str, Any] | None = None
    if hasattr(exc, "retryable") and exc.retryable:
        retry_info = {
            "retryable": True,
            "retry_after": getattr(exc, "retry_after", None),
            "max_retries": getattr(exc, "max_retries", 3),
            "current_attempt": getattr(request.state, "retry_attempt", 1),
        }

    response_content: dict[str, Any] = {
        "success": False,
        "error": {
            "type": exc.__class__.__name__,
            "message": exc.get_i18n_message(),
            "trace_id": trace_id,
            "context": exc.context if exc.context else None,
        },
    }

    # Include i18n information if available
    if hasattr(exc, "i18n_key") and exc.i18n_key:
        response_content["error"]["i18n_key"] = exc.i18n_key
    if hasattr(exc, "i18n_params") and exc.i18n_params:
        response_content["error"]["i18n_params"] = exc.i18n_params

    if retry_info:
        response_content["retry_info"] = retry_info

    return JSONResponse(
        status_code=exc.status_code, content=response_content, headers=exc.headers or {}
    )


async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """
    Handle FastAPI HTTP exceptions.

    Provides consistent error response format for built-in FastAPI HTTP exceptions.
    """
    trace_id = getattr(request.state, "trace_id", None)

    logger.warning(
        "HTTP exception occurred",
        extra={
            "trace_id": trace_id,
            "status_code": exc.status_code,
            "detail": exc.detail,
            "path": request.url.path,
            "method": request.method,
        },
    )

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": {
                "type": "HTTPException",
                "message": exc.detail,
                "trace_id": trace_id,
            },
        },
    )


async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """
    Handle request validation errors.

    Transforms Pydantic validation errors into user-friendly error messages
    while maintaining detailed error information for debugging.
    """
    trace_id = getattr(request.state, "trace_id", None)

    # Extract validation errors with more user-friendly formatting
    errors = []
    for error in exc.errors():
        field_path = " -> ".join(str(loc) for loc in error["loc"])
        errors.append(
            {
                "field": field_path,
                "message": error["msg"],
                "type": error["type"],
                "input": error.get("input"),
            }
        )

    logger.warning(
        "Request validation failed",
        extra={
            "trace_id": trace_id,
            "errors": errors,
            "path": request.url.path,
            "method": request.method,
        },
    )

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "success": False,
            "error": {
                "type": "ValidationError",
                "message": "Request validation failed",
                "trace_id": trace_id,
                "details": errors,
            },
        },
    )


async def starlette_http_exception_handler(
    request: Request, exc: StarletteHTTPException
) -> JSONResponse:
    """
    Handle Starlette HTTP exceptions.

    Catches HTTP exceptions that might escape from Starlette middleware
    and provides consistent error formatting.
    """
    trace_id = getattr(request.state, "trace_id", None)

    logger.warning(
        "Starlette HTTP exception occurred",
        extra={
            "trace_id": trace_id,
            "status_code": exc.status_code,
            "detail": exc.detail,
            "path": request.url.path,
            "method": request.method,
        },
    )

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": {
                "type": "StarletteHTTPException",
                "message": exc.detail,
                "trace_id": trace_id,
            },
        },
    )


async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Handle unexpected exceptions.

    Catches any unhandled exceptions and provides a generic error response
    while logging the full exception details for investigation.
    """
    trace_id = getattr(request.state, "trace_id", None)

    logger.error(
        "Unhandled exception occurred",
        extra={
            "trace_id": trace_id,
            "exception_type": exc.__class__.__name__,
            "path": request.url.path,
            "method": request.method,
        },
        exc_info=True,
    )

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "success": False,
            "error": {
                "type": "InternalServerError",
                "message": "An unexpected error occurred. Please try again later.",
                "trace_id": trace_id,
            },
        },
    )


def register_exception_handlers(app) -> None:
    """
    Register all exception handlers with the FastAPI application.

    Args:
        app: FastAPI application instance
    """
    app.add_exception_handler(BaseAppException, base_app_exception_handler)
    app.add_exception_handler(HTTPException, http_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(StarletteHTTPException, starlette_http_exception_handler)
    app.add_exception_handler(Exception, unhandled_exception_handler)
