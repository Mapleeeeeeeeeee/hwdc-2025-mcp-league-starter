"""Conversation API endpoints."""

from __future__ import annotations

import json
from collections.abc import AsyncIterator
from functools import lru_cache
from typing import Annotated

from fastapi import APIRouter, Depends, Response
from src.integrations.llm import ConversationAgentFactory
from src.models import (
    ConversationReply,
    ConversationRequest,
    ListModelsResponse,
    LLMModelDescriptor,
    UpsertLLMModelRequest,
)
from src.shared.response import APIResponse, create_success_response
from src.usecases.conversation import ConversationUsecase, ModelManagementUsecase
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


def get_model_management_usecase(
    agent_factory: AgentFactoryDep,
) -> ModelManagementUsecase:
    return ModelManagementUsecase(agent_factory)


ModelManagementUsecaseDep = Annotated[
    ModelManagementUsecase, Depends(get_model_management_usecase)
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
    usecase: ModelManagementUsecaseDep,
) -> APIResponse[ListModelsResponse]:
    payload = await usecase.list_models()
    return create_success_response(data=payload, message="Model list retrieved")


@router.put("/models/{model_key}", status_code=204)
async def update_active_model(
    model_key: str,
    usecase: ModelManagementUsecaseDep,
) -> Response:
    await usecase.set_active_model(model_key)
    return Response(status_code=204)


@router.post("/models", response_model=APIResponse[LLMModelDescriptor], status_code=201)
async def upsert_model(
    payload: UpsertLLMModelRequest,
    usecase: ModelManagementUsecaseDep,
) -> APIResponse[LLMModelDescriptor]:
    descriptor = await usecase.upsert_model(payload)
    return create_success_response(
        data=descriptor,
        message="Model configuration updated",
    )
