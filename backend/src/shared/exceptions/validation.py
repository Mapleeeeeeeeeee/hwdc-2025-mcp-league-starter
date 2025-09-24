"""
Validation business exceptions for HWDC 2025 MCP League Starter.

Contains exceptions specific to input validation and business rule validation.
"""

from src.core.exceptions import BadRequestError, UnprocessableEntityError


class InvalidInputError(BadRequestError):
    """
    Exception raised when input validation fails at business logic level.

    More specific than generic BadRequestError with field-level context.
    """

    def __init__(self, field: str, value: str, reason: str, **kwargs):
        super().__init__(
            detail=f"Invalid {field}: {reason}",
            i18n_key="errors.input.invalid",
            i18n_params={"field": field, "value": value, "reason": reason},
            context={"field": field, "value": value, "reason": reason},
            **kwargs,
        )


class ValidationError(UnprocessableEntityError):
    """
    Exception raised when business validation fails.

    Use this for complex business rule validations that don't fit
    field-level validation.
    """

    def __init__(
        self, message: str, validation_errors: list[dict] | None = None, **kwargs
    ):
        super().__init__(
            detail=message,
            i18n_key="errors.validation.failed",
            i18n_params={"message": message},
            context={"message": message, "validation_errors": validation_errors},
            **kwargs,
        )
