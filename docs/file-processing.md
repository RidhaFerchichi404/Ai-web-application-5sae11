# File processing

Status: Planned. No extractor runs in this repository yet.

The document service will accept a file, store it, record metadata, and move it through a small status machine. Text extraction and chunking are part of the same lifecycle and are specified with RAG in [rag.md](rag.md).

## Supported types

### PDF

PyMuPDF will extract text from PDF files. Scanned pages without a text layer are not a Phase 5 or Phase 6 guarantee. Pillow will be added only if a later extractor needs image handling. It is not required for text-layer PDFs.

### DOCX

python-docx will extract paragraph text from `.docx` files. Legacy `.doc` binaries are not planned.

### TXT

The Python standard library will read `.txt` files as UTF-8. Invalid encodings will fail the document with status `FAILED` rather than guessing silently in a way that corrupts the text. A later refinement may try a fallback encoding. That refinement is not part of the current plan.

### Markdown

The Python standard library will read `.md` files as UTF-8 text. Markdown will be indexed as text. The pipeline will not render it to HTML before chunking.

## Lifecycle

Success:

```text
UPLOADED
   ↓
PROCESSING
   ↓
READY
```

Failure:

```text
PROCESSING
   ↓
FAILED
```

| Status | Meaning |
| --- | --- |
| `UPLOADED` | Bytes are stored and the row exists. Extraction has not finished. |
| `PROCESSING` | Extraction, chunking, or embedding is in progress. |
| `READY` | Chunks are stored and the file can be used for questions. |
| `FAILED` | Processing stopped. `error_message` explains the failure in terms safe to show the user. |

Phase 5 delivers upload, validation, storage, metadata, deletion, and the status field. Phase 6 performs the transition into `READY` or `FAILED` after extraction and embedding. Until Phase 6, a stored file may remain `UPLOADED`. The API will not report `READY` unless chunks exist.

## Storage rules

- The configured directory is `UPLOAD_DIRECTORY` (example: `./storage/uploads`).
- The name on disk is a generated `stored_filename`, not the raw client path.
- `original_filename` is kept for display after the dangerous characters are stripped.
- Size must be within `MAX_FILE_SIZE_MB` (example: 25).
- The server will allow only the extensions and media types listed above.
- Deleting a document removes the row, its chunks, and the file on disk.
- Uploaded files are never executed, imported as code, or served as HTML.

## Processing steps

Once Phase 6 is active, `PROCESSING` covers:

1. Open the stored file from `stored_filename` inside the upload directory.
2. Extract text with the library for that type.
3. Clean whitespace.
4. Split into ordered chunks.
5. Embed each chunk through Ollama.
6. Insert `document_chunks` rows.
7. Set `READY` or `FAILED`.

If extraction returns no text, status will become `FAILED` with a message that the file had no readable text.

## Related documents

- [Database](database.md)
- [API](api.md)
- [RAG](rag.md)
- [Security](security.md)
