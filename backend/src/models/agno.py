"""API models for Agno configuration management."""

from pydantic import BaseModel, ConfigDict, Field


class ToolkitInfo(BaseModel):
    """Toolkit configuration information."""

    model_config = ConfigDict(populate_by_name=True)

    key: str = Field(description="Toolkit unique identifier")
    toolkit_class: str = Field(
        description="Python class path", serialization_alias="toolkitClass"
    )
    enabled: bool = Field(description="Whether the toolkit is enabled")
    config: dict = Field(default_factory=dict, description="Toolkit configuration")


class PromptInfo(BaseModel):
    """Prompt preset information."""

    model_config = ConfigDict(populate_by_name=True)

    key: str = Field(description="Prompt unique identifier")
    name: str = Field(description="Human-readable name")
    enabled: bool = Field(description="Whether the prompt is enabled")
    instruction_count: int = Field(
        description="Number of instructions", serialization_alias="instructionCount"
    )


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
