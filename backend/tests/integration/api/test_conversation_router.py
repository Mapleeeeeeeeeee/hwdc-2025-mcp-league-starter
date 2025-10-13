"""Integration tests for the conversation router."""

from __future__ import annotations

import json
from collections.abc import AsyncIterator, Iterator
from types import SimpleNamespace

import pytest
import pytest_asyncio
from agno.agent import RunContentEvent, RunErrorEvent
from httpx import ASGITransport, AsyncClient
from src.api.v1 import conversation_router
from src.integrations.llm import LLMModelConfig
from src.main import app

pytestmark = [pytest.mark.integration, pytest.mark.api]


class StubRunOutput:
    def __init__(
        self, *, content: str | None, run_id: str | None, model: str | None
    ) -> None:
        self._content = content
        self.content = content
        self.run_id = run_id
        self.model = model

    def get_content_as_string(self) -> str | None:
        return self._content


class StubAgent:
    def __init__(self) -> None:
        self.run_output = StubRunOutput(
            content="ok", run_id="run-1", model="openai:gpt-5-mini"
        )
        self.stream_events: list[object] = []
        self.model = SimpleNamespace(id="openai:gpt-5-mini")
        self.calls: list[dict[str, object]] = []
        self.added_tools: list[object] = []

    def arun(self, *, stream: bool = False, **kwargs):
        self.calls.append({"stream": stream, **kwargs})

        if stream:

            async def iterator() -> AsyncIterator[object]:
                for event in self.stream_events:
                    yield event

            return iterator()

        async def runner():
            return self.run_output

        return runner()

    def add_tool(self, tool: object) -> None:
        self.added_tools.append(tool)


class StubAgentFactory:
    def __init__(self, *, available_models: list[LLMModelConfig]) -> None:
        self.agent = StubAgent()
        self.available_models = list(available_models)
        self.active_model_key = (
            available_models[0].key if available_models else "openai:gpt-5-mini"
        )
        self.set_active_calls: list[str] = []

    def create_agent(
        self,
        *,
        model_key: str | None = None,
        session_id: str | None = None,
        prompt_key: str | None = None,
        overrides=None,
        strict_tools: bool = False,
    ):
        return self.agent

    def get_available_models(self) -> list[LLMModelConfig]:
        return list(self.available_models)

    def get_active_model_key(self) -> str:
        return self.active_model_key

    def set_active_model_key(self, key: str) -> None:
        self.set_active_calls.append(key)
        self.active_model_key = key

    def register_model(self, config: LLMModelConfig) -> None:
        self.available_models = [
            cfg for cfg in self.available_models if cfg.key != config.key
        ]
        self.available_models.append(config)


@pytest.fixture
def stub_factory() -> Iterator[StubAgentFactory]:
    conversation_router.get_agent_factory.cache_clear()
    available = [
        LLMModelConfig(
            key="openai:gpt-5-mini",
            provider="openai",
            model_id="gpt-5-mini",
            metadata={"display_name": "OpenAI"},
        )
    ]
    factory = StubAgentFactory(available_models=available)
    app.dependency_overrides[conversation_router.get_agent_factory] = lambda: factory
    yield factory
    app.dependency_overrides.pop(conversation_router.get_agent_factory, None)
    conversation_router.get_agent_factory.cache_clear()


@pytest_asyncio.fixture
async def async_client(stub_factory: StubAgentFactory) -> AsyncIterator[AsyncClient]:
    transport = ASGITransport(app=app)
    await app.router.startup()
    try:
        async with AsyncClient(
            transport=transport, base_url="http://testserver"
        ) as client:
            yield client
    finally:
        await app.router.shutdown()


def _make_content_event(content: str, run_id: str | None = None) -> RunContentEvent:
    return RunContentEvent(content=content, run_id=run_id)


def _make_error_event(error_message: str) -> RunErrorEvent:
    return RunErrorEvent(content=error_message)


@pytest.mark.asyncio
async def test_generate_conversation_reply__returns_success_payload(
    stub_factory: StubAgentFactory,
    async_client: AsyncClient,
) -> None:
    stub_factory.agent.run_output = StubRunOutput(
        content="Hello from agent",
        run_id="run-123",
        model="openai:gpt-5-mini",
    )

    response = await async_client.post(
        "/api/v1/conversation",
        json={
            "conversationId": "conv-1",
            "history": [
                {"role": "user", "content": "Hello"},
                {"role": "assistant", "content": "Hi"},
            ],
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["data"]["messageId"] == "run-123"
    assert payload["data"]["content"] == "Hello from agent"
    assert "X-Trace-ID" in response.headers
    assert "X-Process-Time" in response.headers


@pytest.mark.asyncio
async def test_generate_conversation_reply__with_mcp_tools__registers_toolkit(
    stub_factory: StubAgentFactory,
    async_client: AsyncClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: dict[str, object] = {}

    def _fake_get_mcp_toolkit(server_name: str, *, allowed_functions=None):
        captured["server"] = server_name
        captured["functions"] = allowed_functions
        toolkit = SimpleNamespace(functions={"search_files": object()})
        return toolkit

    monkeypatch.setattr(
        "src.usecases.conversation.conversation_usecase.get_mcp_toolkit",
        _fake_get_mcp_toolkit,
    )

    response = await async_client.post(
        "/api/v1/conversation",
        json={
            "conversationId": "conv-tools",
            "history": [
                {"role": "user", "content": "List files"},
            ],
            "tools": [
                {
                    "server": "filesystem",
                    "functions": ["search_files", "  "],
                }
            ],
        },
    )

    assert response.status_code == 200
    assert stub_factory.agent.added_tools, "應該註冊至少一個 MCP 工具"
    assert captured["server"] == "filesystem"
    assert captured["functions"] == ["search_files"]
    added_tool = stub_factory.agent.added_tools[0]
    assert hasattr(added_tool, "functions")
    assert "search_files" in added_tool.functions


@pytest.mark.asyncio
async def test_generate_conversation_reply__llm_no_output__returns_error_payload(
    stub_factory: StubAgentFactory,
    async_client: AsyncClient,
) -> None:
    stub_factory.agent.run_output = StubRunOutput(content=None, run_id=None, model=None)

    response = await async_client.post(
        "/api/v1/conversation",
        json={
            "conversationId": "conv-1",
            "history": [
                {"role": "user", "content": "Hello"},
                {"role": "assistant", "content": "Hi"},
            ],
        },
    )

    assert response.status_code == 503
    payload = response.json()
    assert payload["success"] is False
    assert payload["error"]["type"] == "LLMNoOutputError"
    assert payload["error"]["context"] == {"conversation_id": "conv-1"}
    retry_info = payload.get("retry_info")
    assert retry_info is not None
    assert retry_info["retryable"] is True
    assert "X-Trace-ID" in response.headers
    assert "X-Process-Time" in response.headers


@pytest.mark.asyncio
async def test_stream_conversation_reply__emits_sse_chunks(
    stub_factory: StubAgentFactory,
    async_client: AsyncClient,
) -> None:
    factory_agent = stub_factory.agent
    factory_agent.stream_events = [
        _make_content_event("part-1", run_id="run-1"),
        _make_content_event("part-2", run_id="run-1"),
    ]

    async with async_client.stream(
        "POST",
        "/api/v1/conversation/stream",
        json={
            "conversationId": "conv-2",
            "history": [{"role": "user", "content": "Hello"}],
        },
    ) as response:
        assert response.status_code == 200
        assert response.headers["content-type"].startswith("text/event-stream")
        body = ""
        async for chunk in response.aiter_text():
            body += chunk

    messages = [line for line in body.split("\n\n") if line]

    assert len(messages) == 2
    assert messages[0].startswith("data: ")
    payload = json.loads(messages[0].removeprefix("data: "))
    assert payload["delta"] == "part-1"
    assert "X-Trace-ID" in response.headers
    assert "X-Process-Time" in response.headers


@pytest.mark.asyncio
async def test_stream_conversation_reply__error_event__returns_error_response(
    stub_factory: StubAgentFactory,
    async_client: AsyncClient,
) -> None:
    factory_agent = stub_factory.agent
    factory_agent.stream_events = [_make_error_event("boom")]

    async with async_client.stream(
        "POST",
        "/api/v1/conversation/stream",
        json={
            "conversationId": "conv-3",
            "history": [{"role": "user", "content": "Hello"}],
        },
    ) as response:
        assert response.status_code == 200
        assert response.headers["content-type"].startswith("text/event-stream")
        body = ""
        async for chunk in response.aiter_text():
            body += chunk

    messages = [line for line in body.split("\n\n") if line]

    assert len(messages) == 1
    assert messages[0].startswith("event: error\n")
    data_line = next(
        line for line in messages[0].split("\n") if line.startswith("data: ")
    )
    payload = json.loads(data_line.removeprefix("data: "))
    assert payload == {
        "type": "LLMStreamError",
        "message": "LLM stream ended unexpectedly",
        "context": {"conversation_id": "conv-3"},
    }


@pytest.mark.asyncio
async def test_model_management_endpoints__list_and_upsert(
    stub_factory: StubAgentFactory,
    async_client: AsyncClient,
) -> None:
    list_response = await async_client.get("/api/v1/conversation/models")
    upsert_response = await async_client.post(
        "/api/v1/conversation/models",
        json={
            "key": "ollama:llama3.1",
            "provider": "ollama",
            "modelId": "llama3.1",
            "supportsStreaming": True,
            "metadata": {"display_name": "Llama"},
            "setActive": True,
        },
    )
    set_active_status = (
        await async_client.put("/api/v1/conversation/models/ollama:llama3.1")
    ).status_code

    assert list_response.status_code == 200
    assert upsert_response.status_code == 201
    list_payload = list_response.json()
    upsert_payload = upsert_response.json()

    assert list_payload["data"]["activeModelKey"] == "openai:gpt-5-mini"
    assert upsert_payload["data"]["key"] == "ollama:llama3.1"
    assert set_active_status == 204
    assert stub_factory.set_active_calls[-1] == "ollama:llama3.1"
    assert "X-Trace-ID" in list_response.headers
    assert "X-Trace-ID" in upsert_response.headers
