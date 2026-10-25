import json
import os

import httpx
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app.services import conversations as conversation_service
from tests.database import db_server_up


def _configured_model_is_installed() -> bool:
    base_url = os.environ.get("OLLAMA_BASE_URL", "").rstrip("/")
    model = os.environ.get("OLLAMA_CHAT_MODEL", "")
    if not base_url or not model:
        return False
    try:
        response = httpx.get(f"{base_url}/api/tags", timeout=2.0)
        response.raise_for_status()
    except httpx.HTTPError:
        return False
    names = [item.get("name") for item in response.json().get("models", [])]
    return model in names


@pytest.mark.skipif(
    not db_server_up() or not _configured_model_is_installed(),
    reason="PostgreSQL is down, or Ollama is down, or OLLAMA_CHAT_MODEL is not installed",
)
def test_live_chat_stream(db: Session) -> None:
    model = os.environ["OLLAMA_CHAT_MODEL"]
    with TestClient(app) as client:
        created = client.post("/api/conversations", json={})
        assert created.status_code == 201
        conversation_id = created.json()["id"]
        with client.stream(
            "POST",
            "/api/chat",
            json={"conversation_id": conversation_id, "message": "Reply with the word ok."},
        ) as response:
            assert response.status_code == 200
            lines = [json.loads(line) for line in response.iter_lines() if line]

    assert lines
    assert any(isinstance(line.get("content"), str) and line["content"] for line in lines)
    assert lines[-1]["done"] is True
    assert all("error" not in line for line in lines)
    db.expire_all()
    stored = conversation_service.list_messages(db, conversation_id)
    assert [row.role for row in stored] == ["user", "assistant"]
    assert stored[1].content
    assert model
