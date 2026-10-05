# Testing

Status: Planned, except the health test in `backend/tests/test_health.py`, which is implemented and does not need MySQL. Phase 9 will implement the rest of the strategy below.

Tests will not call a cloud language-model API.

## Unit testing

Backend unit tests will cover pure behavior: filename sanitization, chunk splitting, prompt assembly, status transitions, and configuration parsing. They will not need MySQL or Ollama. External calls will be replaced with fakes.

Frontend unit tests will cover presentational components with fixed props: a message bubble, an empty state, a document row.

## Integration testing

Integration tests will use the real boundaries the feature needs:

- MySQL 8.x for persistence tests, against a dedicated test database, not a developer’s only copy of `local_ai_assistant`.
- Ollama for a small set of live checks, skipped when Ollama is not running, so a machine without models can still run the rest of the suite.

PostgreSQL will not be used as the test database.

## API testing

API tests will call FastAPI routes with a test client:

- `GET /api/health`
- Conversation create, list, rename, and delete
- Message listing
- Chat validation errors without requiring a full model when the Ollama client is faked
- Document upload rejection for type and size
- Document list and delete

Each route in [api.md](api.md) should have at least one success case and one failure case once it exists.

## RAG testing

RAG tests will use a tiny fixture document and a fake embedding function that returns stable vectors. They will assert that:

- Chunks are ordered and stored
- A query returns the fixture passage through the vector repository
- The prompt contains a separate context block
- A document with no extracted text becomes `FAILED`

A smaller live test may call the configured Ollama embedding model when it is installed. That test is optional in CI if no model is present.

## Document-processing testing

Fixture files will cover one small PDF, one DOCX, one TXT, and one Markdown file. Tests will check extracted text, rejection of a disallowed extension, and the status path `UPLOADED` → `PROCESSING` → `READY` or `FAILED`.

PyMuPDF and python-docx will run in these tests. The tests will not execute the fixture files.

## Ollama integration testing

When Ollama is available, one test will hit the health check, one will request a short completion from `OLLAMA_CHAT_MODEL`, and one will request an embedding from `OLLAMA_EMBEDDING_MODEL`. Assertions will check shape and a non-empty result, not a specific sentence. Model names stay configurable so the test reads the environment instead of assuming `qwen3:8b` or `nomic-embed-text`.

## Frontend testing

Component tests will render the sidebar, thread, and composer. Interaction tests will type a draft, submit it against a mocked API, and show streamed text as chunks arrive. The mock will follow the stream framing chosen in Phase 3.

## End-to-end testing

One end-to-end path will create a conversation, send a message, and see a streamed reply persisted after refresh. A second path will upload a TXT file, wait until it is `READY`, and ask a question whose answer depends on that file.

These tests need MySQL, Ollama, the backend, and the frontend. They are not part of the default unit run. Phase 9 will document how to start them. They are not runnable in Phase 1.

## What not to test yet

The health route is covered. Add further tests when the feature they describe exists.
