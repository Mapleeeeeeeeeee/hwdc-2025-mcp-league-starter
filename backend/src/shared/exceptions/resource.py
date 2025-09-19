"""
Resource and quota business exceptions for HWDC 2025 MCP League Starter.

Contains exceptions specific to resource management, quotas, and resource conflicts.
"""

from src.core.exceptions import ConflictError


class ResourceAlreadyExistsError(ConflictError):
    """
    Exception raised when trying to create a resource that already exists.

    Generic resource conflict error for any type of resource.
    """

    def __init__(self, resource_type: str, identifier: str, **kwargs):
        super().__init__(
            detail=f"{resource_type} with identifier '{identifier}' already exists",
            i18n_key="errors.resource.already_exists",
            i18n_params={"resource_type": resource_type, "identifier": identifier},
            context={"resource_type": resource_type, "identifier": identifier},
            **kwargs,
        )


class QuotaExceededError(ConflictError):
    """
    Exception raised when a user or resource has exceeded its quota/limits.

    Common usage: rate limiting, storage limits, API usage limits, etc.
    """

    def __init__(
        self, quota_type: str, current_usage: int | float, limit: int | float, **kwargs
    ):
        super().__init__(
            detail=f"{quota_type} quota exceeded: {current_usage}/{limit}",
            i18n_key="errors.quota.exceeded",
            i18n_params={
                "quota_type": quota_type,
                "current_usage": str(current_usage),
                "limit": str(limit),
            },
            context={
                "quota_type": quota_type,
                "current_usage": current_usage,
                "limit": limit,
            },
            **kwargs,
        )


__all__ = [
    "ResourceAlreadyExistsError",
    "QuotaExceededError",
]
