import json

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse

from app.core.config import get_settings
from app.schemas.ollama import ChatRequest, ModelsResponse
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


@router.post("/chat")
async def chat(
    body: ChatRequest,
    request: Request,
    service: OllamaService = Depends(get_ollama_service),
) -> StreamingResponse:
    model = body.model or service.chat_model
    try:
        await service.require_model(model)
    except OllamaServiceError as exc:
        raise _http_error(exc) from exc

    async def chunks():
        try:
            async for chunk in service.iter_chat(body.message, model):
                if await request.is_disconnected():
                    return
                yield json.dumps(chunk) + "\n"
        except OllamaServiceError as exc:
            yield json.dumps({"error": {"code": exc.code, "message": exc.message}}) + "\n"

    return StreamingResponse(chunks(), media_type="application/x-ndjson")
