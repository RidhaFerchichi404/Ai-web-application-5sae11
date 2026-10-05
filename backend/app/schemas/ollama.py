from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    message: str = Field(min_length=1)
    model: str | None = None


class ModelsResponse(BaseModel):
    models: list[str]
    chat_model: str
    embedding_model: str
    chat_model_installed: bool
    embedding_model_installed: bool
