from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.ollama import get_ollama_service
from app.db.session import get_db
from app.schemas.conversation import (
    ConversationCreate,
    ConversationResponse,
    ConversationUpdate,
    MessageResponse,
)
from app.services import conversations as conversation_service
from app.services.conversations import ConversationNotFound, InvalidTitle
from app.services.ollama import OllamaService, OllamaServiceError

router = APIRouter()


def _not_found(exc: ConversationNotFound) -> HTTPException:
    return HTTPException(
        status_code=404,
        detail={"code": "conversation_not_found", "message": str(exc)},
    )


def _invalid_title(exc: InvalidTitle) -> HTTPException:
    return HTTPException(status_code=422, detail={"code": "invalid_title", "message": str(exc)})


def _ollama_http_error(exc: OllamaServiceError) -> HTTPException:
    return HTTPException(status_code=exc.status_code, detail={"code": exc.code, "message": exc.message})


@router.get("/conversations", response_model=list[ConversationResponse])
def list_conversations(
    q: str | None = Query(default=None),
    db: Session = Depends(get_db),
) -> list[ConversationResponse]:
    return conversation_service.list_conversations(db, q)


@router.post("/conversations", response_model=ConversationResponse, status_code=201)
async def create_conversation(
    body: ConversationCreate,
    db: Session = Depends(get_db),
    ollama: OllamaService = Depends(get_ollama_service),
) -> ConversationResponse:
    chat_model = body.chat_model.strip() if body.chat_model and body.chat_model.strip() else None
    if chat_model:
        try:
            await ollama.require_model(chat_model)
        except OllamaServiceError as exc:
            raise _ollama_http_error(exc) from exc
    try:
        return conversation_service.create_conversation(db, body.title, chat_model)
    except InvalidTitle as exc:
        raise _invalid_title(exc) from exc


@router.get("/conversations/{conversation_id}", response_model=ConversationResponse)
def get_conversation(
    conversation_id: int,
    db: Session = Depends(get_db),
) -> ConversationResponse:
    try:
        return conversation_service.get_conversation(db, conversation_id)
    except ConversationNotFound as exc:
        raise _not_found(exc) from exc


@router.patch("/conversations/{conversation_id}", response_model=ConversationResponse)
async def update_conversation(
    conversation_id: int,
    body: ConversationUpdate,
    db: Session = Depends(get_db),
    ollama: OllamaService = Depends(get_ollama_service),
) -> ConversationResponse:
    fields = body.model_fields_set
    chat_model = body.chat_model.strip() if body.chat_model and body.chat_model.strip() else None
    if "chat_model" in fields and body.chat_model and chat_model is None:
        raise HTTPException(
            status_code=422,
            detail={"code": "invalid_chat_model", "message": "Chat model cannot be blank."},
        )
    if chat_model:
        try:
            await ollama.require_model(chat_model)
        except OllamaServiceError as exc:
            raise _ollama_http_error(exc) from exc
    try:
        return conversation_service.update_conversation(
            db,
            conversation_id,
            title=body.title,
            title_set="title" in fields,
            chat_model=chat_model,
            chat_model_set="chat_model" in fields,
        )
    except ConversationNotFound as exc:
        raise _not_found(exc) from exc
    except InvalidTitle as exc:
        raise _invalid_title(exc) from exc


@router.delete("/conversations/{conversation_id}", status_code=204)
def delete_conversation(conversation_id: int, db: Session = Depends(get_db)) -> None:
    try:
        conversation_service.delete_conversation(db, conversation_id)
    except ConversationNotFound as exc:
        raise _not_found(exc) from exc


@router.get("/conversations/{conversation_id}/messages", response_model=list[MessageResponse])
def list_messages(conversation_id: int, db: Session = Depends(get_db)) -> list[MessageResponse]:
    try:
        return conversation_service.list_messages(db, conversation_id)
    except ConversationNotFound as exc:
        raise _not_found(exc) from exc
