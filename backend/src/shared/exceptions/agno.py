"""Agno tools related exceptions."""

from src.core.exceptions import BadRequestError, ServiceUnavailableError


class ToolkitLoadError(ServiceUnavailableError):
    """Raised when a toolkit cannot be loaded or instantiated."""

    def __init__(self, toolkit_key: str, reason: str, **kwargs):
        super().__init__(
            detail=f"Failed to load toolkit '{toolkit_key}': {reason}",
            i18n_key="errors.agno.toolkit_load_failed",
            i18n_params={"toolkit_key": toolkit_key, "reason": reason},
            context={"toolkit_key": toolkit_key, "reason": reason},
            **kwargs,
        )


class ToolkitNotFoundError(BadRequestError):
    """Raised when a requested toolkit configuration is not found."""

    def __init__(self, toolkit_key: str, **kwargs):
        super().__init__(
            detail=f"Toolkit configuration '{toolkit_key}' not found",
            i18n_key="errors.agno.toolkit_not_found",
            i18n_params={"toolkit_key": toolkit_key},
            context={"toolkit_key": toolkit_key},
            **kwargs,
        )


class PromptNotFoundError(BadRequestError):
    """Raised when a requested prompt configuration is not found."""

    def __init__(self, prompt_key: str, **kwargs):
        super().__init__(
            detail=f"Prompt configuration '{prompt_key}' not found",
            i18n_key="errors.agno.prompt_not_found",
            i18n_params={"prompt_key": prompt_key},
            context={"prompt_key": prompt_key},
            **kwargs,
        )
