"""Helpers for describing and validating MCP server configuration."""

from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any

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

    def get_default_params(self) -> list[MCPServerParams]:
        configs: list[MCPServerParams] = []

        if not self.settings.enable_mcp_system:
            logger.info("MCP system disabled; skipping MCP server configuration")
            return configs

        configs.extend(self._load_configured_params())

        deduped: dict[str, MCPServerParams] = {}
        for item in configs:
            deduped[item.name] = item
        configs = list(deduped.values())

        logger.info("Loaded %s MCP server configuration(s)", len(configs))

        if not configs:
            logger.warning("No MCP server configurations available")

        return configs

    def _load_configured_params(self) -> list[MCPServerParams]:
        payload = self._load_servers_payload()
        if payload is None:
            return []

        mcp_servers = None
        if isinstance(payload, dict):
            mcp_servers = payload.get("mcpServers")

        if not isinstance(mcp_servers, dict):
            logger.error("MCP servers config must contain a 'mcpServers' object")
            return []

        entries: list[Any] = []
        for key, value in mcp_servers.items():
            if not isinstance(value, dict):
                logger.warning(
                    "Skipping invalid MCP server entry %s from mcpServers map",
                    key,
                )
                continue
            entry = {**value}
            entry.setdefault("name", key)
            entries.append(entry)

        configs: list[MCPServerParams] = []
        for raw in entries:
            if not isinstance(raw, dict):
                logger.warning("Skipping invalid MCP server entry: %s", raw)
                continue

            params = self._create_params_from_dict(raw)
            if not params:
                continue

            configs.append(params)

        if configs:
            logger.info("Loaded %s MCP server(s) from JSON configuration", len(configs))

        return configs

    def _load_servers_payload(self) -> Any | None:
        custom_path = self.settings.servers_config_file
        if custom_path and custom_path.exists():
            try:
                with custom_path.open("r", encoding="utf-8") as fp:
                    logger.info("Loading MCP servers from %s", custom_path)
                    return json.load(fp)
            except json.JSONDecodeError as exc:
                logger.error("Invalid MCP servers JSON at %s: %s", custom_path, exc)
                return None

        default_path = Path(__file__).with_name("default_servers.json")
        try:
            with default_path.open("r", encoding="utf-8") as fp:
                logger.info("Using bundled MCP server defaults: %s", default_path)
                return json.load(fp)
        except FileNotFoundError:
            logger.error("Bundled MCP server defaults missing at %s", default_path)
            return None

    def _create_params_from_dict(self, data: dict[str, Any]) -> MCPServerParams | None:
        name = str(data.get("name", "")).strip()
        if not name:
            logger.warning("MCP server entry missing 'name'")
            return None

        command = data.get("command")
        if not isinstance(command, str) or not command.strip():
            logger.warning("MCP server '%s' missing command", name)
            return None

        enabled_flag = data.get("enabled", True)
        enabled = bool(enabled_flag)

        timeout = data.get("timeout_seconds", self.settings.timeout_seconds)
        try:
            timeout_seconds = int(timeout)
        except (TypeError, ValueError):
            logger.warning(
                "Invalid timeout for MCP server '%s'; using default %s",
                name,
                self.settings.timeout_seconds,
            )
            timeout_seconds = self.settings.timeout_seconds

        env_config = data.get("env") or {}
        if not isinstance(env_config, dict):
            logger.warning("Invalid env mapping for MCP server '%s'", name)
            env_config = {}
        env: dict[str, str] = {str(k): str(v) for k, v in env_config.items()}

        args = data.get("args") or None
        if isinstance(args, list):
            args = [str(arg) for arg in args]
        elif args is not None:
            logger.warning("Ignoring non-list args for MCP server '%s'", name)
            args = None

        description = str(data.get("description", "")).strip()

        params = MCPServerParams(
            name=name,
            command=command,
            args=args,
            env=env,
            timeout_seconds=timeout_seconds,
            enabled=enabled,
            description=description,
        )

        return params

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
        }

        if not self.settings.enable_mcp_system:
            return requirements

        try:
            result = subprocess.run(
                ["npx", "--version"],
                capture_output=True,
                text=True,
                timeout=10,
            )
            if result.returncode == 0:
                requirements["nodejs"] = True
                requirements["npx"] = True
                logger.info("npx version: %s", result.stdout.strip())
            else:
                logger.warning("npx version check failed: %s", result.stderr)
        except FileNotFoundError:
            logger.error("npx command not found; ensure Node.js is installed")
        except Exception as exc:  # pragma: no cover - defensive logging
            logger.warning("Unable to verify npx: %s", exc)

        return requirements


default_params_manager = MCPParamsManager()
