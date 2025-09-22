"""
Permission and authorization business exceptions for HWDC 2025 MCP League Starter.

Contains exceptions specific to permission checking, authentication, and access control.
"""

from src.core.exceptions import ForbiddenError, UnauthorizedError


class PermissionDeniedError(ForbiddenError):
    """
    Exception raised when a user doesn't have permission for a specific action.

    Generic permission error that can be used across different resources.
    """

    def __init__(
        self, resource: str, action: str, user_id: str | int | None = None, **kwargs
    ):
        super().__init__(
            detail=f"Permission denied: cannot {action} {resource}",
            i18n_key="errors.permission.denied",
            i18n_params={
                "resource": resource,
                "action": action,
                "user_id": str(user_id) if user_id else None,
            },
            context={"resource": resource, "action": action, "user_id": user_id},
            **kwargs,
        )


class AuthenticationRequiredError(UnauthorizedError):
    """
    Exception raised when authentication is required but not provided.

    More specific than generic UnauthorizedError for authentication flows.
    """

    def __init__(self, resource: str | None = None, **kwargs):
        detail = "Authentication required"
        if resource:
            detail = f"Authentication required to access {resource}"

        super().__init__(
            detail=detail,
            i18n_key="errors.auth.required",
            i18n_params={"resource": resource} if resource else {},
            context={"resource": resource} if resource else None,
            **kwargs,
        )


__all__ = [
    "PermissionDeniedError",
    "AuthenticationRequiredError",
]
