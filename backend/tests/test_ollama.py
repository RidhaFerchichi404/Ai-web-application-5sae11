import json

import httpx
import pytest
from fastapi.testclient import TestClient

from app.api.ollama import get_ollama_service
from app.core.config import get_settings
from app.main import app
from app.services.ollama import OllamaService


@pytest.fixture
def ollama_transport():
    def apply(handler):
        app.dependency_overrides[get_ollama_service] = lambda: OllamaService(
            get_settings(),
            transport=httpx.MockTransport(handler),
        )

    yield apply
    app.dependency_overrides.pop(get_ollama_service, None)


def _tags(*names: str) -> httpx.Response:
    return httpx.Response(200, json={"models": [{"name": name} for name in names]})


def test_list_models(ollama_transport) -> None:
    settings = get_settings()

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/api/tags"
        return _tags(settings.ollama_chat_model, "other")

    ollama_transport(handler)
    response = TestClient(app).get("/api/models")

    assert response.status_code == 200
    body = response.json()
    assert body["models"] == [settings.ollama_chat_model, "other"]
    assert body["chat_model"] == settings.ollama_chat_model
    assert body["embedding_model"] == settings.ollama_embedding_model
    assert body["chat_model_installed"] is True
    assert body["embedding_model_installed"] is False


def test_models_when_ollama_is_down(ollama_transport) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("refused")

    ollama_transport(handler)
    response = TestClient(app).get("/api/models")

    assert response.status_code == 503
    assert response.json() == {
        "error": {"code": "ollama_unavailable", "message": "Ollama is unavailable."}
    }


def test_chat_requires_conversation() -> None:
    response = TestClient(app).post("/api/chat", json={"message": "hello"})

    assert response.status_code == 422


def test_iter_chat_sends_history() -> None:
    chat_model = get_settings().ollama_chat_model
    history = [
        {"role": "user", "content": "hello"},
        {"role": "assistant", "content": "Hi"},
        {"role": "user", "content": "again"},
    ]

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/api/tags":
            return _tags(chat_model)
        body = json.loads(request.content)
        assert body["model"] == chat_model
        assert body["stream"] is True
        assert body["messages"] == history
        raw = "\n".join(
            [
                json.dumps({"message": {"content": "Hel"}, "done": False}),
                json.dumps({"message": {"content": "lo"}, "done": True}),
            ]
        )
        return httpx.Response(200, text=raw)

    service = OllamaService(get_settings(), transport=httpx.MockTransport(handler))
    import asyncio

    async def collect() -> list[dict]:
        return [chunk async for chunk in service.iter_chat(history, chat_model)]

    assert asyncio.run(collect()) == [
        {"content": "Hel", "done": False},
        {"content": "lo", "done": True},
    ]


def test_embed_uses_configured_model() -> None:
    embedding_model = get_settings().ollama_embedding_model

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/api/tags":
            return _tags(embedding_model)
        body = json.loads(request.content)
        assert body["model"] == embedding_model
        return httpx.Response(200, json={"embeddings": [[0.25, 0.5]]})

    service = OllamaService(get_settings(), transport=httpx.MockTransport(handler))
    import asyncio

    assert asyncio.run(service.embed("hello")) == [0.25, 0.5]


def test_embed_reports_missing_model() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return _tags(get_settings().ollama_chat_model)

    service = OllamaService(get_settings(), transport=httpx.MockTransport(handler))
    import asyncio

    with pytest.raises(Exception) as caught:
        asyncio.run(service.embed("hello"))
    assert caught.value.code == "model_not_installed"
