"""LLM provider related business exceptions."""

from src.core.exceptions import BadRequestError, ServiceUnavailableError


class LLMProviderNotConfiguredError(ServiceUnavailableError):
    """Raised when the configured LLM provider is missing required credentials."""

    def __init__(self, provider: str, secret_name: str, **kwargs):
        super().__init__(
            detail=f"Provider '{provider}' is not configured correctly",
            i18n_key="errors.llm.provider_missing_secret",
            i18n_params={"provider": provider, "secret": secret_name},
            context={"provider": provider, "secret": secret_name},
            **kwargs,
        )


class LLMProviderUnsupportedError(BadRequestError):
    """Raised when a requested provider does not have an implementation."""

    def __init__(self, provider: str, **kwargs):
        super().__init__(
            detail=f"Unsupported LLM provider '{provider}'",
            i18n_key="errors.llm.provider_unsupported",
            i18n_params={"provider": provider},
            context={"provider": provider},
            **kwargs,
        )


class LLMNoOutputError(ServiceUnavailableError):
    """Raised when the LLM provider returns no content."""

    def __init__(self, **kwargs):
        super().__init__(
            detail="LLM provider returned no content",
            i18n_key="errors.llm.no_output",
            **kwargs,
        )


class LLMStreamError(ServiceUnavailableError):
    """Raised when an error occurs during an LLM stream."""

    def __init__(self, **kwargs):
        super().__init__(
            detail="LLM stream ended unexpectedly",
            i18n_key="errors.llm.stream_incomplete",
            **kwargs,
        )
