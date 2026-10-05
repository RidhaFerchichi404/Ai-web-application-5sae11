# AI

Status: Chat, model listing, and the embedding client are implemented. Conversation history and retrieval are later phases.

## Ollama's role

Ollama is the only model runtime. FastAPI calls Ollama’s local HTTP API for:

- Chat completions, including streamed output
- Listing installed models
- An embedding call that chat does not use

`GET /api/health` stays a process check. Ollama reachability is `GET /api/models`, which returns 503 when the base URL is unreachable.

The application does not call OpenAI, Gemini, Claude, or any other hosted language-model API.

Ollama is expected to run on the host. The example base URL is `http://localhost:11434`. GPU access stays simpler when Ollama is not placed behind an extra container. CPU-only hosts are valid. The project does not require a specific GPU.

## Chat model

The chat model answers the user. Its name comes from `OLLAMA_CHAT_MODEL`, or from the model the user selects in the interface once Phase 7 exists. A conversation may store the chosen name on `conversations.chat_model`.

Example only, not a required model:

```env
OLLAMA_CHAT_MODEL=qwen3:8b
```

The user must pull the model in Ollama before the app can use it. If the name is missing or not installed, the API returns a clear error and does not switch to another provider.

## Embedding model

The embedding model turns chunk text and user questions into vectors for retrieval. It is separate from the chat model. Its name comes from `OLLAMA_EMBEDDING_MODEL`.

Example only:

```env
OLLAMA_EMBEDDING_MODEL=nomic-embed-text
```

Chat and embedding models can be changed independently. They must stay compatible with each other only in the sense that the same embedding model is used both when chunks are indexed and when a question is searched.

## Local inference

Text will leave the machine only if the user copies it or a later feature explicitly sends it somewhere. Phase 1 through Phase 10 do not add that feature. Prompts, documents, and completions stay between the browser, FastAPI, MySQL, and local Ollama.

## Model configuration

```env
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_CHAT_MODEL=qwen3:8b
OLLAMA_EMBEDDING_MODEL=nomic-embed-text
```

These values are examples. Deployments will set their own model names. Code will read configuration at startup and will not bake a model id into source files.

## Model selection

`GET /api/models` lists installed Ollama models, the configured chat and embedding names, and whether each configured model is installed. The composer will show the active chat model. Selecting another installed model will apply to the next message and, in Phase 4, update the conversation stored model name. The embedding model stays a server setting, because mixing embedding models in one index would make similarity meaningless.

## Streaming

Chat responses stream from Ollama through FastAPI as newline-delimited JSON. The framing is documented in [api.md](api.md). Closing the client connection stops generation. A cancel route is not provided.

Phase 3 sends only the current user message. History sent to the model will be the persisted messages for that conversation, plus any retrieved chunks when RAG is enabled for the request. The server will not stream partial text into MySQL. It will store the completed assistant message when the stream finishes. If the user stops early, the stored assistant message will be the text received before the stop.

## Error handling

Failures the Ollama service surfaces:

- Base URL unreachable
- HTTP error from Ollama
- Chat model not installed
- Embedding model not installed
- Stream interrupted before any tokens

The client will see a short message. Logs on the server may include the Ollama status code. Logs will not include database passwords or full document dumps by default.

See also [architecture.md](architecture.md) and [rag.md](rag.md).
