"""Configuration helpers for the MCP integration."""

from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path
from typing import Any

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class MCPSettings(BaseSettings):
    """Runtime configuration for MCP server orchestration."""

    enable_mcp_system: bool = Field(default=False, alias="ENABLE_MCP_SYSTEM")
    npx_command: str = Field(default="npx", alias="MCP_NPX_COMMAND")
    base_path: Path = Field(default=Path("."), alias="MCP_BASE_PATH")
    node_env: str = Field(default="development", alias="MCP_NODE_ENV")
    timeout_seconds: int = Field(default=60, alias="MCP_TIMEOUT_SECONDS")
    enabled_servers: list[str] | str = Field(
        default_factory=lambda: ["filesystem"],
        alias="MCP_ENABLED_SERVERS",
    )
    brave_api_key: str | None = Field(default=None, alias="BRAVE_API_KEY")
    postgres_database_url: str | None = Field(
        default=None, alias="POSTGRES_DATABASE_URL"
    )

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    @field_validator("base_path", mode="before")
    @classmethod
    def _normalise_base_path(cls, value: str | Path) -> Path:
        """Ensure base paths are resolved inside the project directory."""
        path = Path(value).expanduser()
        if not path.is_absolute():
            path = (Path.cwd() / path).resolve()
        else:
            path = path.resolve()
        return path

    @field_validator("enabled_servers", mode="before")
    @classmethod
    def _parse_enabled_servers(cls, value: Any) -> list[str]:
        if value is None:
            return []
        if isinstance(value, str):
            items = [item.strip() for item in value.split(",") if item.strip()]
            return [item.lower() for item in items]
        if isinstance(value, Iterable):
            items = [str(item).strip() for item in value if str(item).strip()]
            return [item.lower() for item in items]
        raise TypeError("enabled_servers must be a string or iterable of strings")

    def is_server_enabled(self, name: str) -> bool:
        """Return True when the given server identifier is enabled."""
        return self.enable_mcp_system and name.lower() in self.enabled_servers


mcp_settings = MCPSettings()
