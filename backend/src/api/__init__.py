"""
API layer for HWDC 2025 MCP League Starter backend.

Provides FastAPI routing, exception handling, and API versioning.
"""

from .exception_handlers import register_exception_handlers

__all__ = [
    "register_exception_handlers",
]
