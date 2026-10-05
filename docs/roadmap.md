# Roadmap

Status: Defined as a sequence. Phases 1, 2, and 3 are complete. Phase 4 is next and has not started. Every later phase is Planned.

```text
[DONE]
Phase 1 — Documentation and architecture

[DONE]
Phase 2 — Backend foundation

[DONE]
Phase 3 — Ollama

[NEXT]
Phase 4 — Conversations

Phase 5 — Files

Phase 6 — RAG

Phase 7 — Frontend

Phase 8 — UX

Phase 9 — Testing

Phase 10 — Security and finalization
```

## Phase 1 — Documentation and architecture

Complete. Specification, decision log, environment template, and ignore rules. Phase 1 left `frontend/`, `backend/`, and `storage/uploads/` as placeholders and did not add an application runtime.

## Phase 2 — Backend foundation

Complete. FastAPI application, configuration, MySQL connection, SQLAlchemy, migrations, health check, logging, and error handling.

## Phase 3 — Ollama

Complete. Local chat streaming, model discovery, configurable model names, and an embedding method that chat does not call. Conversations are not stored.

## Phase 4 — Conversations

Planned. Create, list, rename, and delete conversations. Persist messages.

## Phase 5 — Files

Planned. Upload, validate, store, list, and delete PDF, DOCX, TXT, and Markdown files. Track processing status.

## Phase 6 — RAG

Planned. Extract, clean, chunk, embed, store, and retrieve document context for Ollama prompts. Vector search stays behind a repository.

## Phase 7 — Frontend

Planned. Next.js workspace with sidebar, chat, composer, attachments, history, model selection, Markdown, and streaming.

## Phase 8 — UX

Planned. Original dark, minimal interface, motion, empty and error states, responsive layout, accessibility, and keyboard shortcuts.

## Phase 9 — Testing

Planned. Backend, frontend, document, RAG, Ollama, MySQL, and end-to-end coverage described in [testing.md](testing.md).

## Phase 10 — Security and finalization

Planned. Validation, path safety, sanitized errors, configuration hygiene, performance pass, and a documentation review.

Task-level detail for each phase is in [development.md](development.md).

## After Phase 10

Not scheduled. A login flow around the planned `users` table would be a new decision, not an implied part of the phases above.
