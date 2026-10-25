import asyncio
import json

import httpx
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.ollama import get_ollama_service, iter_chat_events
from app.main import app
from app.models.conversation import Conversation
from app.models.document import Document
from app.models.message import Message
from app.services import conversations as conversation_service
from app.services.ollama import OllamaService
from tests.database import db_server_up

pytestmark = pytest.mark.skipif(not db_server_up(), reason="PostgreSQL is unreachable")


def _tags(*names: str) -> httpx.Response:
    return httpx.Response(200, json={"models": [{"name": name} for name in names]})


def _use_ollama(handler) -> None:
    from app.core.config import get_settings

    app.dependency_overrides[get_ollama_service] = lambda: OllamaService(
        get_settings(),
        transport=httpx.MockTransport(handler),
    )


def test_conversation_crud_search_and_delete(db: Session) -> None:
    from app.core.config import get_settings

    chat_model = get_settings().ollama_chat_model

    def handler(request: httpx.Request) -> httpx.Response:
        return _tags(chat_model, "other-model")

    _use_ollama(handler)
    with TestClient(app) as client:
        created = client.post("/api/conversations", json={})
        assert created.status_code == 201
        body = created.json()
        assert body["title"] == "New conversation"
        assert body["chat_model"] is None
        assert "user_id" not in body
        conversation_id = body["id"]

        renamed = client.patch(
            f"/api/conversations/{conversation_id}",
            json={"title": "Alpha notes", "chat_model": chat_model},
        )
        assert renamed.status_code == 200
        assert renamed.json()["title"] == "Alpha notes"
        assert renamed.json()["chat_model"] == chat_model

        other = client.post("/api/conversations", json={"title": "Beta"})
        assert other.status_code == 201

        listed = client.get("/api/conversations", params={"q": "Alpha"})
        assert listed.status_code == 200
        assert [item["title"] for item in listed.json()] == ["Alpha notes"]

        missing = client.get("/api/conversations/999999")
        assert missing.status_code == 404
        assert missing.json()["error"]["code"] == "conversation_not_found"

        blank = client.patch(f"/api/conversations/{conversation_id}", json={"title": "  "})
        assert blank.status_code == 422
        assert blank.json()["error"]["code"] == "invalid_title"

        not_installed = client.post("/api/conversations", json={"chat_model": "missing-model"})
        assert not_installed.status_code == 404
        assert not_installed.json()["error"]["code"] == "model_not_installed"

        user = conversation_service.find_local_user(db)
        assert user is not None
        document = Document(
            user_id=user.id,
            conversation_id=conversation_id,
            original_filename="notes.txt",
            stored_filename=f"stored-{conversation_id}.txt",
            media_type="text/plain",
            extension="txt",
            size_bytes=12,
            status="UPLOADED",
        )
        db.add(Message(conversation_id=conversation_id, role="user", content="keep me"))
        db.add(document)
        db.commit()
        document_id = document.id

        deleted = client.delete(f"/api/conversations/{conversation_id}")
        assert deleted.status_code == 204
        db.expire_all()
        assert db.get(Conversation, conversation_id) is None
        remaining = list(db.scalars(select(Message).where(Message.conversation_id == conversation_id)))
        assert remaining == []
        stored = db.get(Document, document_id)
        assert stored is not None
        assert stored.conversation_id is None
    app.dependency_overrides.pop(get_ollama_service, None)


def test_chat_persists_mocked_stream_and_history(db: Session) -> None:
    from app.core.config import get_settings

    chat_model = get_settings().ollama_chat_model
    seen: list[list[dict[str, str]]] = []

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/api/tags":
            return _tags(chat_model)
        body = json.loads(request.content)
        seen.append(body["messages"])
        if len(seen) == 1:
            raw = "\n".join(
                [
                    json.dumps({"message": {"content": "Hel"}, "done": False}),
                    json.dumps({"message": {"content": "lo"}, "done": True}),
                ]
            )
        else:
            raw = json.dumps({"message": {"content": "Again"}, "done": True})
        return httpx.Response(200, text=raw)

    _use_ollama(handler)
    with TestClient(app) as client:
        created = client.post("/api/conversations", json={})
        conversation_id = created.json()["id"]
        with client.stream(
            "POST",
            "/api/chat",
            json={"conversation_id": conversation_id, "message": "First question line\nmore"},
        ) as response:
            assert response.status_code == 200
            lines = [json.loads(line) for line in response.iter_lines() if line]
        assert lines == [
            {"content": "Hel", "done": False},
            {"content": "lo", "done": True},
        ]
        db.expire_all()
        stored = conversation_service.list_messages(db, conversation_id)
        assert [(row.role, row.content) for row in stored] == [
            ("user", "First question line\nmore"),
            ("assistant", "Hello"),
        ]
        conversation = conversation_service.get_conversation(db, conversation_id)
        assert conversation.title == "First question line"
        assert conversation.chat_model == chat_model

        with client.stream(
            "POST",
            "/api/chat",
            json={"conversation_id": conversation_id, "message": "Second"},
        ) as response:
            assert response.status_code == 200
            list(response.iter_lines())

    assert seen[1] == [
        {"role": "user", "content": "First question line\nmore"},
        {"role": "assistant", "content": "Hello"},
        {"role": "user", "content": "Second"},
    ]
    app.dependency_overrides.pop(get_ollama_service, None)


def test_chat_rejects_missing_model_without_saving(db: Session) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return _tags("other")

    _use_ollama(handler)
    with TestClient(app) as client:
        created = client.post("/api/conversations", json={"title": "Kept"})
        conversation_id = created.json()["id"]
        response = client.post("/api/chat", json={"conversation_id": conversation_id, "message": "hello"})
        assert response.status_code == 404
        assert response.json()["error"]["code"] == "model_not_installed"
        missing = client.post("/api/chat", json={"conversation_id": 999999, "message": "hello"})
        assert missing.status_code == 404
        assert missing.json()["error"]["code"] == "conversation_not_found"
    db.expire_all()
    assert conversation_service.list_messages(db, conversation_id) == []
    app.dependency_overrides.pop(get_ollama_service, None)


def test_stopped_stream_stores_partial_reply(db: Session) -> None:
    from app.core.config import get_settings

    conversation = conversation_service.create_conversation(db, "Kept title", None)
    history = conversation_service.begin_turn(db, conversation, "hello", get_settings().ollama_chat_model)

    class DisconnectAfterFirst:
        def __init__(self) -> None:
            self.calls = 0

        async def is_disconnected(self) -> bool:
            self.calls += 1
            return self.calls > 1

    class Scripted:
        async def iter_chat(self, messages, model):
            yield {"content": "Hel", "done": False}
            yield {"content": "lo", "done": True}

    async def collect() -> list[str]:
        return [
            line
            async for line in iter_chat_events(
                DisconnectAfterFirst(),
                Scripted(),
                history,
                get_settings().ollama_chat_model,
                db,
                conversation.id,
            )
        ]

    lines = asyncio.run(collect())
    assert len(lines) == 1
    db.expire_all()
    stored = conversation_service.list_messages(db, conversation.id)
    assert [(row.role, row.content) for row in stored] == [
        ("user", "hello"),
        ("assistant", "Hel"),
    ]
