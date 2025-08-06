# RAG API

This folder contains a small **FastAPI** application exposing a minimal, file-based Retrieval-Augmented Generation (RAG) service built on **[LlamaIndex](https://github.com/run-llama/llama_index)**.

## Folder layout

```
api/
├── data/                   # Runtime data (not in Git)
│   ├── configs/<rag-name>.json # Per-RAG configuration files (auto-generated)
│   ├── files/<rag-name>/       # Source documents (any text-based format supported by LlamaIndex)
│   ├── indices/<rag-name>/     # Persisted vector index & metadata (auto-generated)
│   └── resumes/<rag-name>.md   # Auto-generated project summaries (auto-generated)
├── main.py                # FastAPI entry-point
├── services/
│   └── rag_router.py     # RAG API routes
├── src/
│   ├── agent.py          # Agent and tools implementation
│   ├── config.py         # Configuration management
│   ├── openai_models.py  # OpenAI models management
│   ├── rag.py            # RAGService implementation
│   ├── rag_config.py     # RAG configuration classes
│   └── types.py          # Shared TypedDict definitions
├── requirements.txt      # Python dependencies
└── README.md             # This file
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
API_DEBUG=False
API_HOST=0.0.0.0
API_PORT=8000
OPENAI_API_KEY=sk-...
```

The `api/src/config.py` module automatically loads these variables on application startup.

## Endpoints

### RAG Management

| Method | Path | Description |
| ------ | ---- | ----------- |
| `DELETE` | `/rag/{rag_name}` | Delete a RAG index and all its associated files. |
| `GET`  | `/rag` | List every existing RAG index. |
| `POST` | `/rag/{rag_name}` | Build (or rebuild) an index from documents in `data/files/{rag_name}/`. Can be called even if the directory is empty. |

### RAG Configuration

| Method | Path | Description |
| ------ | ---- | ----------- |
| `GET`  | `/rag/{rag_name}/config` | Get the configuration for a specific RAG (chat model, embedding model, system prompt). |
| `GET`  | `/rag/models` | Get all available OpenAI models for chat and embeddings. |
| `POST` | `/rag/{rag_name}/generate-prompt` | Generate a system prompt from a description using AI. |
| `PUT` | `/rag/{rag_name}/config` | Update the configuration for a specific RAG. |

### Query Operations

| Method | Path | Description |
| ------ | ---- | ----------- |
| `POST` | `/rag/{rag_name}/stream` | Stream the answer in real-time with agentic workflow (tokens, sources, documents, and metadata). |

### Document Management

| Method | Path | Description |
| ------ | ---- | ----------- |
| `DELETE` | `/rag/{rag_name}/files/{filename}` | Delete a specific file from the RAG's document directory. |
| `GET`  | `/rag/{rag_name}/files` | List all files and directories in the RAG's document directory. Returns detailed info including type and symlink targets. |
| `POST` | `/rag/{rag_name}/files` | Upload a document to the RAG's files directory or create a folder with file filters. |
| `POST` | `/rag/{rag_name}/reindex` | Manually reindex the RAG from all current files and symlinks. |
| `POST` | `/rag/{rag_name}/symlink` | Create a symbolic link to an external file or directory with file filters. |

### URL Management

| Method | Path | Description |
| ------ | ---- | ----------- |
| `DELETE` | `/rag/{rag_name}/urls` | Remove a URL document from the RAG. |
| `GET` | `/rag/{rag_name}/urls` | List all URLs in the RAG. |
| `POST` | `/rag/{rag_name}/urls` | Add a URL as a document to the RAG. |

## Features

### Advanced File Management
- **File filtering**: Advanced glob pattern support for including/excluding files
- **Folder creation**: Create empty folders for organization
- **Smart file listing**: Detailed metadata including file types, sizes, and symlink targets
- **Symbolic links**: Link to external files and directories
- **URL integration**: Add web pages as documents with HTML parsing

### Agent-Based Architecture
Each RAG uses an intelligent agent with access to multiple tools:
- **File operations**: Read and list files in the document directory
- **Local RAG search**: Semantic search through indexed documents
- **Project summaries**: Auto-generated summaries for better context understanding
- **Web search**: Real-time web search via OpenAI's web search API

### Real-Time Streaming
The RAG system provides **real-time streaming** with an agentic workflow that includes:
- **Immediate token streaming**: Text appears as the agent generates it
- **Live metadata updates**: Sources, documents, and chat history stream as they're found
- **Progressive enhancement**: Users see results instantly, with additional context arriving progressively
- **Tool activity visualization**: Real-time display of web searches, document retrieval, and file operations

### Type Safety
The codebase uses comprehensive TypeScript-style typing:
- **Pattern matching** for efficient event processing
- **Shared type definitions** in `src/types.py`
- **Strict typing** for all streaming events and data structures

## Configuration

Each RAG instance can be individually configured with its own settings stored in `data/configs/{rag_name}.json`. The configuration includes:

- **`chat_model`**: OpenAI model to use for generating responses (default: `gpt-4o-mini`)
- **`embedding_model`**: OpenAI model to use for creating embeddings (default: `text-embedding-3-large`)
- **`system_prompt`**: Custom system prompt to guide the model's responses

- **`file_filters`**: (Optional) A dictionary specifying include and exclude glob patterns for specific folders or symlinks within the RAG's document directory.
  - The keys of this dictionary should be the names of the folders or symlinks (e.g., `"my-folder"`, `"my-symlink"`).
  - A special key `"_base"` can be used to apply filters directly to files in the root of the RAG's `data/files/{rag_name}/` directory.
  - Each value is an object with two optional keys:
    - **`include`**: A list of glob patterns for files to include (default: `["**/*"]`). Files must match at least one include pattern to be processed.
    - **`exclude`**: A list of glob patterns for files to exclude (default: `[]`). Files matching any exclude pattern will be ignored.

### Available Models

**Chat Models:**
- `gpt-4.1`
- `gpt-4.1-mini`
- `gpt-4.1-nano`
- `gpt-4o`
- `o3`
- `o3-mini`
- `o4-mini`

**Embedding Models:**
- `text-embedding-3-large` (default)
- `text-embedding-3-small`
- `text-embedding-ada-002`

### Configuration Example

```json
{
  "chat_model": "gpt-4.1-mini",
  "embedding_model": "text-embedding-3-large",
  "system_prompt": "You are a helpful assistant that answers questions based on the provided context. Be concise and accurate.",
  "file_filters": {
    "my-project-docs": {
      "include": ["**/*.py"],
      "exclude": ["venv/**"]
    },
    "old-docs-symlink": {
      "exclude": ["*.bak"]
    }
  }
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

# Generate a system prompt from description
$promptData = @{
    description = 'I want the AI to be an expert in web development with React and Node.js'
} | ConvertTo-Json
Invoke-RestMethod -Method Post -Uri 'http://localhost:8000/rag/my-docs/generate-prompt' `
    -Body $promptData -ContentType 'application/json'

# Add a URL as a document
$urlData = @{
    url = 'https://example.com/documentation'
} | ConvertTo-Json
Invoke-RestMethod -Method Post -Uri 'http://localhost:8000/rag/my-docs/urls' `
    -Body $urlData -ContentType 'application/json'

# List URLs in the RAG
Invoke-RestMethod -Method Get -Uri 'http://localhost:8000/rag/my-docs/urls'

# Stream the answer with real-time agent workflow (PowerShell)
$body = @{
    query = 'What is the project about?'
    history = @(
        @{ role = 'user'; content = 'Previous question' },
        @{ role = 'assistant'; content = 'Previous answer' }
    )
} | ConvertTo-Json -Depth 3
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

### Streaming Response Format

The streaming endpoint returns a mixed-format response:
- **Text tokens** are streamed directly as they're generated
- **Metadata events** are JSON objects with special markers:
  ```
  token1token2token3...
  ---sources---
  {"content": "...", "urls": [...]}

  ---documents---
  [{"content": "...", "source": "..."}]

  ---chat_history---
  {"content": "...", "role": "assistant"}

  ---final---
  {"sources": [...], "documents": [...], "chat_history": [...]}
  ```

## Notes

* **Real-time streaming**: All responses stream immediately with progressive enhancement
* **Agent-based**: Each query uses an intelligent agent with multiple tools (RAG, web search, file ops)
* **Type safety**: Comprehensive typing with shared TypedDict definitions in `src/types.py`
* **Auto-summaries**: Project summaries are auto-generated and stored in `data/resumes/`
* **Persistent indices**: Vector indices persist on disk; loading an existing RAG is instant
* **Per-RAG configuration**: Each RAG has its own config file with model settings and system prompt
* **File filtering**: Advanced glob pattern support for including/excluding files during indexing
* **URL integration**: Web pages can be added as documents with HTML parsing and markdown conversion
* **Symbolic links**: Link to external files and directories with filtering support
* **Configuration changes** are applied immediately to new queries and index operations
* All code follows the repository coding guidelines (tabs, single quotes, english)
* API documentation is available at `http://localhost:8000/docs` when running the server
