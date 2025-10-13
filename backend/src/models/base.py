"""Shared base model for API DTOs."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict


def _to_camel(value: str) -> str:
    parts = value.split("_")
    return parts[0] + "".join(part.title() for part in parts[1:])


class APIBaseModel(BaseModel):
    """Base model enforcing camelCase JSON while keeping snake_case internally."""

    model_config = ConfigDict(
        populate_by_name=True,
        alias_generator=_to_camel,
        arbitrary_types_allowed=True,
    )
