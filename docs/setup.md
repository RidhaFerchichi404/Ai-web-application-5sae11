# Setup

Status: Backend setup is runnable. Ollama integration and the frontend are still Planned.

## Prerequisites

| Tool | Role |
| --- | --- |
| Git | Clone and version this repository |
| Node.js and npm | Next.js frontend, from Phase 7 |
| Python | FastAPI backend, from Phase 2 |
| MySQL 8.x | Relational database |
| Ollama | Local chat and embedding models |
| Docker | Future Compose-based infrastructure |

A GPU is not required. Ollama can run on CPU. A GPU will only affect speed.

PostgreSQL is not a prerequisite. This project uses MySQL 8.x.

## Ollama

Install Ollama from the official distribution for the host operating system. This repository will not vendor Ollama.

After installation:

1. Start the Ollama service so it listens on the local API, by default `http://localhost:11434`.
2. Pull a chat model you want to use.
3. Pull an embedding model you want to use.
4. Put those model names in `.env`. The names in `.env.example` are examples only.

The application will read `OLLAMA_CHAT_MODEL` and `OLLAMA_EMBEDDING_MODEL` from the environment. Changing models will not require a code change. A later phase will also list models installed in Ollama so the interface can offer a choice.

## MySQL

Install MySQL 8.x locally, or wait for the Compose definition in a later phase. Create a database that matches `DATABASE_URL`. The example URL expects a database named `local_ai_assistant`:

```text
mysql+pymysql://username:password@localhost:3306/local_ai_assistant
```

Replace `username` and `password`. Do not commit the real `.env`.

Migrations live in `backend/alembic`. `alembic upgrade head` creates the tables. Create the empty database first.

## Environment file

From the repository root:

```text
copy .env.example .env
```

Then edit `.env`. The backend loads this file from the repository root. Missing required variables stop startup. Do not commit `.env`.

Variables:

| Variable | Purpose |
| --- | --- |
| `APP_ENV` | `development` or a later environment name |
| `DATABASE_URL` | SQLAlchemy URL for MySQL |
| `OLLAMA_BASE_URL` | Ollama HTTP API |
| `OLLAMA_CHAT_MODEL` | Default chat model name |
| `OLLAMA_EMBEDDING_MODEL` | Embedding model name |
| `MAX_FILE_SIZE_MB` | Upload limit |
| `UPLOAD_DIRECTORY` | Directory for stored files |

## Planned installation sequence

1. Copy `.env.example` to `.env` and fill in local values.
2. Create the MySQL database.
3. From `backend/`, create a virtual environment, install `requirements.txt`, and run `alembic upgrade head`.
4. Start FastAPI with `uvicorn app.main:app --reload --port 8000`.
5. Confirm Ollama is running and the chosen models are pulled. Phase 3. The API does not call Ollama yet.
6. Install frontend dependencies and start Next.js. Phase 7.

From the repository root, `docker compose up -d` starts MySQL 8 on host port 3307 and creates `local_ai_assistant`. Copy `.env.example` to `.env` first so Compose can read `MYSQL_ROOT_PASSWORD`. Ollama stays on the host. See [deployment.md](deployment.md).

## Repository layout after clone

`frontend/` is still a placeholder. `backend/` is the FastAPI application. `storage/uploads/` is empty and is the future upload directory. Uploaded bytes will be gitignored.
