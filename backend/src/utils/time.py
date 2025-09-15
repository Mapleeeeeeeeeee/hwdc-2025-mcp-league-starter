"""Utilities for handling timezone-aware datetime objects."""

from datetime import datetime, timezone
from typing import Any


def utc_now() -> datetime:
    """Get the current UTC datetime with timezone information."""
    return datetime.now(timezone.utc)


def to_utc(dt: datetime) -> datetime:
    """Convert a datetime object to UTC."""
    if dt.tzinfo is None:
        # For naive datetimes, we assume they are in UTC
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def from_iso_string(iso_string: str) -> datetime:
    """Parse an ISO-8601 formatted string to a timezone-aware datetime."""
    return datetime.fromisoformat(iso_string)


def to_iso_string(dt: datetime) -> str:
    """Convert a datetime object to ISO-8601 format string."""
    if dt.tzinfo is None:
        raise ValueError("Cannot serialize naive datetime. Use timezone-aware datetime.")
    return dt.isoformat()


def ensure_utc(value: Any) -> datetime:
    """Ensure a value is a timezone-aware UTC datetime."""
    if isinstance(value, datetime):
        return to_utc(value)
    elif isinstance(value, str):
        return to_utc(from_iso_string(value))
    else:
        raise TypeError(f"Cannot convert {type(value)} to datetime")