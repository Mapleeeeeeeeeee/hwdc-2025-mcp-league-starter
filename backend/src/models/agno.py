"""API models for Agno configuration management."""

from pydantic import BaseModel, Field


class ToolkitInfo(BaseModel):
    """Toolkit configuration information."""

    key: str = Field(description="Toolkit unique identifier")
    toolkit_class: str = Field(description="Python class path")
    enabled: bool = Field(description="Whether the toolkit is enabled")
    config: dict = Field(default_factory=dict, description="Toolkit configuration")


class PromptInfo(BaseModel):
    """Prompt preset information."""

    key: str = Field(description="Prompt unique identifier")
    name: str = Field(description="Human-readable name")
    enabled: bool = Field(description="Whether the prompt is enabled")
    instruction_count: int = Field(description="Number of instructions")


class AgnoConfigResponse(BaseModel):
    """Response containing available Agno configurations."""

    toolkits: list[ToolkitInfo] = Field(description="Available toolkits")
    prompts: list[PromptInfo] = Field(description="Available prompts")


class UpdateToolkitRequest(BaseModel):
    """Request to update toolkit enabled state."""

    enabled: bool = Field(description="Enable or disable the toolkit")


class UpdatePromptRequest(BaseModel):
    """Request to update prompt enabled state."""

    enabled: bool = Field(description="Enable or disable the prompt")
