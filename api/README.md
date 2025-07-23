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
├── indices/<rag-name>/  # Persisted vector index & metadata (auto-generated)
└── configs/<rag-name>.json  # Per-RAG configuration files (auto-generated)
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
| `POST` | `/rag/{rag_name}` | Build (or rebuild) an index from documents in `data/files/{rag_name}/`. Can be called even if the directory is empty. |
| `DELETE` | `/rag/{rag_name}` | Delete a RAG index and all its associated files. |

### RAG Configuration

| Method | Path | Description |
| ------ | ---- | ----------- |
| `GET`  | `/rag/{rag_name}/config` | Get the configuration for a specific RAG (chat model, embedding model, system prompt). |
| `PUT` | `/rag/{rag_name}/config` | Update the configuration for a specific RAG. |

### Query Operations

| Method | Path | Description |
| ------ | ---- | ----------- |
| `POST` | `/rag/{rag_name}/query` | Return the full answer for the provided query. |
| `POST` | `/rag/{rag_name}/stream` | Stream the answer token-by-token (plain text chunks). |

### Document Management

| Method | Path | Description |
| ------ | ---- | ----------- |
| `GET`  | `/rag/{rag_name}/files` | List all files and directories in the RAG's document directory. Returns detailed info including type and symlink targets. |
| `POST` | `/rag/{rag_name}/files` | Upload a document to the RAG's files directory. |
| `POST` | `/rag/{rag_name}/symlink` | Create a symbolic link to an external file or directory. |
| `POST` | `/rag/{rag_name}/reindex` | Manually reindex the RAG from all current files and symlinks. |
| `DELETE` | `/rag/{rag_name}/files/{filename}` | Delete a specific file from the RAG's document directory. |

## Configuration

Each RAG instance can be individually configured with its own settings stored in `data/configs/{rag_name}.json`. The configuration includes:

- **`chat_model`**: OpenAI model to use for generating responses (default: `gpt-4o-mini`)
- **`embedding_model`**: OpenAI model to use for creating embeddings (default: `text-embedding-3-large`)
- **`system_prompt`**: Custom system prompt to guide the model's responses

### Available Models

**Chat Models:**
- `gpt-4o`
- `gpt-4o-mini` (default)
- `gpt-4-turbo`
- `gpt-4`
- `gpt-3.5-turbo`

**Embedding Models:**
- `text-embedding-3-large` (default)
- `text-embedding-3-small`
- `text-embedding-ada-002`

### Configuration Example

```json
{
  "chat_model": "gpt-4o-mini",
  "embedding_model": "text-embedding-3-large",
  "system_prompt": "You are a helpful assistant that answers questions based on the provided context. Be concise and accurate."
}
```

### Example

```powershell
# Upload a document
$file = Get-Item "document.pdf"
$form = @{
    file = $file
}
Invoke-RestMethod -Method Post -Uri 'http://localhost:8000/rag/my-docs/files' -Form $form

# Create a symbolic link to external documents
$symlinkData = @{
    target_path = 'C:\Documents\MyProject'
    link_name = 'project-docs'
} | ConvertTo-Json
Invoke-RestMethod -Method Post -Uri 'http://localhost:8000/rag/my-docs/symlink' `
    -Body $symlinkData -ContentType 'application/json'

# Build an index from uploaded files and symlinks
Invoke-RestMethod -Method Post -Uri 'http://localhost:8000/rag/my-docs'

# Manually reindex to include new files
Invoke-RestMethod -Method Post -Uri 'http://localhost:8000/rag/my-docs/reindex'

# Get current configuration
Invoke-RestMethod -Method Get -Uri 'http://localhost:8000/rag/my-docs/config'

# Update configuration
$config = @{
    chat_model = 'gpt-4o'
    embedding_model = 'text-embedding-3-large'
    system_prompt = 'You are an expert analyst. Provide detailed insights based on the documents.'
} | ConvertTo-Json
Invoke-RestMethod -Method Put -Uri 'http://localhost:8000/rag/my-docs/config' `
    -Body $config -ContentType 'application/json'

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
* Each RAG has its own configuration file that persists its model settings and system prompt.
* Configuration changes are applied immediately to new queries and index operations.
* The current implementation is kept intentionally small (<200 lines per file). Feel free to extend `RAGService` with new capabilities (metadata, permissions, etc.).
* All code follows the repository coding guidelines (tabs, single quotes, english).
* API documentation is available at `http://localhost:8000/docs` when running the server.
