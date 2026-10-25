import json
from collections.abc import AsyncIterator

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.session import get_db
from app.schemas.ollama import ChatRequest, ModelsResponse
from app.services import conversations as conversation_service
from app.services.conversations import ConversationNotFound
from app.services.ollama import OllamaService, OllamaServiceError

router = APIRouter()


def get_ollama_service() -> OllamaService:
    return OllamaService(get_settings())


def _http_error(exc: OllamaServiceError) -> HTTPException:
    return HTTPException(status_code=exc.status_code, detail={"code": exc.code, "message": exc.message})


@router.get("/models", response_model=ModelsResponse)
async def list_models(service: OllamaService = Depends(get_ollama_service)) -> ModelsResponse:
    try:
        installed = await service.list_models()
    except OllamaServiceError as exc:
        raise _http_error(exc) from exc
    return ModelsResponse(
        models=installed,
        chat_model=service.chat_model,
        embedding_model=service.embedding_model,
        chat_model_installed=service.chat_model in installed,
        embedding_model_installed=service.embedding_model in installed,
    )


async def iter_chat_events(
    request: Request,
    service: OllamaService,
    history: list[dict[str, str]],
    model: str,
    db: Session,
    conversation_id: int,
) -> AsyncIterator[str]:
    """Stream NDJSON and store the assistant text once, including a client stop."""
    parts: list[str] = []
    try:
        async for chunk in service.iter_chat(history, model):
            if await request.is_disconnected():
                return
            content = chunk["content"] if isinstance(chunk.get("content"), str) else ""
            parts.append(content)
            yield json.dumps({"content": content, "done": bool(chunk.get("done"))}) + "\n"
    except OllamaServiceError as exc:
        yield json.dumps({"error": {"code": exc.code, "message": exc.message}}) + "\n"
    finally:
        conversation_service.save_assistant(db, conversation_id, "".join(parts))


@router.post("/chat")
async def chat(
    body: ChatRequest,
    request: Request,
    service: OllamaService = Depends(get_ollama_service),
    db: Session = Depends(get_db),
) -> StreamingResponse:
    try:
        conversation = conversation_service.get_conversation(db, body.conversation_id)
    except ConversationNotFound as exc:
        raise HTTPException(
            status_code=404,
            detail={"code": "conversation_not_found", "message": str(exc)},
        ) from exc
    model = body.model or conversation.chat_model or service.chat_model
    try:
        await service.require_model(model)
    except OllamaServiceError as exc:
        raise _http_error(exc) from exc
    history = conversation_service.begin_turn(db, conversation, body.message, model)
    return StreamingResponse(
        iter_chat_events(request, service, history, model, db, conversation.id),
        media_type="application/x-ndjson",
    )
