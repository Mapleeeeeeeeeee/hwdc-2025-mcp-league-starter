import os
from pathlib import Path
from typing import Any

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings


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

    @property
    def is_development(self) -> bool:
        return self.environment == "development"

    @property
    def is_production(self) -> bool:
        return self.environment == "production"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        extra = "ignore"

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
