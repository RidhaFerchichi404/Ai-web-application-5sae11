# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project status

Phase 4 (conversations and messages) is complete. Phase 5 (file management) has not started.
Database: Supabase (PostgreSQL). Backend deployed on Railway. Frontend deployed on Vercel.

## Commands

### Backend

All commands run from `backend/` using the virtual environment at `backend/.venv`.

**Windows:**
```
.venv\Scripts\python -m uvicorn app.main:app --reload --port 8000
.venv\Scripts\python -m pytest
.venv\Scripts\python -m pytest tests/test_health.py        # no PostgreSQL needed
.venv\Scripts\python -m alembic upgrade head
.venv\Scripts\python -m alembic revision --autogenerate -m "description"
```

**macOS/Linux:** activate `.venv/bin/activate` first, then use `uvicorn`, `pytest`, `alembic` directly.

Environment variables come from `.env` at the repository root. Copy `.env.example` to `.env` before first run. Every variable is required — there are no defaults for secrets. The PostgreSQL database must exist before running migrations.

### Frontend

All commands run from `frontend/`.

```
npm run dev      # local dev server on port 3000
npm run build    # production build (must pass before deploy)
npm start        # serve production build locally
```

`frontend/.env.local` sets `NEXT_PUBLIC_API_URL=http://localhost:8000` for local dev. In production (Vercel) set `NEXT_PUBLIC_API_URL` to the Railway backend URL.

## Architecture

Browser → Vercel (Next.js `frontend/`) → Railway (FastAPI `backend/`) → Supabase (PostgreSQL)
                                                                        → Ollama (via ngrok tunnel)

FastAPI is the only backend. Ollama is the only model provider — the app never calls any cloud LLM API. For deployed environments, Ollama must be exposed publicly (e.g. ngrok) and `OLLAMA_BASE_URL` must point to that URL.

**Backend layer structure inside `backend/app/`:**
- `api/` — FastAPI routers (thin: validate, call service, return response)
- `services/` — business logic and DB writes
- `schemas/` — Pydantic request/response models
- `models/` — SQLAlchemy ORM models (PostgreSQL types: `BigInteger`, `TIMESTAMP`, `Text`, `JSONB`)
- `db/` — engine and session factory (`get_db` dependency)
- `core/` — config (`get_settings` is `lru_cache`'d), logging, CORS, error handlers

**Single local user:** there are no accounts or auth. `conversations.get_or_create_local_user` finds or creates a user with `display_name = "Local"`. All conversations belong to that user.

**Streaming chat:** `POST /api/chat` returns `StreamingResponse` with `application/x-ndjson`. Each line is `{"content": "...", "done": false}`. The final line has `"done": true`. The assistant message is written to DB in a `finally` block.

**Error shape:** all HTTP errors use `{"code": "...", "message": "..."}` inside `detail`. The unhandled-exception handler returns `{"error": {"code": "internal_error", "message": "..."}}`.

**CORS:** controlled by `CORS_ORIGINS` env var (comma-separated list). Default: `http://localhost:3000`. Set to the Vercel deployment URL in production.

**Frontend structure (`frontend/`):**
- `app/chat/layout.tsx` — sidebar shell + `<Suspense>` wrapper
- `app/chat/page.tsx` — empty state
- `app/chat/[id]/page.tsx` — thin server page; renders `<ConversationContent>` in Suspense
- `components/chat/ConversationContent.tsx` — full streaming conversation UI
- `components/chat/MessageBubble.tsx` — Markdown rendering, syntax highlighting, copy
- `components/chat/Composer.tsx` — textarea + model selector + send/stop
- `components/sidebar/Sidebar.tsx` — conversation list, search, new, delete
- `lib/api.ts` — all fetch calls; `streamChat()` is an async generator over NDJSON

## Database

PostgreSQL (Supabase). Tables: `users`, `conversations`, `messages`, `documents`, `document_chunks`.
Use the **transaction pooler** connection string (port **6543**) for deployed environments to avoid exhausting connection limits. Use port 5432 for local PostgreSQL.

Alembic migrations live in `backend/alembic/versions/`. Revision IDs follow the pattern `NNNN_slug`.

The `updated_at` column is managed by `_touch()` in the service layer (explicit `func.now()`), not by a DB trigger — PostgreSQL has no column-level `ON UPDATE`.

## Testing

`tests/test_health.py` does not need PostgreSQL. Tests that touch the DB use `tests/database.py`, which connects to the `postgres` admin DB to create `local_ai_assistant_test`, runs migrations, and the `db` fixture truncates all tables with `TRUNCATE ... RESTART IDENTITY CASCADE` between tests.

## Deployment

### Railway (FastAPI backend)

1. Create a new Railway project, add a service from the GitHub repo, set **Root Directory** to `backend/`.
2. Set env vars: `APP_ENV`, `DATABASE_URL` (Supabase transaction pooler), `OLLAMA_BASE_URL` (ngrok URL), `OLLAMA_CHAT_MODEL`, `OLLAMA_EMBEDDING_MODEL`, `MAX_FILE_SIZE_MB`, `UPLOAD_DIRECTORY`, `CORS_ORIGINS` (Vercel URL).
3. Railway auto-runs `Procfile` → `uvicorn app.main:app --host 0.0.0.0 --port $PORT`.
4. Run `alembic upgrade head` via Railway shell or CI once after first deploy.

### Vercel (Next.js frontend)

1. Import the GitHub repo into Vercel; `vercel.json` at the root sets **Root Directory** to `frontend/`.
2. Set env var `NEXT_PUBLIC_API_URL` to the Railway backend URL.
3. Set `CORS_ORIGINS` on Railway to include `https://your-app.vercel.app`.

### ngrok (local Ollama for cloud deploy)

```
ngrok http 11434
```

Set `OLLAMA_BASE_URL` on Railway to the ngrok public URL. The URL changes on each `ngrok` restart unless you have a paid ngrok account with a static domain.

## Key files

| Path | Purpose |
|---|---|
| `backend/app/core/config.py` | `Settings` (pydantic-settings); all env vars incl. `cors_origins` |
| `backend/app/services/ollama.py` | `OllamaService` — only place that calls Ollama |
| `backend/app/services/conversations.py` | conversation + message CRUD and `begin_turn` |
| `backend/app/api/ollama.py` | `GET /api/models`, `POST /api/chat` with streaming |
| `backend/app/api/conversations.py` | conversation REST endpoints |
| `backend/tests/conftest.py` | pytest fixtures; `db` fixture overrides `get_db` |
| `backend/tests/database.py` | test DB bootstrap (create, migrate, engine) |
| `frontend/lib/api.ts` | all API calls; `streamChat()` async generator |
| `frontend/components/chat/ConversationContent.tsx` | main chat UI with streaming |
