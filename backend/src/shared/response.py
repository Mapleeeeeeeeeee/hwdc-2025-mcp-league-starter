"""
API response wrapper models for consistent response formatting.

Provides standardized response structures for all API endpoints,
ensuring consistent client-server communication patterns.
"""

from typing import Any, TypeVar

from pydantic import BaseModel, ConfigDict, Field

T = TypeVar("T")


class BaseResponse(BaseModel):
    """
    Base response model with common configuration.

    Provides consistent configuration for all response models.
    """

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "success": True,
                    "data": {"key": "value"},
                    "message": "OK",
                    "trace_id": "abc-123-def-456",
                }
            ]
        }
    )


class APIResponse[T](BaseResponse):
    """
    Standard API response wrapper.

    Provides a consistent structure for all API responses with success status,
    optional data payload, message, and trace ID for debugging.
    """

    success: bool = Field(description="Indicates whether the request was successful")
    data: T | None = Field(default=None, description="Response payload data")
    message: str = Field(default="OK", description="Human-readable response message")
    trace_id: str | None = Field(
        default=None, description="Unique request identifier for debugging"
    )


class PaginationMeta(BaseResponse):
    """
    Pagination metadata for paginated responses.

    Contains information about current page, total items, and navigation.
    """

    current_page: int = Field(ge=1, description="Current page number (1-based)")
    page_size: int = Field(ge=1, le=100, description="Number of items per page")
    total_items: int = Field(ge=0, description="Total number of items across all pages")
    total_pages: int = Field(ge=0, description="Total number of pages")
    has_next: bool = Field(description="Whether there is a next page")
    has_previous: bool = Field(description="Whether there is a previous page")

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "current_page": 2,
                    "page_size": 20,
                    "total_items": 150,
                    "total_pages": 8,
                    "has_next": True,
                    "has_previous": True,
                }
            ]
        }
    )


class PaginatedResponse(APIResponse[list[T]]):
    """
    Paginated API response wrapper.

    Extends APIResponse to include pagination metadata for responses
    that return lists of items with pagination support.
    """

    pagination: PaginationMeta | None = Field(
        default=None, description="Pagination metadata"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "success": True,
                    "data": [{"id": 1, "name": "Item 1"}, {"id": 2, "name": "Item 2"}],
                    "message": "Items retrieved successfully",
                    "trace_id": "abc-123-def-456",
                    "pagination": {
                        "current_page": 1,
                        "page_size": 20,
                        "total_items": 2,
                        "total_pages": 1,
                        "has_next": False,
                        "has_previous": False,
                    },
                }
            ]
        }
    )


class ErrorDetail(BaseModel):
    """
    Error detail information.

    Provides structured error information including type, message, and context.
    """

    type: str = Field(description="Error type or classification")
    message: str = Field(description="Human-readable error message")
    trace_id: str | None = Field(
        default=None, description="Unique request identifier for debugging"
    )
    context: dict[str, Any] | None = Field(
        default=None, description="Additional context information for debugging"
    )
    details: list[dict[str, Any]] | None = Field(
        default=None, description="Detailed error information (e.g., validation errors)"
    )


class RetryInfo(BaseResponse):
    """
    Retry information for recoverable errors.

    Provides guidance on whether and how to retry failed requests.
    """

    retryable: bool = Field(description="Whether the operation can be retried")
    retry_after: int | None = Field(
        default=None, description="Suggested retry delay in seconds"
    )
    max_retries: int = Field(
        default=3, ge=0, description="Maximum number of retry attempts"
    )
    current_attempt: int = Field(default=1, ge=1, description="Current attempt number")

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "retryable": True,
                    "retry_after": 30,
                    "max_retries": 3,
                    "current_attempt": 1,
                }
            ]
        }
    )


class ErrorResponse(BaseResponse):
    """
    Error response wrapper.

    Standardized error response format with detailed error information
    and optional retry guidance.
    """

    success: bool = Field(default=False, description="Always False for error responses")
    data: None = Field(default=None, description="Always None for error responses")
    message: str = Field(default="Request failed", description="Error message")
    trace_id: str | None = Field(default=None, description="Request trace ID")
    error: ErrorDetail = Field(description="Detailed error information")
    retry_info: RetryInfo | None = Field(
        default=None, description="Retry guidance for recoverable errors"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "success": False,
                    "data": None,
                    "message": "Request failed",
                    "trace_id": "abc-123-def-456",
                    "error": {
                        "type": "NotFoundError",
                        "message": "User not found",
                        "trace_id": "abc-123-def-456",
                        "context": {"user_id": 123},
                    },
                    "retry_info": {
                        "retryable": False,
                        "retry_after": None,
                        "max_retries": 0,
                        "current_attempt": 1,
                    },
                }
            ]
        }
    )


def create_success_response[T](
    data: T | None = None, message: str = "OK", trace_id: str | None = None
) -> APIResponse[T]:
    """
    Create a standardized success response.

    Args:
        data: Response payload
        message: Success message
        trace_id: Request trace ID

    Returns:
        Standardized success response
    """
    return APIResponse[T](success=True, data=data, message=message, trace_id=trace_id)


def create_paginated_response[T](
    data: list[T],
    pagination_meta: PaginationMeta,
    message: str = "OK",
    trace_id: str | None = None,
) -> PaginatedResponse[T]:
    """
    Create a standardized paginated response.

    Args:
        data: List of items for current page
        pagination_meta: Pagination metadata
        message: Success message
        trace_id: Request trace ID

    Returns:
        Standardized paginated response
    """
    return PaginatedResponse[T](
        success=True,
        data=data,
        message=message,
        trace_id=trace_id,
        pagination=pagination_meta,
    )
