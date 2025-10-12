"""Conversation API endpoints."""

from __future__ import annotations

import asyncio
import json
from collections.abc import AsyncIterator
from functools import lru_cache
from typing import Annotated

from fastapi import APIRouter, Depends, Response
from src.core import get_logger
from src.integrations.llm import ConversationAgentFactory
from src.models import (
    ConversationReply,
    ConversationRequest,
    ListModelsResponse,
    LLMModelDescriptor,
    UpsertLLMModelRequest,
)
from src.shared.exceptions.llm import LLMStreamError
from src.shared.response import APIResponse, create_success_response
from src.usecases.conversation import ConversationUsecase, ModelManagementUsecase
from starlette.responses import StreamingResponse


@lru_cache(maxsize=1)
def get_agent_factory() -> ConversationAgentFactory:
    return ConversationAgentFactory()


router = APIRouter(prefix="/conversation", tags=["conversation"])
logger = get_logger(__name__)


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
    async def event_stream_with_heartbeat() -> AsyncIterator[str]:
        """
        Stream events with heartbeat to prevent timeout during long operations.
        Sends SSE comment (': heartbeat') every 15 seconds if no data.
        """
        heartbeat_interval = 15.0  # seconds
        last_event_time = asyncio.get_event_loop().time()

        async def heartbeat_sender():
            """Send periodic heartbeat comments to keep connection alive."""
            nonlocal last_event_time
            while True:
                await asyncio.sleep(heartbeat_interval)
                current_time = asyncio.get_event_loop().time()
                if current_time - last_event_time >= heartbeat_interval:
                    yield ": heartbeat\n\n"

        async def data_sender():
            """Send actual streaming data and update last event time."""
            nonlocal last_event_time
            try:
                async for chunk in usecase.stream_reply(payload):
                    last_event_time = asyncio.get_event_loop().time()
                    data = json.dumps(chunk.model_dump(by_alias=True))
                    yield f"data: {data}\n\n"
            except LLMStreamError as exc:
                last_event_time = asyncio.get_event_loop().time()
                error_payload = {
                    "type": exc.__class__.__name__,
                    "message": exc.detail,
                    "context": exc.context or None,
                }
                yield f"event: error\ndata: {json.dumps(error_payload)}\n\n"
            except Exception as exc:  # pragma: no cover - defensive
                logger.exception("Streaming conversation failed", exc_info=exc)
                last_event_time = asyncio.get_event_loop().time()
                message = getattr(exc, "detail", str(exc)) or "Streaming error"
                error_payload = {
                    "type": exc.__class__.__name__,
                    "message": message,
                    "context": getattr(exc, "context", None),
                }
                yield f"event: error\ndata: {json.dumps(error_payload)}\n\n"

        # Merge heartbeat and data streams
        heartbeat_gen = heartbeat_sender()
        data_gen = data_sender()

        # Use asyncio to interleave both generators
        pending = {
            asyncio.create_task(anext(heartbeat_gen)): "heartbeat",
            asyncio.create_task(anext(data_gen)): "data",
        }

        try:
            while pending:
                done, pending_set = await asyncio.wait(
                    pending.keys(), return_when=asyncio.FIRST_COMPLETED
                )

                # Process completed tasks BEFORE modifying pending dict
                for task in done:
                    source = pending[task]  # Get source before removing
                    try:
                        result = task.result()
                        yield result

                        # Create new task for the same source
                        if source == "heartbeat":
                            new_task = asyncio.create_task(anext(heartbeat_gen))
                            pending[new_task] = "heartbeat"
                        elif source == "data":
                            new_task = asyncio.create_task(anext(data_gen))
                            pending[new_task] = "data"
                    except StopAsyncIteration:
                        # One of the generators finished
                        if source == "data":
                            # Data stream finished, stop heartbeat too
                            for remaining_task in pending_set:
                                remaining_task.cancel()
                            return
                    finally:
                        # Remove completed task from pending
                        del pending[task]
        finally:
            # Cleanup
            for task in pending.keys():
                task.cancel()

    return StreamingResponse(
        event_stream_with_heartbeat(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",  # Disable Nginx buffering
            "Connection": "keep-alive",
        },
    )


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
