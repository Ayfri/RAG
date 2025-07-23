# RAG API

This folder contains a small **FastAPI** application exposing a minimal, file-based Retrieval-Augmented Generation (RAG) service built on **[LlamaIndex](https://github.com/run-llama/llama_index)**.

## Folder layout

```
api/
├── main.py                # FastAPI entry-point
├── services/
│   └── rag_router.py     # RAG API routes
├── src/
│   ├── config.py         # Configuration management
│   └── rag.py            # RAGService implementation
├── requirements.txt      # Python dependencies
└── README.md             # This file
```

Additional runtime data live outside the Git index:

```
data/
├── files/<rag-name>/    # Source documents (any text-based format supported by LlamaIndex)
└── indices/<rag-name>/  # Persisted vector index & metadata (auto-generated)
```

The `data/` directory is listed in the project-level **.gitignore** so you never commit large embeddings.

## Installation

```powershell
# Create a virtual environment (recommended)
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt
```

> 📦  **Tip**: When iterating locally you can run `uvicorn api.main:app --reload` to start the server with auto-reload.

## Environment variables

Create a `.env` file at the repository root containing the necessary environment variables, including your OpenAI key. For example:

```
OPENAI_API_KEY=sk-...
API_HOST=0.0.0.0
API_PORT=8000
API_DEBUG=False
```

The `api/src/config.py` module automatically loads these variables on application startup.

## Endpoints

### RAG Management

| Method | Path | Description |
| ------ | ---- | ----------- |
| `GET`  | `/rag` | List every existing RAG index. |
| `POST` | `/rag/{rag_name}` | Build (or rebuild) an index from documents in `data/files/{rag_name}/`. |
| `DELETE` | `/rag/{rag_name}` | Delete a RAG index and all its associated files. |

### Query Operations

| Method | Path | Description |
| ------ | ---- | ----------- |
| `POST` | `/rag/{rag_name}/query` | Return the full answer for the provided query. |
| `POST` | `/rag/{rag_name}/stream` | Stream the answer token-by-token (plain text chunks). |

### Document Management

| Method | Path | Description |
| ------ | ---- | ----------- |
| `GET`  | `/rag/{rag_name}/files` | List all files in the RAG's document directory. |
| `POST` | `/rag/{rag_name}/files` | Upload a document to the RAG's files directory. |
| `DELETE` | `/rag/{rag_name}/files/{filename}` | Delete a specific file from the RAG's document directory. |

### Example

```powershell
# Upload a document
$file = Get-Item "document.pdf"
$form = @{
    file = $file
}
Invoke-RestMethod -Method Post -Uri 'http://localhost:8000/rag/my-docs/files' -Form $form

# Build an index from uploaded files
Invoke-RestMethod -Method Post -Uri 'http://localhost:8000/rag/my-docs'

# Ask a question and get the full answer
Invoke-RestMethod -Method Post -Uri 'http://localhost:8000/rag/my-docs/query' `
    -Body (@{ query = 'What is the project about?' } | ConvertTo-Json) `
    -ContentType 'application/json'

# Stream the answer (PowerShell)
$body = @{ query = 'Explain the main features.' } | ConvertTo-Json
$resp = Invoke-WebRequest -Method Post -Uri 'http://localhost:8000/rag/my-docs/stream' `
    -Body $body -ContentType 'application/json' -ResponseHeadersVariable rh -UseBasicParsing
$resp.Content

# List files in a RAG
Invoke-RestMethod -Method Get -Uri 'http://localhost:8000/rag/my-docs/files'

# Delete a file
Invoke-RestMethod -Method Delete -Uri 'http://localhost:8000/rag/my-docs/files/document.pdf'

# Delete entire RAG
Invoke-RestMethod -Method Delete -Uri 'http://localhost:8000/rag/my-docs'
```

## Notes

* Indices persist on disk; loading an existing RAG is instant.
* The current implementation is kept intentionally small (<200 lines per file). Feel free to extend `RAGService` with new capabilities (metadata, permissions, etc.).
* All code follows the repository coding guidelines (tabs, single quotes, english).
* API documentation is available at `http://localhost:8000/docs` when running the server.
