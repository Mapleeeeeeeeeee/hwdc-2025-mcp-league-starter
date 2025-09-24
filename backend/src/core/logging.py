"""Application-wide logging utilities."""

from __future__ import annotations

import logging
from logging.config import dictConfig
from typing import Any

from src.config import settings

# Default log format emphasises level, time, module, and message.
LOG_FORMAT = "%(asctime)s | %(levelname)s | %(name)s:%(lineno)d | %(message)s"

# Audit logs favour machine readable structure while staying human friendly.
AUDIT_LOG_FORMAT = (
    "%(asctime)s | AUDIT | %(name)s | user=%(user)s | action=%(action)s | %(message)s"
)


def _build_default_logging_config(log_level: str) -> dict[str, Any]:
    """Construct the default logging configuration dictionary."""
    return {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "standard": {"format": LOG_FORMAT},
            "audit": {"format": AUDIT_LOG_FORMAT},
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "formatter": "standard",
            },
            "audit_console": {
                "class": "logging.StreamHandler",
                "formatter": "audit",
            },
        },
        "loggers": {
            "": {  # root logger
                "handlers": ["console"],
                "level": log_level,
                "propagate": False,
            },
            "uvicorn": {
                "handlers": ["console"],
                "level": log_level,
                "propagate": False,
            },
            "uvicorn.error": {
                "handlers": ["console"],
                "level": log_level,
                "propagate": False,
            },
            "uvicorn.access": {
                "handlers": ["console"],
                "level": log_level,
                "propagate": False,
            },
            "audit": {
                "handlers": ["audit_console"],
                "level": "INFO",
                "propagate": False,
            },
        },
    }


def setup_logging(
    *,
    log_level: str | None = None,
    config_overrides: dict[str, Any] | None = None,
) -> None:
    """
    Initialise application logging configuration.

    Args:
        log_level: Optional log level override (defaults to settings.log_level).
        config_overrides: Optional dictConfig-compatible overrides.
    """
    level = (log_level or settings.log_level).upper()
    config = _build_default_logging_config(level)

    if config_overrides:
        # Deep merges can be handled separately; this helper performs a shallow update.
        for key, value in config_overrides.items():
            config[key] = value

    dictConfig(config)


def get_logger(name: str | None = None) -> logging.Logger:
    """Return a logger instance, defaulting to the root logger."""
    return logging.getLogger(name)


def get_audit_logger() -> logging.Logger:
    """Convenience accessor for the audit logger."""
    return logging.getLogger("audit")
