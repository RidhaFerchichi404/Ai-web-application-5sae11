# Backend

Status: Implemented for the Phase 2 foundation. Chat, document, RAG, and Ollama services are not written. `services/` and `utils/` are packages only.

## Stack

- Python
- FastAPI
- SQLAlchemy
- Pydantic

Ollama and MySQL are external processes. Document libraries (PyMuPDF, python-docx, and Pillow when needed) will be added when file processing starts, not during the empty foundation.

## Layout

```text
backend/
└── app/
    ├── main.py
    ├── api/
    ├── core/
    ├── db/
    ├── models/
    ├── schemas/
    ├── services/
    └── utils/
```

Phase 2 created this tree and a running app. Later phases fill the modules. Do not add a second package or a second web framework.

## Directories

### `app/main.py`

Creates the FastAPI application, mounts routers, and installs error handlers. It will not contain SQL or Ollama calls inline.

### `app/api/`

HTTP routes only. Routers parse requests, call a service, and return a response or a stream. Planned routers follow [api.md](api.md): health, models, conversations, chat, and documents.

Route functions will stay thin. Business rules belong in services.

### `app/core/`

Configuration and cross-cutting setup: environment variables, logging, and shared constants such as the upload size limit. Settings will be loaded from the environment. The example names are in `.env.example`.

Secrets will not have defaults that look like production passwords. Missing required settings will fail startup with a clear message.

### `app/db/`

SQLAlchemy engine, session factory, and migration entry. The database URL will use MySQL (`mysql+pymysql`). Sessions will be request-scoped and closed when the request finishes.

### `app/models/`

SQLAlchemy models for `users`, `conversations`, `messages`, `documents`, and `document_chunks`, matching [database.md](database.md). Models describe tables. They do not call Ollama.

### `app/schemas/`

Pydantic models for request and response bodies. These are the API boundary. They are separate from SQLAlchemy models so a table change does not silently change the JSON shape.

### `app/services/`

Use cases:

- Chat service
- Conversation service
- Document service
- RAG service
- Ollama service
- Vector search repository

Responsibilities are described in [architecture.md](architecture.md). Services call each other. The vector repository is the only code that reads or writes embedding payloads.

### `app/utils/`

Small helpers that do not belong to a service: safe filenames, time formatting, and similar functions. Helpers will not open their own database sessions.

## Request flow

A typical chat turn, once Phases 3, 4, and 6 exist:

1. `api` validates the body with a Pydantic schema.
2. Conversation service loads the thread and recent messages.
3. If documents are attached, RAG service asks the vector repository for chunks.
4. Chat service builds the prompt and calls the Ollama service.
5. Tokens stream back through the route.
6. The finished assistant message is stored.

Phase 2 delivered app startup, config, a database session, logging, errors, and `GET /api/health`.

## Errors and logs

Unhandled exceptions will become a generic JSON error. Expected failures (unknown id, Ollama down, file rejected) will use explicit status codes. Logs will include a request id and the error type. They will omit secrets and uploaded file contents.

## Related documents

- [API](api.md)
- [Database](database.md)
- [AI](ai.md)
- [File processing](file-processing.md)
- [Security](security.md)
