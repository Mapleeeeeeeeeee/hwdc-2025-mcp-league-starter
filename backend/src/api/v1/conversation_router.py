"""Conversation API endpoints."""

from __future__ import annotations

import json
from collections.abc import AsyncIterator
from functools import lru_cache
from typing import Annotated

from fastapi import APIRouter, Depends, Response
from src.integrations.llm import ConversationAgentFactory, LLMModelConfig
from src.models.conversation import (
    ConversationReply,
    ConversationRequest,
    ListModelsResponse,
    LLMModelDescriptor,
    UpsertLLMModelRequest,
)
from src.shared.response import APIResponse, create_success_response
from src.usecases.conversation import ConversationUsecase
from starlette.responses import StreamingResponse


@lru_cache(maxsize=1)
def get_agent_factory() -> ConversationAgentFactory:
    return ConversationAgentFactory()


router = APIRouter(prefix="/conversation", tags=["conversation"])


AgentFactoryDep = Annotated[ConversationAgentFactory, Depends(get_agent_factory)]


def get_conversation_usecase(
    agent_factory: AgentFactoryDep,
) -> ConversationUsecase:
    return ConversationUsecase(agent_factory=agent_factory)


ConversationUsecaseDep = Annotated[
    ConversationUsecase, Depends(get_conversation_usecase)
]


@router.post("", response_model=APIResponse[ConversationReply])
async def generate_conversation_reply(
    payload: ConversationRequest,
    usecase: ConversationUsecaseDep,
) -> APIResponse[ConversationReply]:
    reply = await usecase.generate_reply(payload)
    return create_success_response(data=reply, message="Conversation reply generated")


@router.post("/stream")
async def stream_conversation_reply(
    payload: ConversationRequest,
    usecase: ConversationUsecaseDep,
) -> Response:
    async def event_stream() -> AsyncIterator[str]:
        async for chunk in usecase.stream_reply(payload):
            data = json.dumps(chunk.model_dump(by_alias=True))
            yield f"data: {data}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")


@router.get("/models", response_model=APIResponse[ListModelsResponse])
async def list_models(
    agent_factory: AgentFactoryDep,
) -> APIResponse[ListModelsResponse]:
    configs = agent_factory.get_available_models()
    models = [
        LLMModelDescriptor(
            key=config.key,
            provider=config.provider,
            model_id=config.model_id,
            supports_streaming=config.supports_streaming,
            metadata=config.metadata,
            base_url=config.base_url,
        )
        for config in configs
    ]
    payload = ListModelsResponse(
        active_model_key=agent_factory.get_active_model_key(),
        models=models,
    )
    return create_success_response(data=payload, message="Model list retrieved")


@router.put("/models/{model_key}", status_code=204)
async def update_active_model(
    model_key: str,
    agent_factory: AgentFactoryDep,
) -> Response:
    agent_factory.set_active_model_key(model_key)
    return Response(status_code=204)


@router.post("/models", response_model=APIResponse[LLMModelDescriptor], status_code=201)
async def upsert_model(
    payload: UpsertLLMModelRequest,
    agent_factory: AgentFactoryDep,
) -> APIResponse[LLMModelDescriptor]:
    config = LLMModelConfig(
        key=payload.key,
        provider=payload.provider,
        model_id=payload.model_id,
        api_key_env=payload.api_key_env,
        base_url=payload.base_url,
        default_params=dict(payload.default_params or {}),
        supports_streaming=payload.supports_streaming,
        metadata=dict(payload.metadata or {}),
    )

    agent_factory.register_model(config)
    if payload.set_active:
        agent_factory.set_active_model_key(config.key)

    descriptor = LLMModelDescriptor(
        key=config.key,
        provider=config.provider,
        model_id=config.model_id,
        supports_streaming=config.supports_streaming,
        metadata=config.metadata,
        base_url=config.base_url,
    )

    return create_success_response(
        data=descriptor,
        message="Model configuration updated",
    )
