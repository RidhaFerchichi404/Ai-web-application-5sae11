# API

Status: `GET /api/health`, `GET /api/models`, and stateless `POST /api/chat` are implemented. Every other route on this page is `Status: Planned`.

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

Status: Planned. Phase 4.

Lists conversations for the sidebar, newest activity first. An optional search string will filter by title.

### `POST /api/conversations`

Status: Planned. Phase 4.

Creates a conversation. The title may be omitted and filled from the first message later.

### `GET /api/conversations/{id}`

Status: Planned. Phase 4.

Returns one conversation.

### `PATCH /api/conversations/{id}`

Status: Planned. Phase 4.

Renames a conversation or updates the stored chat model name.

### `DELETE /api/conversations/{id}`

Status: Planned. Phase 4.

Deletes a conversation and its messages. Linked document rows stay, with the conversation link cleared.

## Messages and chat

### `GET /api/conversations/{id}/messages`

Status: Planned. Phase 4.

Returns messages for a conversation in creation order.

### `POST /api/chat`

Status: Implemented for a single message. Phase 4 will add conversation ids and persistence. Phase 6 will add document context.

Body:

```json
{ "message": "Hello", "model": null }
```

`message` is required. `model` is optional. When it is omitted or null, the server uses `OLLAMA_CHAT_MODEL`. A model that is not installed returns `404` with code `model_not_installed`. The server does not fall back to another provider. This route does not read or write MySQL.

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
