import json
import logging
from collections.abc import AsyncIterator

import httpx

from app.core.config import Settings

logger = logging.getLogger("app.ollama")


class OllamaServiceError(Exception):
    def __init__(self, *, status_code: int, code: str, message: str) -> None:
        self.status_code = status_code
        self.code = code
        self.message = message
        super().__init__(message)


class OllamaService:
    """Client for the local Ollama HTTP API. This is the only model provider."""

    def __init__(self, settings: Settings, transport: httpx.AsyncBaseTransport | None = None) -> None:
        self._base_url = settings.ollama_base_url.rstrip("/")
        self._chat_model = settings.ollama_chat_model
        self._embedding_model = settings.ollama_embedding_model
        self._transport = transport

    @property
    def chat_model(self) -> str:
        return self._chat_model

    @property
    def embedding_model(self) -> str:
        return self._embedding_model

    async def list_models(self) -> list[str]:
        payload = await self._get("/api/tags")
        names: list[str] = []
        for item in payload.get("models", []):
            name = item.get("name")
            if isinstance(name, str) and name:
                names.append(name)
        return names

    async def require_model(self, model: str) -> None:
        installed = await self.list_models()
        if model not in installed:
            raise OllamaServiceError(
                status_code=404,
                code="model_not_installed",
                message=f"Model {model} is not installed in Ollama.",
            )

    async def iter_chat(self, message: str, model: str) -> AsyncIterator[dict[str, str | bool]]:
        """Yield one object per Ollama chunk. The last object has done=true."""
        timeout = httpx.Timeout(connect=5.0, read=None, write=30.0, pool=5.0)
        payload = {
            "model": model,
            "messages": [{"role": "user", "content": message}],
            "stream": True,
        }
        saw_done = False
        try:
            async with self._client(timeout) as client:
                async with client.stream("POST", "/api/chat", json=payload) as response:
                    if response.status_code >= 400:
                        logger.error("ollama chat failed status=%s", response.status_code)
                        raise OllamaServiceError(
                            status_code=502,
                            code="ollama_error",
                            message="Ollama rejected the chat request.",
                        )
                    async for line in response.aiter_lines():
                        if not line.strip():
                            continue
                        chunk = json.loads(line)
                        content = ""
                        message_part = chunk.get("message")
                        if isinstance(message_part, dict):
                            text = message_part.get("content")
                            if isinstance(text, str):
                                content = text
                        done = bool(chunk.get("done"))
                        saw_done = saw_done or done
                        yield {"content": content, "done": done}
        except OllamaServiceError:
            raise
        except httpx.HTTPError as exc:
            logger.error("ollama chat transport failed type=%s", type(exc).__name__)
            raise OllamaServiceError(
                status_code=503,
                code="ollama_unavailable",
                message="Ollama is unavailable.",
            ) from exc
        if not saw_done:
            yield {"content": "", "done": True}

    async def embed(self, text: str) -> list[float]:
        """Embed text with the configured embedding model. Chat does not call this."""
        await self.require_model(self._embedding_model)
        payload = await self._post(
            "/api/embed",
            {"model": self._embedding_model, "input": text},
            failure_message="Ollama rejected the embedding request.",
        )
        vectors = payload.get("embeddings")
        if not isinstance(vectors, list) or not vectors or not isinstance(vectors[0], list):
            raise OllamaServiceError(
                status_code=502,
                code="ollama_error",
                message="Ollama returned no embedding.",
            )
        return [float(value) for value in vectors[0]]

    def _client(self, timeout: httpx.Timeout) -> httpx.AsyncClient:
        kwargs: dict[str, object] = {"base_url": self._base_url, "timeout": timeout}
        if self._transport is not None:
            kwargs["transport"] = self._transport
        return httpx.AsyncClient(**kwargs)

    async def _get(self, path: str) -> dict:
        timeout = httpx.Timeout(5.0)
        try:
            async with self._client(timeout) as client:
                response = await client.get(path)
        except httpx.HTTPError as exc:
            logger.error("ollama request failed type=%s", type(exc).__name__)
            raise OllamaServiceError(
                status_code=503,
                code="ollama_unavailable",
                message="Ollama is unavailable.",
            ) from exc
        return self._read_json(response)

    async def _post(self, path: str, payload: dict, *, failure_message: str) -> dict:
        timeout = httpx.Timeout(30.0)
        try:
            async with self._client(timeout) as client:
                response = await client.post(path, json=payload)
        except httpx.HTTPError as exc:
            logger.error("ollama request failed type=%s", type(exc).__name__)
            raise OllamaServiceError(
                status_code=503,
                code="ollama_unavailable",
                message="Ollama is unavailable.",
            ) from exc
        if response.status_code >= 400:
            logger.error("ollama request failed status=%s", response.status_code)
            raise OllamaServiceError(status_code=502, code="ollama_error", message=failure_message)
        return self._read_json(response)

    def _read_json(self, response: httpx.Response) -> dict:
        if response.status_code >= 400:
            logger.error("ollama request failed status=%s", response.status_code)
            raise OllamaServiceError(
                status_code=503 if response.status_code >= 500 else 502,
                code="ollama_error",
                message="Ollama returned an error.",
            )
        try:
            payload = response.json()
        except json.JSONDecodeError as exc:
            raise OllamaServiceError(
                status_code=502,
                code="ollama_error",
                message="Ollama returned an unreadable response.",
            ) from exc
        if not isinstance(payload, dict):
            raise OllamaServiceError(
                status_code=502,
                code="ollama_error",
                message="Ollama returned an unreadable response.",
            )
        return payload
