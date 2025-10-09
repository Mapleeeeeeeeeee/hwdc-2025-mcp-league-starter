import os
from pathlib import Path
from typing import Any

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    host: str = Field(default="127.0.0.1", alias="HOST")
    port: int = Field(default=8080, alias="PORT")
    environment: str = Field(default="development", alias="ENVIRONMENT")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    llm_models_file: Path = Field(
        default=Path("config/llm_models.json"),
        alias="LLM_MODELS_FILE",
    )
    llm_active_model_file: Path = Field(
        default=Path("config/active_llm_model.json"),
        alias="LLM_ACTIVE_MODEL_FILE",
    )
    cors_allowed_origins: str | list[str] = Field(
        default="",
        alias="CORS_ALLOWED_ORIGINS",
    )
    cors_allowed_methods: str | list[str] = Field(
        default="",
        alias="CORS_ALLOWED_METHODS",
    )
    cors_allowed_headers: str | list[str] = Field(
        default="",
        alias="CORS_ALLOWED_HEADERS",
    )

    @property
    def cors_origins(self) -> list[str]:
        """
        Get CORS origins based on environment.
        Production: Explicit origins only (from env var or hardcoded)
        Development: Flexible origins from env var
        """
        # If explicitly set via env var, use it
        if self.cors_allowed_origins:
            return (
                self.cors_allowed_origins
                if isinstance(self.cors_allowed_origins, list)
                else []
            )

        # Environment-specific defaults
        if self.is_production:
            # Production: No default origins - must be explicitly configured
            # This forces deployment to set CORS_ALLOWED_ORIGINS
            return []
        else:
            # Development: Sensible defaults
            return [
                "http://localhost:3001",  # Next.js dev server
                "http://localhost:8080",  # Docker
                "http://localhost:3000",  # Alternative dev port
            ]

    @property
    def cors_methods(self) -> list[str]:
        """Get CORS methods (environment-independent)"""
        if self.cors_allowed_methods:
            return (
                self.cors_allowed_methods
                if isinstance(self.cors_allowed_methods, list)
                else []
            )
        return ["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"]

    @property
    def cors_headers(self) -> list[str]:
        """Get CORS headers (environment-independent)"""
        if self.cors_allowed_headers:
            return (
                self.cors_allowed_headers
                if isinstance(self.cors_allowed_headers, list)
                else []
            )
        return [
            "Authorization",
            "Content-Type",
            "Accept",
            "Accept-Language",
            "X-Requested-With",
        ]

    @property
    def is_development(self) -> bool:
        return self.environment == "development"

    @property
    def is_production(self) -> bool:
        return self.environment == "production"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    @field_validator("llm_models_file", "llm_active_model_file", mode="before")
    @classmethod
    def _validate_path(cls, value: Any) -> Path:
        path = Path(value)
        # 在測試環境中，允許使用臨時目錄
        if str(path).startswith(("/tmp/", "/var/folders/")):
            return path.resolve()

        # 確保不會跳出專案根目錄，避免路徑注入風險
        root = Path.cwd().resolve()
        resolved = (root / path).resolve() if not path.is_absolute() else path.resolve()
        if root not in resolved.parents and resolved != root:
            raise ValueError("Configured path must reside within the project directory")
        return resolved

    @field_validator(
        "cors_allowed_origins",
        "cors_allowed_methods",
        "cors_allowed_headers",
        mode="before",
    )
    @classmethod
    def _parse_cors_list(cls, value: Any) -> list[str]:
        if value is None or value == "":
            return []
        if isinstance(value, str):
            import json

            trimmed = value.strip()

            # Allow JSON-style arrays for convenience
            if (trimmed.startswith("[") and trimmed.endswith("]")) or (
                trimmed.startswith("(") and trimmed.endswith(")")
            ):
                try:
                    parsed = json.loads(trimmed.replace("(", "[").replace(")", "]"))
                    if isinstance(parsed, (list, tuple)):
                        return [
                            str(origin).strip()
                            for origin in parsed
                            if str(origin).strip()
                        ]
                except json.JSONDecodeError as exc:
                    raise ValueError(
                        "CORS list JSON parsing failed",
                    ) from exc

            return [origin.strip() for origin in trimmed.split(",") if origin.strip()]
        if isinstance(value, (list, tuple, set)):
            return [str(origin).strip() for origin in value if str(origin).strip()]
        raise TypeError(
            "CORS settings must be a comma-separated string or list of strings"
        )

    def get_secret(
        self,
        name: str,
        *,
        default: str | None = None,
        strip: bool = True,
    ) -> str | None:
        """Safely fetch secrets from environment variables."""

        value = os.getenv(name, default)
        if value is None:
            return None
        return value.strip() if strip else value


# Global settings instance
settings = Settings()
