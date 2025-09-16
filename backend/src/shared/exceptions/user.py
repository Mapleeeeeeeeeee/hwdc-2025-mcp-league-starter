"""
User-related business exceptions for HWDC 2025 MCP League Starter.

Contains exceptions specific to user management, authentication,
and user-related operations.
"""

from core.exceptions import ConflictError, ForbiddenError, NotFoundError


class UserNotFoundError(NotFoundError):
    """
    Exception raised when a user cannot be found.

    Common usage: authentication, user management, permissions, profiles
    """

    def __init__(self, user_id: str | int | None = None, **kwargs):
        detail = "User not found"
        if user_id:
            detail = f"User {user_id} not found"

        super().__init__(
            detail=detail,
            i18n_key="errors.user.not_found",
            i18n_params={"user_id": str(user_id)} if user_id else {},
            context={"user_id": user_id} if user_id else None,
            **kwargs,
        )


class UserAlreadyExistsError(ConflictError):
    """
    Exception raised when trying to create a user that already exists.

    Common usage: user registration, account creation
    """

    def __init__(self, identifier: str, identifier_type: str = "email", **kwargs):
        super().__init__(
            detail=f"User with {identifier_type} '{identifier}' already exists",
            i18n_key="errors.user.already_exists",
            i18n_params={"identifier": identifier, "identifier_type": identifier_type},
            context={"identifier": identifier, "identifier_type": identifier_type},
            **kwargs,
        )


class UserAccessDeniedError(ForbiddenError):
    """
    Exception raised when a user doesn't have permission to access a resource.

    More specific than generic ForbiddenError for user-related access control.
    """

    def __init__(
        self, user_id: str | int | None = None, resource: str | None = None, **kwargs
    ):
        detail = "Access denied"
        if resource:
            detail = f"Access denied to {resource}"

        super().__init__(
            detail=detail,
            i18n_key="errors.user.access_denied",
            i18n_params={
                "user_id": str(user_id) if user_id else None,
                "resource": resource,
            },
            context={"user_id": user_id, "resource": resource},
            **kwargs,
        )


__all__ = [
    "UserNotFoundError",
    "UserAlreadyExistsError",
    "UserAccessDeniedError",
]
