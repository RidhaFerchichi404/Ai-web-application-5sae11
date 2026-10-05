# Decision log

Status: Defined.

Record architecture choices here before implementing them. Each decision states the context, the choice, and why. Supersede a decision with a new entry instead of rewriting history.

Product scope stays a single Next.js app, a single FastAPI app, MySQL 8.x, and Ollama. See [architecture.md](../architecture.md).

## Decision 001 — Ollama

Status: Defined.

Choice: all chat and embedding inference will go through Ollama on the local machine.

Why:

- Local inference
- Privacy
- No API costs
- Model flexibility

The application will not depend on OpenAI, Gemini, Claude, or other cloud language-model APIs. Chat and embedding model names will be configuration, not hard-coded product defaults. Example names in `.env.example` are illustrations.

## Decision 002 — MySQL

Status: Defined.

Choice: MySQL 8.x is the only application database.

Why:

- Familiar relational database
- Simple data model
- Suitable for conversations and documents
- Already supported by the planned backend

PostgreSQL will not be used. A PostgreSQL vector type will not be used. Embeddings, when Phase 6 stores them, will follow Decision 005.

## Decision 003 — FastAPI

Status: Defined.

Choice: one Python FastAPI service is the backend.

Why:

- Python AI ecosystem
- Simple API development
- Excellent async support
- Good integration with Ollama and document processing

Document extraction libraries (PyMuPDF, python-docx) fit this process. The backend will not be split into microservices.

## Decision 004 — Next.js

Status: Defined.

Choice: the interface will be a Next.js application using React, TypeScript, Tailwind CSS, and shadcn/ui.

Why:

- React ecosystem
- Excellent TypeScript support
- Modern web application framework

The visual direction will be original: dark, minimal, and conversation-first. It will not copy another product’s implementation or brand.

## Decision 005 — Vector search isolation

Status: Defined as a boundary. The repository is not implemented.

Choice: similarity search will be hidden behind a vector search repository. The rest of FastAPI will request relevant chunks and will not issue storage-specific vector queries.

Planned first store: embedding arrays saved on `document_chunks` rows in MySQL, with similarity computed in the backend process. That store can be replaced later without rewriting chat or document flows.

Why:

- The relational model already lives in MySQL
- The project should stay free of an extra database
- A later store remains possible if retrieval outgrows in-process search

This decision does not add Elasticsearch, a dedicated vector server, or a PostgreSQL vector extension.
