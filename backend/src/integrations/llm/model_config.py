"""Data contracts for LLM model configuration."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field, field_validator


class LLMModelConfig(BaseModel):
    """Configuration describing how to instantiate a model provider."""

    key: str = Field(
        description="Unique identifier used by clients to select the model",
    )
    provider: str = Field(
        description="Provider slug, e.g. 'openai', 'together'",
    )
    model_id: str = Field(
        description="Provider-specific model identifier",
    )
    api_key_env: str = Field(
        description="Environment variable name that stores the provider API key",
    )
    base_url: str | None = Field(
        default=None,
        description="Optional override for provider base URL",
    )
    default_params: dict[str, Any] = Field(
        default_factory=dict,
        description="Additional keyword arguments passed to the provider constructor",
    )
    supports_streaming: bool = Field(default=True)
    metadata: dict[str, Any] = Field(default_factory=dict)

    model_config = {
        "str_min_length": 1,
    }

    @field_validator("api_key_env")
    @classmethod
    def _ensure_no_secrets(cls, value: str) -> str:
        # 防止直接把 API key 寫進設定檔
        if value.strip() == "" or "=" in value:
            msg = (
                "api_key_env must reference an environment variable name, "
                "not a literal key"
            )
            raise ValueError(msg)
        return value


class LLMModelRegistryFile(BaseModel):
    """Wrapper used when loading from JSON files."""

    models: list[LLMModelConfig] = Field(default_factory=list)
