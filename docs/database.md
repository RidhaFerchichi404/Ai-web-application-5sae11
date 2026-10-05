# Database

Status: Implemented as SQLAlchemy models and `backend/alembic/versions/0001_initial_schema.py`. Applying the migration requires a MySQL 8.x database created by the operator. No rows are seeded.

The database name in the example configuration is `local_ai_assistant`. The URL scheme will be `mysql+pymysql`.

PostgreSQL is not part of this design. Embeddings will not use a PostgreSQL vector type. How similarity search reads embeddings is isolated in the vector search repository. See [decisions/README.md](decisions/README.md), Decision 005.

Authentication is not scheduled in Phases 1–10. The `users` table still exists so conversations and documents have an owner when a later login decision is made. Until then, the backend may use a single local user row. That behavior is not implemented.

## Relationships

```text
users
  ├── conversations
  │     └── messages
  └── documents
        └── document_chunks
```

A document may also point at a conversation when the file was attached in that chat. The documents library can list files without requiring that link.

## users

Purpose: identify the owner of conversations and documents.

| Column | Type | Notes |
| --- | --- | --- |
| `id` | `BIGINT UNSIGNED` | Primary key |
| `display_name` | `VARCHAR(255)` | Required |
| `created_at` | `DATETIME(6)` | Required |
| `updated_at` | `DATETIME(6)` | Required |

Relationships: one user has many conversations and many documents.

Constraints:

- Primary key on `id`.
- `display_name` not null.

Indexes:

- Primary key only. Email and password columns are intentionally absent until an authentication decision exists.

## conversations

Purpose: one chat thread, including its title and the chat model last associated with it.

| Column | Type | Notes |
| --- | --- | --- |
| `id` | `BIGINT UNSIGNED` | Primary key |
| `user_id` | `BIGINT UNSIGNED` | Foreign key to `users.id` |
| `title` | `VARCHAR(255)` | Required. The UI will allow rename |
| `chat_model` | `VARCHAR(255)` | Nullable snapshot of the Ollama model name |
| `created_at` | `DATETIME(6)` | Required |
| `updated_at` | `DATETIME(6)` | Required. Changes when the thread is renamed or a message is added |

Relationships: belongs to one user. Has many messages. May be referenced by documents attached in that thread.

Constraints:

- Primary key on `id`.
- `user_id` not null.
- Foreign key to `users.id`.
- `title` not null.

Indexes:

- Primary key.
- Index on `user_id`, `updated_at` for the sidebar history.
- Index on `title` is optional and can wait until search needs it. Phase 4 can start with application-side filtering if the history stays small.

## messages

Purpose: one turn in a conversation.

| Column | Type | Notes |
| --- | --- | --- |
| `id` | `BIGINT UNSIGNED` | Primary key |
| `conversation_id` | `BIGINT UNSIGNED` | Foreign key to `conversations.id` |
| `role` | `VARCHAR(32)` | `user`, `assistant`, or `system` |
| `content` | `LONGTEXT` | Required message body |
| `created_at` | `DATETIME(6)` | Required |

Relationships: belongs to one conversation.

Constraints:

- Primary key on `id`.
- `conversation_id` not null.
- Foreign key to `conversations.id` with delete cascade so removing a conversation removes its messages.
- `role` restricted to `user`, `assistant`, and `system`.
- `content` not null.

Indexes:

- Primary key.
- Index on `conversation_id`, `created_at` for history in order.

## documents

Purpose: metadata for one uploaded file. Bytes live on disk under `UPLOAD_DIRECTORY`, not in this table.

| Column | Type | Notes |
| --- | --- | --- |
| `id` | `BIGINT UNSIGNED` | Primary key |
| `user_id` | `BIGINT UNSIGNED` | Foreign key to `users.id` |
| `conversation_id` | `BIGINT UNSIGNED` | Nullable foreign key to `conversations.id` |
| `original_filename` | `VARCHAR(255)` | Name as provided, stored for display after sanitization checks |
| `stored_filename` | `VARCHAR(255)` | Unique name used on disk. Not a user-controlled path |
| `media_type` | `VARCHAR(127)` | Detected type, for example `application/pdf` |
| `extension` | `VARCHAR(16)` | `pdf`, `docx`, `txt`, or `md` |
| `size_bytes` | `BIGINT UNSIGNED` | Size after upload |
| `status` | `VARCHAR(32)` | `UPLOADED`, `PROCESSING`, `READY`, or `FAILED` |
| `error_message` | `TEXT` | Nullable. Set when status is `FAILED` |
| `created_at` | `DATETIME(6)` | Upload time |
| `updated_at` | `DATETIME(6)` | Required |

Relationships: belongs to one user. Optionally belongs to one conversation. Has many chunks.

Constraints:

- Primary key on `id`.
- Foreign key to `users.id`.
- Nullable foreign key to `conversations.id`. Deleting a conversation will not delete the file row. `conversation_id` will be set null.
- `stored_filename` unique.
- `status` restricted to the four values above.
- `size_bytes` greater than 0.

Indexes:

- Primary key.
- Unique index on `stored_filename`.
- Index on `user_id`, `created_at` for the document list.
- Index on `status` for processing work.

## document_chunks

Purpose: one piece of extracted text and, once Phase 6 runs, its embedding payload.

| Column | Type | Notes |
| --- | --- | --- |
| `id` | `BIGINT UNSIGNED` | Primary key |
| `document_id` | `BIGINT UNSIGNED` | Foreign key to `documents.id` |
| `chunk_index` | `INT UNSIGNED` | Order within the document, starting at 0 |
| `content` | `LONGTEXT` | Chunk text used in prompts |
| `embedding` | `JSON` | Nullable array of numbers. Read and written only by the vector search repository |
| `created_at` | `DATETIME(6)` | Required |

Relationships: belongs to one document.

Constraints:

- Primary key on `id`.
- Foreign key to `documents.id` with delete cascade.
- Unique pair `document_id`, `chunk_index`.
- `content` not null.

Indexes:

- Primary key.
- Unique index on `document_id`, `chunk_index`.

Application code outside the vector repository will not filter or sort on `embedding`. Replacing the store later can move that column, or stop using it, without changing conversation or document queries.

## Migration policy

The initial migration matches this document. If the schema changes, update this file and the decision log first, then add a new migration. Do not change the tables by hand in a way that drifts from this spec.
