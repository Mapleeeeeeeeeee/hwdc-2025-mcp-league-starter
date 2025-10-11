"""Lifecycle management for Model Context Protocol (MCP) servers."""

from __future__ import annotations

import asyncio
import os
import platform
import sys
import traceback
from typing import Any

from agno.tools.mcp import MCPTools

from src.core.logging import get_logger
from src.models import ReloadAllMCPServersResponse, ReloadMCPServerResponse
from src.shared.exceptions import (
    MCPNoServersAvailableError,
    MCPServerDisabledError,
    MCPServerNotFoundError,
    MCPServerReloadError,
)

from .server_params import MCPParamsManager, MCPServerParams
from .toolkit import MCPToolkit

logger = get_logger(__name__)


class MCPManager:
    """Coordinate MCP server startup, tracking, and shutdown."""

    _instance: MCPManager | None = None
    _class_initialised = False

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, params_manager: MCPParamsManager | None = None) -> None:
        if MCPManager._class_initialised:
            return

        self._params_manager = params_manager or MCPParamsManager()
        self._servers: dict[str, MCPTools] = {}
        self._configs: list[MCPServerParams] = []
        self._lock = asyncio.Lock()
        self._initialized = False
        MCPManager._class_initialised = True

    async def initialize_system(self) -> bool:
        """Initialise all configured MCP servers."""
        settings = self._params_manager.settings
        logger.info("Starting MCP system initialisation")

        if not settings.enable_mcp_system:
            logger.info("MCP system disabled via configuration; skipping startup")
            return False

        self._log_environment_info()

        requirements = self._params_manager.check_environment_requirements()
        self._log_environment_requirements(requirements)

        configs = [
            cfg
            for cfg in self._params_manager.get_default_params()
            if self._params_manager.validate_config(cfg)
        ]

        if not configs:
            logger.warning("No valid MCP server configuration found")
            return False

        await self.initialize_from_configs(configs)
        self._log_initialization_result()

        logger.info("MCP system initialisation complete")
        return self.is_initialized()

    async def initialize_from_configs(self, configs: list[MCPServerParams]) -> None:
        """Initialise all enabled servers from the provided configurations."""
        async with self._lock:
            if self._initialized and self._servers:
                logger.debug("MCP manager already initialised; skipping re-run")
                return

            self._configs = configs
            enabled_configs = [config for config in configs if config.enabled]

            if not enabled_configs:
                logger.warning("No MCP servers marked as enabled")
                return

            logger.info("Initialising %s MCP server(s)", len(enabled_configs))

            tasks = [
                asyncio.create_task(self._initialise_single_server(config))
                for config in enabled_configs
            ]
            results = await asyncio.gather(*tasks, return_exceptions=True)

            success_count = 0
            total_functions = 0

            for config, result in zip(enabled_configs, results, strict=False):
                if isinstance(result, Exception):
                    self._handle_initialization_error(config, result)
                    continue

                success_count += 1
                total_functions += self._get_server_function_count(config.name)

            logger.info(
                "MCP manager initialisation summary: %s/%s servers ready "
                "(%s functions)",
                success_count,
                len(enabled_configs),
                total_functions,
            )

            if success_count > 0:
                self._initialized = True

    async def _initialise_single_server(self, config: MCPServerParams) -> None:
        logger.info("Initialising MCP server '%s'", config.name)
        full_command = config.get_full_command()
        logger.debug("Command: %s", full_command)
        logger.debug("Environment: %s", config.env)
        logger.debug("Timeout: %s", config.timeout_seconds)

        mcp_kwargs: dict[str, Any] = {"command": full_command}

        if config.env:
            mcp_kwargs["env"] = config.env

        if config.timeout_seconds:
            mcp_kwargs["timeout_seconds"] = config.timeout_seconds

        mcp_tools = MCPTools(**mcp_kwargs)
        await mcp_tools.__aenter__()

        function_count = (
            len(mcp_tools.functions) if hasattr(mcp_tools, "functions") else 0
        )
        logger.debug(
            "Loaded %s function(s) for MCP server '%s'",
            function_count,
            config.name,
        )

        self._servers[config.name] = mcp_tools
        logger.info("MCP server '%s' initialised successfully", config.name)

    def _handle_initialization_error(
        self, config: MCPServerParams, error: Exception
    ) -> None:
        logger.error(
            "Failed to initialise MCP server '%s': %s",
            config.name,
            error,
        )
        logger.debug(
            "Traceback for MCP server '%s':\n%s",
            config.name,
            "".join(
                traceback.format_exception(
                    type(error),
                    error,
                    error.__traceback__,
                )
            ),
        )

    def _log_environment_info(self) -> None:
        logger.info("Python version: %s", sys.version.replace("\n", " "))
        logger.info("Platform: %s %s", platform.system(), platform.release())
        logger.debug("Working directory: %s", os.getcwd())
        logger.debug("PATH (first 200 chars): %s", os.environ.get("PATH", "")[:200])

    def _log_environment_requirements(self, requirements: dict[str, bool]) -> None:
        logger.info("Environment requirement checks")
        for name, satisfied in requirements.items():
            logger.info(" - %s: %s", name, "OK" if satisfied else "MISSING")

        if not all(requirements.values()):
            logger.warning("One or more MCP environment requirements are not satisfied")

    def _log_initialization_result(self) -> None:
        if not self.is_initialized():
            logger.warning("MCP manager initialisation failed or no servers connected")
            return

        status = self.get_server_status()
        total_functions = sum(info["function_count"] for info in status.values())

        logger.info("MCP servers ready: %s", len(status))
        logger.info("Total MCP functions available: %s", total_functions)

        for server_name, info in status.items():
            logger.info(
                "Server '%s' (%s) -> %s functions",
                server_name,
                info.get("description") or "no description",
                info["function_count"],
            )

    def get_toolkit_for_server(
        self, server_name: str, *, allowed_functions: list[str] | None = None
    ) -> MCPToolkit | None:
        if not self._initialized:
            logger.debug("MCP manager not initialised; cannot provide toolkit")
            return None

        tools = self._servers.get(server_name)
        if tools is None:
            logger.debug("MCP server '%s' not found", server_name)
            return None

        return MCPToolkit(server_name, tools, allowed_functions=allowed_functions)

    def get_functions_for_server(self, server_name: str) -> dict[str, Any]:
        tools = self._servers.get(server_name)
        if tools is None or not hasattr(tools, "functions"):
            return {}
        return tools.functions

    def _get_server_function_count(self, server_name: str) -> int:
        return len(self.get_functions_for_server(server_name))

    def get_server_status(self) -> dict[str, dict[str, Any]]:
        status: dict[str, dict[str, Any]] = {}
        names = {config.name for config in self._configs} | set(self._servers.keys())
        for server_name in sorted(names):
            functions = self.get_functions_for_server(server_name)
            status[server_name] = {
                "connected": server_name in self._servers,
                "function_count": len(functions),
                "functions": list(functions.keys()),
                "description": self._get_server_description(server_name),
                "enabled": self._is_server_enabled(server_name),
            }
        return status

    def _get_server_description(self, server_name: str) -> str:
        for config in self._configs:
            if config.name == server_name:
                return config.description
        return ""

    def _is_server_enabled(self, server_name: str) -> bool:
        for config in self._configs:
            if config.name == server_name:
                return config.enabled
        return False

    def get_available_servers(self) -> list[str]:
        return list(self._servers.keys())

    def is_initialized(self) -> bool:
        return self._initialized and bool(self._servers)

    def get_system_status(self) -> dict[str, Any]:
        if not self.is_initialized():
            return {
                "initialized": False,
                "servers": {},
                "total_servers": 0,
                "total_functions": 0,
                "message": "MCP system not initialised",
            }

        server_status = self.get_server_status()
        total_functions = sum(info["function_count"] for info in server_status.values())

        return {
            "initialized": True,
            "servers": server_status,
            "total_servers": len(server_status),
            "total_functions": total_functions,
            "available_servers": self.get_available_servers(),
        }

    async def reload_server(self, server_name: str) -> ReloadMCPServerResponse:
        """Reload a specific MCP server by name."""
        logger.info("Reloading MCP server '%s'", server_name)

        async with self._lock:
            # Reload configurations from file to pick up any changes
            fresh_configs = [
                cfg
                for cfg in self._params_manager.get_default_params()
                if self._params_manager.validate_config(cfg)
            ]
            self._configs = fresh_configs

            # Find the server config
            config = None
            for cfg in self._configs:
                if cfg.name == server_name:
                    config = cfg
                    break

            if config is None:
                logger.warning("Server '%s' not found in configuration", server_name)
                raise MCPServerNotFoundError(server_name)

            if not config.enabled:
                logger.warning("Server '%s' is disabled in configuration", server_name)
                raise MCPServerDisabledError(server_name)

            # Close existing connection if any
            if server_name in self._servers:
                await self._close_server(server_name)

            # Reinitialize the server
            try:
                await self._initialise_single_server(config)
                function_count = self._get_server_function_count(server_name)
                logger.info(
                    "Server '%s' reloaded successfully with %s functions",
                    server_name,
                    function_count,
                )
                return ReloadMCPServerResponse(
                    server_name=server_name,
                    success=True,
                    message="Server reloaded successfully",
                    function_count=function_count,
                )
            except Exception as exc:
                logger.error("Failed to reload server '%s': %s", server_name, exc)
                raise MCPServerReloadError(server_name, reason=str(exc)) from exc

    async def reload_all_servers(self) -> ReloadAllMCPServersResponse:
        """Reload all enabled MCP servers."""
        logger.info("Reloading all MCP servers")

        async with self._lock:
            # Reload configurations from file to pick up any changes
            fresh_configs = [
                cfg
                for cfg in self._params_manager.get_default_params()
                if self._params_manager.validate_config(cfg)
            ]
            self._configs = fresh_configs

            enabled_configs = [config for config in self._configs if config.enabled]

            if not enabled_configs:
                logger.warning("No enabled servers to reload")
                raise MCPNoServersAvailableError()

            # Close all existing connections
            for server_name in list(self._servers.keys()):
                await self._close_server(server_name)

            # Reinitialize all enabled servers
            results: list[ReloadMCPServerResponse] = []
            success_count = 0
            failed_count = 0

            for config in enabled_configs:
                try:
                    await self._initialise_single_server(config)
                    function_count = self._get_server_function_count(config.name)
                    results.append(
                        ReloadMCPServerResponse(
                            server_name=config.name,
                            success=True,
                            message="Server reloaded successfully",
                            function_count=function_count,
                        )
                    )
                    success_count += 1
                except Exception as exc:
                    logger.error("Failed to reload server '%s': %s", config.name, exc)
                    results.append(
                        ReloadMCPServerResponse(
                            server_name=config.name,
                            success=False,
                            message=f"Failed to reload: {exc!s}",
                            function_count=0,
                        )
                    )
                    failed_count += 1

            logger.info(
                "Reload complete: %s/%s servers successful",
                success_count,
                len(enabled_configs),
            )

            return ReloadAllMCPServersResponse(
                success=success_count > 0,
                reloaded_count=success_count,
                failed_count=failed_count,
                results=results,
            )

    async def _close_server(self, server_name: str) -> None:
        """Close a specific MCP server connection."""
        tools = self._servers.get(server_name)
        if tools is None:
            return

        try:
            logger.info("Closing MCP server '%s'", server_name)
            if hasattr(tools, "__aexit__"):
                await tools.__aexit__(None, None, None)
            elif hasattr(tools, "close") and callable(tools.close):
                result = tools.close()
                if asyncio.iscoroutine(result):
                    await result
            else:  # pragma: no cover - safety fallback
                logger.debug(
                    "MCP server '%s' exposes no async close handler",
                    server_name,
                )
        except Exception as exc:  # pragma: no cover - defensive logging
            logger.warning(
                "Error while closing MCP server '%s': %s",
                server_name,
                exc,
            )
        finally:
            self._servers.pop(server_name, None)

    async def shutdown(self) -> None:
        """Close all active MCP tool connections and reset state."""
        logger.info("Commencing MCP manager shutdown")

        if not self._initialized or not self._servers:
            logger.debug("MCP manager not initialised; nothing to shut down")
            return

        async with self._lock:
            shutdown_errors: list[str] = []

            for server_name in list(self._servers.keys()):
                try:
                    await self._close_server(server_name)
                except Exception as exc:  # pragma: no cover - defensive logging
                    message = f"Error while cleaning MCP server '{server_name}': {exc}"
                    logger.warning(message)
                    shutdown_errors.append(message)

            self._servers.clear()
            self._configs = []
            self._initialized = False

            if shutdown_errors:
                logger.debug("MCP shutdown issues: %s", shutdown_errors)

        logger.info("MCP manager shutdown complete")


async def initialize_mcp_system() -> bool:
    return await MCPManager().initialize_system()


def get_mcp_status() -> dict[str, Any]:
    return MCPManager().get_system_status()


async def graceful_mcp_cleanup() -> None:
    await MCPManager().shutdown()


def is_mcp_initialized() -> bool:
    return MCPManager().is_initialized()


def get_available_mcp_servers() -> list[str]:
    return MCPManager().get_available_servers()


def get_mcp_server_functions(server_name: str) -> list[str]:
    manager = MCPManager()
    if not manager.is_initialized():
        return []
    return list(manager.get_functions_for_server(server_name).keys())


def get_mcp_toolkit(
    server_name: str, *, allowed_functions: list[str] | None = None
) -> MCPToolkit | None:
    """Get the toolkit for a specific MCP server."""
    return MCPManager().get_toolkit_for_server(
        server_name, allowed_functions=allowed_functions
    )


async def reload_mcp_server(server_name: str) -> ReloadMCPServerResponse:
    """Reload a specific MCP server."""
    return await MCPManager().reload_server(server_name)


async def reload_all_mcp_servers() -> ReloadAllMCPServersResponse:
    """Reload all enabled MCP servers."""
    return await MCPManager().reload_all_servers()
