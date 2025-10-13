"""API router for Agno configuration management."""

from __future__ import annotations

from functools import lru_cache
from typing import Annotated

from fastapi import APIRouter, Depends
from src.core import get_logger
from src.integrations.llm import PromptsConfigStore, ToolsConfigStore
from src.models.agno import (
    AgnoConfigResponse,
    PromptInfo,
    ToolkitInfo,
    UpdatePromptRequest,
    UpdateToolkitRequest,
)
from src.shared.response import APIResponse, create_success_response

router = APIRouter(prefix="/agno", tags=["agno"])
logger = get_logger(__name__)


@lru_cache(maxsize=1)
def get_tools_store() -> ToolsConfigStore:
    """Get or create the tools configuration store singleton."""
    return ToolsConfigStore()


@lru_cache(maxsize=1)
def get_prompts_store() -> PromptsConfigStore:
    """Get or create the prompts configuration store singleton."""
    return PromptsConfigStore()


ToolsStoreDep = Annotated[ToolsConfigStore, Depends(get_tools_store)]
PromptsStoreDep = Annotated[PromptsConfigStore, Depends(get_prompts_store)]


@router.get("/config", response_model=APIResponse[AgnoConfigResponse])
async def get_agno_config(
    tools_store: ToolsStoreDep,
    prompts_store: PromptsStoreDep,
) -> APIResponse[AgnoConfigResponse]:
    """Get available Agno toolkits and prompts configuration.

    Returns current configuration of all toolkits and prompts,
    including their enabled/disabled state.
    """
    logger.debug("Fetching Agno configuration")

    # Get all toolkits
    all_toolkits = tools_store._load_config().toolkits
    toolkits = [
        ToolkitInfo(
            key=tk.key,
            toolkit_class=tk.toolkit_class,
            enabled=tk.enabled,
            config=tk.config,
        )
        for tk in all_toolkits
    ]

    # Get all prompts
    all_prompts = prompts_store._load_config().prompts
    prompts = [
        PromptInfo(
            key=p.key,
            name=p.name,
            enabled=p.enabled,
            instruction_count=len(p.instructions),
        )
        for p in all_prompts
    ]

    logger.info(
        "Agno configuration retrieved",
        extra={
            "toolkit_count": len(toolkits),
            "prompt_count": len(prompts),
        },
    )

    return create_success_response(
        data=AgnoConfigResponse(toolkits=toolkits, prompts=prompts),
        message="Agno configuration retrieved successfully",
    )


@router.patch("/toolkits/{toolkit_key}", response_model=APIResponse[None])
async def update_toolkit(
    toolkit_key: str,
    request: UpdateToolkitRequest,
    tools_store: ToolsStoreDep,
) -> APIResponse[None]:
    """Enable or disable a specific toolkit.

    Args:
        toolkit_key: The toolkit identifier
        request: Update request with enabled state
        tools_store: Injected tools configuration store

    Raises:
        ToolkitNotFoundError: If the toolkit key is not found
    """
    logger.info(
        "Updating toolkit enabled state",
        extra={
            "toolkit_key": toolkit_key,
            "enabled": request.enabled,
        },
    )

    # This will raise ToolkitNotFoundError if not found
    # The exception will be handled by the global exception handler
    tools_store.update_toolkit_enabled(toolkit_key, request.enabled)

    action = "enabled" if request.enabled else "disabled"
    logger.info(
        f"Toolkit {action} successfully",
        extra={"toolkit_key": toolkit_key},
    )

    return create_success_response(
        message=f"Toolkit '{toolkit_key}' {action} successfully"
    )


@router.patch("/prompts/{prompt_key}", response_model=APIResponse[None])
async def update_prompt(
    prompt_key: str,
    request: UpdatePromptRequest,
    prompts_store: PromptsStoreDep,
) -> APIResponse[None]:
    """Enable or disable a specific prompt preset.

    Args:
        prompt_key: The prompt identifier
        request: Update request with enabled state
        prompts_store: Injected prompts configuration store

    Raises:
        PromptNotFoundError: If the prompt key is not found
    """
    logger.info(
        "Updating prompt enabled state",
        extra={
            "prompt_key": prompt_key,
            "enabled": request.enabled,
        },
    )

    # This will raise PromptNotFoundError if not found
    # The exception will be handled by the global exception handler
    prompts_store.update_prompt_enabled(prompt_key, request.enabled)

    action = "enabled" if request.enabled else "disabled"
    logger.info(
        f"Prompt {action} successfully",
        extra={"prompt_key": prompt_key},
    )

    return create_success_response(
        message=f"Prompt '{prompt_key}' {action} successfully"
    )
