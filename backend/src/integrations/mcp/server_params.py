"""Helpers for describing and validating MCP server configuration."""

from __future__ import annotations

import platform
import subprocess
from dataclasses import dataclass
from pathlib import Path

from src.core.logging import get_logger

from .config import MCPSettings, mcp_settings

logger = get_logger(__name__)


@dataclass(slots=True)
class MCPServerParams:
    """Descriptor for an MCP server process."""

    name: str
    command: str
    args: list[str] | None = None
    env: dict[str, str] | None = None
    timeout_seconds: int = 60
    enabled: bool = True
    description: str = ""

    def get_full_command(self) -> str:
        if self.args:
            return f"{self.command} {' '.join(self.args)}"
        return self.command

    def get_command_list(self) -> list[str]:
        if self.args:
            return [self.command, *self.args]
        return self.command.split()


class MCPParamsManager:
    """Produce server parameter definitions based on runtime configuration."""

    def __init__(self, settings: MCPSettings | None = None) -> None:
        self.settings = settings or mcp_settings

    def get_platform_command(self, base_cmd: str) -> str:
        return base_cmd.replace("npx", self.settings.npx_command, 1)

    def get_default_params(self) -> list[MCPServerParams]:
        configs: list[MCPServerParams] = []

        if not self.settings.enable_mcp_system:
            logger.info("MCP system disabled; skipping MCP server configuration")
            return configs

        if self.settings.is_server_enabled("filesystem"):
            configs.append(
                MCPServerParams(
                    name="filesystem",
                    command=(
                        "npx -y @modelcontextprotocol/server-filesystem "
                        f"{self._format_base_path(self.settings.base_path)}"
                    ),
                    env={"NODE_ENV": self.settings.node_env},
                    timeout_seconds=self.settings.timeout_seconds,
                    description="Filesystem browsing tools",
                )
            )

        if self.settings.is_server_enabled("context7"):
            configs.append(
                MCPServerParams(
                    name="context7",
                    command="npx -y @upstash/context7-mcp@latest",
                    timeout_seconds=self.settings.timeout_seconds,
                    description="Context7 documentation tools",
                )
            )

        if self.settings.is_server_enabled("brave-search"):
            api_key = self.settings.brave_api_key
            if not api_key:
                logger.warning(
                    "Brave Search MCP enabled but BRAVE_API_KEY not configured"
                )

            configs.append(
                MCPServerParams(
                    name="brave-search",
                    command="npx -y @modelcontextprotocol/server-brave-search",
                    env={"BRAVE_API_KEY": api_key or ""},
                    timeout_seconds=self.settings.timeout_seconds,
                    description="Brave search integration",
                )
            )

        if self.settings.is_server_enabled("postgres"):
            database_url = self.settings.postgres_database_url
            if not database_url:
                logger.warning(
                    "PostgreSQL MCP enabled but POSTGRES_DATABASE_URL not configured",
                )

            configs.append(
                MCPServerParams(
                    name="postgres",
                    command=(
                        "npx -y @modelcontextprotocol/server-postgres "
                        f"{database_url or ''}"
                    ),
                    timeout_seconds=self.settings.timeout_seconds,
                    description="PostgreSQL database tools",
                )
            )

        for config in configs:
            if config.args:
                config.command = self.settings.npx_command
            else:
                config.command = self.get_platform_command(config.command)

        logger.info("Loaded %s MCP server configuration(s)", len(configs))
        logger.debug(
            "Platform: %s | base path: %s",
            platform.system(),
            self.settings.base_path,
        )

        return configs

    def validate_config(self, config: MCPServerParams) -> bool:
        if not config.name:
            logger.error("MCP configuration missing server name")
            return False

        if not config.command:
            logger.error("MCP configuration %s missing command", config.name)
            return False

        if config.timeout_seconds <= 0:
            logger.warning(
                "MCP configuration %s has invalid timeout; applying default %s seconds",
                config.name,
                self.settings.timeout_seconds,
            )
            config.timeout_seconds = self.settings.timeout_seconds

        return True

    def check_environment_requirements(self) -> dict[str, bool]:
        requirements = {
            "mcp_system_enabled": self.settings.enable_mcp_system,
            "nodejs": False,
            "npx": False,
            "brave_api_key": bool(self.settings.brave_api_key),
            "postgres_database_url": bool(self.settings.postgres_database_url),
        }

        if not self.settings.enable_mcp_system:
            return requirements

        try:
            result = subprocess.run(
                [self.settings.npx_command, "--version"],
                capture_output=True,
                text=True,
                timeout=10,
            )
            if result.returncode == 0:
                requirements["nodejs"] = True
                requirements["npx"] = True
                logger.info(
                    "%s version: %s",
                    self.settings.npx_command,
                    result.stdout.strip(),
                )
            else:
                logger.warning(
                    "%s version check failed: %s",
                    self.settings.npx_command,
                    result.stderr,
                )
        except FileNotFoundError:
            logger.error(
                "%s command not found; ensure Node.js is installed",
                self.settings.npx_command,
            )
        except Exception as exc:  # pragma: no cover - defensive logging
            logger.warning("Unable to verify %s: %s", self.settings.npx_command, exc)

        return requirements

    @staticmethod
    def _format_base_path(path: Path) -> str:
        return str(path)


default_params_manager = MCPParamsManager()
