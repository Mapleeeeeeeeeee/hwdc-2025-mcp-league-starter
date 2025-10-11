"""Configuration helpers for the MCP integration."""

from __future__ import annotations

from pathlib import Path

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class MCPSettings(BaseSettings):
    """Runtime configuration for MCP server orchestration."""

    enable_mcp_system: bool = Field(default=False, alias="ENABLE_MCP_SYSTEM")
    timeout_seconds: int = Field(default=60, alias="MCP_TIMEOUT_SECONDS")
    servers_config_file: Path | None = Field(
        default=Path("config/mcp_servers.json"),
        alias="MCP_SERVERS_FILE",
    )

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    @field_validator("servers_config_file", mode="before")
    @classmethod
    def _normalise_config_path(cls, value: str | Path | None) -> Path | None:
        if value is None:
            return None
        path = Path(value).expanduser()
        if not path.is_absolute():
            path = (Path.cwd() / path).resolve()
        else:
            path = path.resolve()
        return path

    def is_mcp_enabled_globally(self) -> bool:
        """Return True when the MCP system is enabled."""
        return self.enable_mcp_system


mcp_settings = MCPSettings()
