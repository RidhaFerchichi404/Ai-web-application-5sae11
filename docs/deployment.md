# Deployment

Status: MySQL 8 runs with Docker Compose. The API, the frontend, and Ollama are not containers. The full application is not a single deployable stack yet.

## Development processes

Local development will eventually run four pieces:

```text
Next.js
FastAPI
MySQL
Ollama
```

FastAPI is started from `backend/` on port 8000. Next.js will be started from this repository in Phase 7. MySQL 8.x may run on the host or, later, as a Compose service. Ollama should run directly on the host because GPU access is easier that way. A machine without a GPU will still use the host Ollama process. The application will use `OLLAMA_BASE_URL` and will not assume a particular device.

Local ports:

| Process | Example |
| --- | --- |
| Next.js | `http://localhost:3000` |
| FastAPI | `http://localhost:8000` |
| MySQL | `localhost:3306` |
| Ollama | `http://localhost:11434` |

FastAPI listens on port 8000. The Next.js port stays an example until Phase 7.

## Docker Compose

Compose currently runs MySQL 8 and creates the `local_ai_assistant` database. It publishes host port 3307 so it does not collide with another server on 3306. `MYSQL_ROOT_PASSWORD` comes from the gitignored `.env`. Ollama stays on the host. FastAPI and Next.js are not Compose services yet.

Guidelines for that future file:

- Do not put real passwords in the committed file. Use environment variables.
- Do not include a cloud model API.
- Prefer leaving Ollama on the host and pointing `OLLAMA_BASE_URL` at it.
- If Ollama is later containerized, that change needs a decision-log entry because GPU passthrough is a different setup.
- One backend service is enough. Do not split chat, RAG, and uploads into separate containers unless the architecture decision changes.

## Configuration

The runtime will read the variables in `.env.example`. Production-like runs will set `APP_ENV` explicitly and will use a MySQL account limited to the application database.

Uploaded files will live in `UPLOAD_DIRECTORY`. That directory must persist across restarts. If the backend later moves into a container, the upload directory must be a mounted volume. That mount is not defined yet.

## What Phase 1 does not do

- No images
- No Compose services
- No process manager
- No public hosting steps
- No TLS termination

Those topics wait until the application exists and a hosting target is chosen.
