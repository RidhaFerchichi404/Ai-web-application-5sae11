# Development

Status: Defined as the working plan. Phases 1, 2, and 3 are complete. Later phases are Planned. Phase 4 has not started.

Build one phase at a time. Do not start a phase until the previous phase is accepted. Do not describe a phase as done because its design is written here.

The target shape stays:

```text
Next.js
    │
    ▼
FastAPI
    │
    ├──── MySQL
    │
    └──── Ollama
```

RAG will be added inside FastAPI during Phase 6. Do not introduce extra services unless a later requirement makes the current design fail.

## PHASE 1 — FOUNDATION

Status: Complete.

This phase prepared the specification and the empty repository layout. It did not build the application.

Tasks:

- Repository inspection
- Architecture definition
- README
- Documentation
- Development roadmap
- Environment template
- Git configuration
- Project structure definition

Definition of done:

- Repository inspected
- README created
- `/docs` created
- Architecture documented
- Technology stack documented
- Database design documented
- Ollama architecture documented
- RAG architecture documented
- Frontend architecture documented
- Backend architecture documented
- File-processing architecture documented
- API planned and documented
- Security documented
- Testing strategy documented
- Deployment strategy documented
- Roadmap created
- Development phases documented
- Decision log created
- `.env.example` created
- `.gitignore` created
- Planned project structure established

## PHASE 2 — BACKEND FOUNDATION

Status: Complete.

- FastAPI project
- Configuration system
- MySQL connection
- SQLAlchemy
- Database migrations
- Health endpoint
- Logging
- Error handling

The backend lives under `backend/` using the layout in [backend.md](backend.md). Configuration reads the variables in `.env.example`. The health endpoint is `GET /api/health` and reports process liveness only.

## PHASE 3 — OLLAMA INTEGRATION

Status: Complete.

- Ollama connection
- Ollama reachability through `GET /api/models`
- Model discovery
- Chat model configuration
- Embedding model configuration
- Basic AI service
- Streaming responses

`OllamaService` calls the local Ollama HTTP API. `GET /api/models` lists installed models. `POST /api/chat` streams one user message as newline-delimited JSON and does not write to MySQL. Model names stay configurable. The examples in `.env.example` are not mandatory models. See [ai.md](ai.md) and [api.md](api.md).

## PHASE 4 — CHAT SYSTEM

Status: Planned.

- Conversations
- Messages
- Conversation history
- Create conversation
- Rename conversation
- Delete conversation
- Message persistence

Persistence will use the `conversations` and `messages` tables in [database.md](database.md). Endpoints are listed in [api.md](api.md).

## PHASE 5 — FILE MANAGEMENT

Status: Planned.

- File upload
- File validation
- File storage
- Document metadata
- File deletion
- Processing status

Supported initially:

- PDF
- DOCX
- TXT
- Markdown

Files will be stored under `UPLOAD_DIRECTORY` (example: `./storage/uploads`). Metadata will use the `documents` table. Processing behavior is specified in [file-processing.md](file-processing.md). Uploaded files will not be executed.

## PHASE 6 — RAG

Status: Planned.

- Text extraction
- Text cleaning
- Chunking
- Embeddings
- Vector storage
- Similarity search
- Context retrieval
- Context injection into Ollama prompts

Vector access will stay behind the repository described in [architecture.md](architecture.md) and [rag.md](rag.md). The planned store is MySQL. PostgreSQL and its vector extensions are out of scope.

## PHASE 7 — FRONTEND

Status: Planned.

- Next.js application
- Layout
- Sidebar
- Chat interface
- Composer
- File attachments
- Conversation history
- Model selector
- Markdown rendering
- Code blocks
- Streaming responses

Visual direction is documented in [frontend.md](frontend.md). Phase 7 builds the working interface. Phase 8 refines it.

## PHASE 8 — UX POLISH

Status: Planned.

- Odysseus-inspired visual direction, as an original dark and minimal workspace
- Animations
- Loading states
- Empty states
- Error states
- Responsive design
- Accessibility
- Keyboard shortcuts

Do not copy another product’s source, branding, logos, or proprietary assets.

## PHASE 9 — TESTING

Status: Planned.

Backend:

- Unit tests
- API tests
- Service tests
- Document-processing tests
- RAG tests

Frontend:

- Component tests
- Interaction tests

Integration:

- Ollama
- MySQL
- End-to-end chat

The strategy is in [testing.md](testing.md). Tests are not written in Phase 1.

## PHASE 10 — SECURITY & FINALIZATION

Status: Planned.

- File validation
- Path traversal prevention
- Input validation
- Error handling
- Logging
- Configuration security
- Performance improvements
- Documentation review

Authentication is not part of this phase. See [security.md](security.md).

## Working agreement

- Mark new behavior as Planned until it runs in the repository.
- Keep MySQL 8.x as the only database.
- Keep Ollama as the only model provider.
- Record architecture changes in [decisions/README.md](decisions/README.md) before coding them.
- Stop at the end of a phase and wait for review before starting the next one.
