"""Helpers for describing and validating MCP server configuration."""

from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any

from src.core.logging import get_logger

from .config import MCPSettings, mcp_settings

logger = get_logger(__name__)


class TransportType(str, Enum):
    """MCP transport types."""

    STDIO = "stdio"
    HTTP = "http"
    SSE = "sse"  # Alias for HTTP with SSE


class AuthType(str, Enum):
    """HTTP authentication types."""

    BEARER = "bearer"
    API_KEY = "api_key"


@dataclass(slots=True)
class HTTPAuthConfig:
    """HTTP authentication configuration."""

    type: AuthType = AuthType.BEARER
    token: str | None = None
    header_name: str = "Authorization"  # For custom header names

    def __post_init__(self) -> None:
        """Validate authentication configuration."""
        if not self.token or not self.token.strip():
            raise ValueError("Auth token cannot be empty")
        if not self.header_name or not self.header_name.strip():
            raise ValueError("Header name cannot be empty")

    def build_header(self) -> dict[str, str]:
        """
        Build authentication header based on type.

        Returns:
            Dictionary with authentication header

        Raises:
            ValueError: If auth type is not supported or token is None
        """
        if not self.token:
            raise ValueError("Cannot build header: token is None")

        if self.type == AuthType.BEARER:
            return {self.header_name: f"Bearer {self.token}"}
        elif self.type == AuthType.API_KEY:
            return {self.header_name: self.token}
        else:
            raise ValueError(f"Unsupported auth type: {self.type}")


@dataclass(slots=True)
class MCPServerParams:
    """Descriptor for an MCP server process or HTTP endpoint."""

    name: str
    transport: TransportType = TransportType.STDIO

    # For stdio transport
    command: str | None = None
    args: list[str] | None = None
    env: dict[str, str] | None = None

    # For HTTP/SSE transport
    url: str | None = None
    auth: HTTPAuthConfig | None = None

    # Common settings
    timeout_seconds: int = 60
    enabled: bool = True
    description: str = ""

    def is_http_transport(self) -> bool:
        """Check if this server uses HTTP/SSE transport."""
        return self.transport in (TransportType.HTTP, TransportType.SSE)

    def is_stdio_transport(self) -> bool:
        """Check if this server uses stdio transport."""
        return self.transport == TransportType.STDIO

    def get_full_command(self) -> str:
        """Get the full command string for stdio transport."""
        if not self.command:
            return ""
        if self.args:
            return f"{self.command} {' '.join(self.args)}"
        return self.command

    def get_command_list(self) -> list[str]:
        """Get the command as a list for stdio transport."""
        if not self.command:
            return []
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

        default_path = (
            Path(__file__).parent.parent.parent
            / "defaults"
            / "default_mcp_servers.json"
        )
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

        # Determine transport type from 'type' field (preferred)
        # or 'transport' field (fallback)
        transport_str = data.get("type") or data.get("transport", "stdio")
        transport_str = str(transport_str).lower()

        try:
            transport = TransportType(transport_str)
        except ValueError:
            logger.warning(
                "Invalid transport type '%s' for MCP server '%s'; using stdio",
                transport_str,
                name,
            )
            transport = TransportType.STDIO

        # Common settings
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

        description = str(data.get("description", "")).strip()

        # Parse based on transport type
        if transport in (TransportType.HTTP, TransportType.SSE):
            return self._create_http_params(
                name, transport, data, timeout_seconds, enabled, description
            )
        else:
            return self._create_stdio_params(
                name, data, timeout_seconds, enabled, description
            )

    def _create_stdio_params(
        self,
        name: str,
        data: dict[str, Any],
        timeout_seconds: int,
        enabled: bool,
        description: str,
    ) -> MCPServerParams | None:
        """Create params for stdio transport."""
        command = data.get("command")
        if not isinstance(command, str) or not command.strip():
            logger.warning("MCP server '%s' missing command for stdio transport", name)
            return None

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

        return MCPServerParams(
            name=name,
            transport=TransportType.STDIO,
            command=command,
            args=args,
            env=env,
            timeout_seconds=timeout_seconds,
            enabled=enabled,
            description=description,
        )

    def _create_http_params(
        self,
        name: str,
        transport: TransportType,
        data: dict[str, Any],
        timeout_seconds: int,
        enabled: bool,
        description: str,
    ) -> MCPServerParams | None:
        """Create params for HTTP/SSE transport."""
        url = data.get("url")
        if not isinstance(url, str) or not url.strip():
            logger.warning("MCP server '%s' missing URL for HTTP transport", name)
            return None

        # Parse authentication config
        auth_config = None
        auth_data = data.get("auth")
        if isinstance(auth_data, dict):
            auth_type_str = str(auth_data.get("type", "bearer")).lower()
            token = auth_data.get("token")
            header_name = auth_data.get("header_name", "Authorization")

            if token:
                # Convert string to AuthType enum
                try:
                    auth_type = AuthType(auth_type_str)
                except ValueError:
                    logger.warning(
                        "Invalid auth type '%s' for MCP server '%s'; using bearer",
                        auth_type_str,
                        name,
                    )
                    auth_type = AuthType.BEARER

                auth_config = HTTPAuthConfig(
                    type=auth_type,
                    token=str(token),
                    header_name=str(header_name),
                )
            else:
                logger.warning(
                    "MCP server '%s' has auth config but missing token",
                    name,
                )

        return MCPServerParams(
            name=name,
            transport=transport,
            url=url.strip(),
            auth=auth_config,
            timeout_seconds=timeout_seconds,
            enabled=enabled,
            description=description,
        )

    def validate_config(self, config: MCPServerParams) -> bool:
        if not config.name:
            logger.error("MCP configuration missing server name")
            return False

        if config.is_stdio_transport():
            if not config.command:
                logger.error(
                    "MCP configuration %s missing command for stdio transport",
                    config.name,
                )
                return False
        elif config.is_http_transport():
            if not config.url:
                logger.error(
                    "MCP configuration %s missing URL for HTTP transport", config.name
                )
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
