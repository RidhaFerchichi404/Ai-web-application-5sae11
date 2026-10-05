# RAG

Status: Planned. Retrieval is not implemented. This document defines the pipeline Phase 6 will build inside FastAPI.

## Why RAG is needed

A local chat model does not know the user’s files. Putting an entire PDF into every prompt is unreliable: context windows are finite, cost in time grows with file size, and irrelevant pages crowd out the question. RAG keeps the file searchable and sends only the passages that match the question.

General knowledge remains in the model weights. Document knowledge comes from retrieved chunks. The prompt will label those chunks as document context so the model can answer from the file when the question is about the file, and can still answer ordinary questions when no documents are attached.

## Pipeline

```text
Document
   ↓
Text Extraction
   ↓
Cleaning
   ↓
Chunking
   ↓
Embedding
   ↓
Storage
   ↓
Question
   ↓
Question Embedding
   ↓
Similarity Search
   ↓
Relevant Chunks
   ↓
Prompt Context
   ↓
Ollama
   ↓
Answer
```

### Indexing

1. The document service will store the file as `UPLOADED`, then set `PROCESSING` when indexing starts. See [file-processing.md](file-processing.md).
2. Extraction will read text from PDF (PyMuPDF), DOCX (python-docx), TXT, or Markdown.
3. Cleaning will normalize whitespace and drop empty regions. It will not rewrite the author’s meaning.
4. Chunking will split the text into ordered pieces. Size and overlap will be configuration chosen in Phase 6, not guessed here as if they already shipped.
5. The Ollama embedding model will encode each chunk.
6. Rows will be inserted into `document_chunks`. The embedding payload will be written only through the vector search repository.
7. Status will become `READY`, or `FAILED` with `error_message` set.

### Query

1. The chat request will include one or more document ids, or a conversation that has attached documents.
2. The question will be embedded with the same embedding model used at index time.
3. The vector search repository will return the closest chunks.
4. Those chunks will be inserted into the prompt as a distinct context block, with document identity and chunk order.
5. Conversation history and the user question will stay outside that block.
6. Ollama will generate the answer. The answer will be stored as a normal assistant message.

If retrieval returns nothing useful, the prompt will still be sent, and the context block will say that no matching passages were found. The model will not be told to invent citations.

## Separating document context from model knowledge

The prompt will have three visible parts:

- Instructions that describe the assistant and tell it to prefer the document context for questions about the attached files.
- A context block that contains only retrieved chunk text.
- The conversation, ending with the current user question.

Retrieved text will not be mixed into the system instruction as if it were product policy. Stored messages will keep the user text and the assistant answer. Raw chunk dumps will not be copied into the message history on every turn. The next turn will retrieve again.

The model may still use general knowledge for wording and for questions that are not answered by the files. The instructions will tell it to say when the documents do not contain the answer.

## Vector boundary

Similarity search is a repository interface:

- Save embeddings for a document’s chunks.
- Search chunks for a query vector, optionally limited to document ids.
- Delete embeddings when a document is deleted.

The planned first body of that repository will read and write the `document_chunks.embedding` JSON column and rank rows in the FastAPI process. Chat, document, and API code will call the repository instead of querying that column. A later store can replace the repository without a rewrite of the pipeline above.

MySQL will remain the system of record for chunk text and document metadata either way.

## Out of scope

- Cloud embedding APIs
- PostgreSQL vector types
- A separate search cluster
- Agent loops that browse the web
- Automatic use of every stored document on every message. Retrieval will run for documents the user attached or selected.
