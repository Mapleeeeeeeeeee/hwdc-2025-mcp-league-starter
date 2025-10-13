"""Data contracts for Agno tools configuration."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class ToolkitConfig(BaseModel):
    """Configuration for a single Agno toolkit."""

    key: str = Field(
        description="Unique identifier for this toolkit configuration",
    )
    toolkit_class: str = Field(
        description=(
            "Full Python path to the toolkit class, "
            "e.g. 'agno.tools.duckduckgo.DuckDuckGoTools'"
        ),
    )
    enabled: bool = Field(
        default=True,
        description="Whether this toolkit should be loaded",
    )
    config: dict[str, Any] = Field(
        default_factory=dict,
        description="Configuration parameters to pass to the toolkit constructor",
    )


class CustomToolConfig(BaseModel):
    """Configuration for custom tools defined in the application."""

    key: str = Field(description="Unique identifier for this custom tool")
    module_path: str = Field(
        description="Python module path where the tool is defined",
    )
    function_name: str = Field(description="Name of the tool function")
    enabled: bool = Field(default=True)


class AgnoToolsConfig(BaseModel):
    """Complete tools configuration file structure."""

    toolkits: list[ToolkitConfig] = Field(default_factory=list)
    custom_tools: list[CustomToolConfig] = Field(default_factory=list)
