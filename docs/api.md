# API

Status: Health, models, conversations, messages, and `POST /api/chat` are implemented. Document routes on this page are `Status: Planned`.

The frontend will call FastAPI over HTTP. Responses will be JSON except for the streamed chat body. Errors will use a small JSON shape and will not leak stack traces, filesystem paths, or database details. See [security.md](security.md).

Base path: `/api`.

## Health

### `GET /api/health`

Status: Implemented.

Returns `{"status": "ok"}` when the API process is running. It does not check MySQL or Ollama. A later phase may add those checks.

## Models

### `GET /api/models`

Status: Implemented.

Returns the model names installed in Ollama, `chat_model`, `embedding_model`, and booleans `chat_model_installed` and `embedding_model_installed`. The server does not invent models that are not installed. If Ollama cannot be reached, the response is `503` with code `ollama_unavailable`.

## Conversations

### `GET /api/conversations`

Status: Implemented.

Lists the local user's conversations, newest `updated_at` first. Optional query `q` filters by title. The response does not include `user_id`.

### `POST /api/conversations`

Status: Implemented.

Creates a conversation. The title may be omitted and is stored as `New conversation` until the first chat message replaces it. Optional `chat_model` must already be installed in Ollama.

### `GET /api/conversations/{id}`

Status: Implemented.

Returns one conversation. An unknown id returns `404` with code `conversation_not_found`.

### `PATCH /api/conversations/{id}`

Status: Implemented.

Renames a conversation or updates the stored chat model name. An empty title is rejected. A new chat model name must be installed.

### `DELETE /api/conversations/{id}`

Status: Implemented.

Deletes a conversation and its messages. Linked document rows stay, with the conversation link cleared.

## Messages and chat

### `GET /api/conversations/{id}/messages`

Status: Implemented.

Returns messages for a conversation in creation order: `id`, `role`, `content`, and `created_at`.

### `POST /api/chat`

Status: Implemented. Phase 6 will add document context.

Body:

```json
{ "conversation_id": 1, "message": "Hello", "model": null }
```

`conversation_id` and `message` are required. `model` is optional. When it is omitted or null, the server uses the conversation's stored chat model, or `OLLAMA_CHAT_MODEL` when that is empty. The chosen installed model is saved on the conversation. A missing conversation returns `404` with code `conversation_not_found`. A model that is not installed returns `404` with code `model_not_installed`. The server does not fall back to another provider.

The user message is stored before streaming. Ollama receives the stored user and assistant turns for that conversation. The assistant reply is stored once, when the stream finishes or the client disconnects. Empty assistant text is not stored. Partial tokens are not written one by one.

The response is `application/x-ndjson`. Each line is one JSON object:

```json
{ "content": "Hel", "done": false }
```

`content` is the text in that chunk and may be empty. `done` is true on the last line. If Ollama fails after the stream has started, the stream ends with one line `{"error": {"code": "...", "message": "..."}}`.

Closing the client connection cancels the Ollama request. There is no cancel route.

## Documents

### `POST /api/documents`

Status: Planned. Phase 5.

Multipart upload. The server will check extension, detected type, and size against `MAX_FILE_SIZE_MB`, then store the file and return metadata with status `UPLOADED`. Phase 6 will move the document through `PROCESSING` to `READY` or `FAILED`. See [file-processing.md](file-processing.md).

Accepted types, planned: PDF, DOCX, TXT, and Markdown.

### `GET /api/documents`

Status: Planned. Phase 5.

Lists documents with filename, type, size, status, and upload time.

### `GET /api/documents/{id}`

Status: Planned. Phase 5.

Returns one document’s metadata. It will not return the raw file unless a later decision adds a download route.

### `DELETE /api/documents/{id}`

Status: Planned. Phase 5.

Deletes the metadata, chunks, and stored bytes.

## Not in this API

- No cloud model proxy.
- No authentication routes in Phases 1–10.
- No endpoint that executes or returns a shell over an uploaded file.
