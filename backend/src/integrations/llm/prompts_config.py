"""Data contracts for Agno prompts configuration."""

from __future__ import annotations

from pydantic import BaseModel, Field


class PromptConfig(BaseModel):
    """Configuration for a single prompt preset."""

    key: str = Field(
        description="Unique identifier for this prompt configuration",
    )
    name: str = Field(
        description="Human-readable name for this prompt preset",
    )
    enabled: bool = Field(
        default=True,
        description="Whether this prompt should be available for use",
    )
    instructions: list[str] = Field(
        default_factory=list,
        description="List of instruction strings to pass to the Agent",
    )


class AgnoPromptsConfig(BaseModel):
    """Complete prompts configuration file structure."""

    prompts: list[PromptConfig] = Field(default_factory=list)
    system_message: str | None = Field(
        default=None,
        description="Optional system message to prepend to all agents",
    )
