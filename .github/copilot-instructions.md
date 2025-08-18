### Quick context

This repository is a Retrieval-Augmented Generation (RAG) web app with a
FastAPI backend (Python) and a SvelteKit frontend. Backend stores RAG data
on-disk under `api/data/` (files, indices, configs, resumes). OpenAI is used
for chat and embeddings (API key via `OPENAI_API_KEY`).

Key paths:

- Backend entry: `api/main.py` (FastAPI)
- Router: `api/services/rag_router.py` (endpoints + streaming)
- Core RAG logic: `api/src/rag.py` (indexing, persistence, core operations)
- Document management: `api/src/document_manager.py` (file/URL operations)
- Agent/tools: `api/src/agent.py` (tools: `rag_tool`, `search`, `read_file_tool`, `list_files_tool`)
- Utilities: `api/src/utils.py` (general-purpose utility functions)
- Config: `api/src/config.py` and `api/src/rag_config.py`

### Role for the AI coding agent

Be a conservative, testable code contributor. Priorities:

- Keep file-based storage behavior intact (do not change data layout under `api/data`).
- Preserve streaming/event shapes (see `api/src/types.py`) used by the frontend.
- Avoid changing environment-loading in `api/src/config.py`; rely on `OPENAI_API_KEY`.

When editing code, run the backend locally using `uvicorn api.main:app --reload` and
validate the streaming endpoint `POST /rag/{name}/stream` returns newline-delimited JSON
events matching `StreamEvent` shapes in `api/src/types.py`.

### Role and Objective

- Ensure all code, examples, and configurations align with current best practices as of mid-2025, following project-specific conventions and leveraging modern language and framework features.

### Process Checklist

- Identify the change goal and its scope.
- Inspect relevant files for examples and existing patterns.
- Make minimal, testable edits following repository conventions.
- Run quick verification (build, smoke or unit tests) and iterate.
- Prepare concise PR notes and verification steps for reviewers.

### Instructions for the agent (project-specific rules)

- When unsure about a feature, briefly search and read the codebase, focusing on examples and tests for that feature. Limit searches to relevant files only.
- Before using any significant tool or script, state its purpose and minimal required inputs in one line.
- After each tool call or substantive code edit, validate the result in 1–2 lines and proceed or self-correct if validation fails.
- Sort properties, variables, and functions alphabetically by name for consistency.
- Keep files concise; prefer files under 200 lines. Split large files into multiple components, functions, or modules as needed.
- Use tab indentation, include semicolons, minimize use of parentheses, use single quotes where possible, and consistently quote all property keys.
- Prefer `pnpm` for all package and script commands.
- Develop on Windows 11 with PowerShell 7.
- All code and comments must be in English.

IMPORTANT runtime rule:

- Never start, stop, or restart the FastAPI/uvicorn server yourself. The developer runs the backend; only provide commands when explicitly asked. Assume the server is already running during verification and use logs/output shared by the user.

#### JavaScript/TypeScript

- Prefer single quotes when possible; use double quotes if the string contains a single quote.
- Use modern shorter syntaxes (e.g., `a?.()`, `a ??= []`)

#### Svelte

- Avoid using `class:` directive with class names containing '/'.
- Do not use event dispatchers; use `onEvent` props instead.
- Never import from `$lib/server` in a Svelte component; use `+page.server.ts` for server logic.
- Do not use TypeScript syntax within the HTML section of Svelte files except when using Svelte 5.
- Use `$app/state` instead of `$app/stores`; state values are plain values.

#### Python

- Do not use `Optional`, `List`, or `Dict`. Use `|`, `list`, and `dict` syntax (e.g., `dict[str, list[int]]`)
- Use Python 3.12 features and syntax.

### Verbosity and stop conditions

- Summarize instructions concisely.
- Use high verbosity in code with readable names, comments, and direct control flow.
- Stop when output and code meet all rules and conventions; escalate if insufficient context.

### Architecture notes the agent must know

- Data flow: documents live in `api/data/files/<rag>/` -> `create_rag` builds a
  `VectorStoreIndex` persisted to `api/data/indices/<rag>/`. `get_agent` uses
  `load_index` to serve retrievals.
- Agent workflow: `RAGService.async_agent_stream` iterates an agent handler and
  yields token, sources, documents, read_file, list_files, chat_history, final events.
  The frontend expects token streaming for progressive display.
- Tools: the FunctionAgent tools live in `api/src/agent.py`. `read_file_tool` and
  `list_files_tool` operate relative to `data/files` — keep their signatures stable.
- Document management: `RAGDocumentManager` in `api/src/document_manager.py` handles
  all file operations, URL management, and document storage. `RAGService` delegates
  document operations to this component for better separation of concerns.
- Utilities: Common functions like URL fetching, file filtering, and directory stats
  are centralized in `api/src/utils.py` for reusability across modules.

### Conventions & patterns

- File-based RAGs: each RAG has files, index directory, and a JSON config at
  `api/data/configs/<rag>.json`. New RAGs are created via `POST /rag/{name}`.
- Filters: `file_filters` in `RAGConfig` map folder/symlink names to include/exclude
  globs. Indexing code applies these via `SimpleDirectoryReader` + `filter_documents_by_include_globs`.
- Streams: server sends newline-separated JSON events from `/rag/{name}/stream`.
  Keep event `type` strings and payload keys unchanged.
- Modular design: `RAGService` focuses on core RAG operations, `RAGDocumentManager`
  handles document/file operations, and `utils.py` provides shared utilities.

### Developer workflows & commands

- Backend dev server (PowerShell):

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r api/requirements.txt
uvicorn api.main:app --reload
```

- Frontend dev (repo root):

```powershell
pnpm install
pnpm dev
```

- Docker-compose (all services):

```powershell
# create .env with OPENAI_API_KEY or set env var
docker-compose up -d --build
docker-compose logs -f
```

### Tests & verification to run after changes

- Smoke: start backend and call `GET /` -> expect JSON {status: 'healthy'}.
- Integration: create a RAG folder under `api/data/files/<test-rag>/` with a
  small markdown file, then call `POST /rag/{test-rag}` and verify `api/data/indices/{test-rag}` is created and `api/data/resumes/{test-rag}.md` exists.
- Streaming: use `POST /rag/{test-rag}/stream` with a JSON body {"query":"..."}
  and expect newline-delimited JSON events whose `type` matches `api/src/types.py`.

### Safe-change checklist (use before committing)

1. Does change preserve on-disk layout under `api/data/`? (files, indices, configs)
2. Are `StreamEvent` types, keys and token streaming logic unmodified? (frontend depends on it)
3. Are OpenAI model names and API-key usage unchanged in `api/src/config.py` and `api/src/rag.py`? If modifying, update README and `.env` instructions.
4. Run backend smoke tests above.

### Examples to reference in PRs

- If adding a new tool for the agent, mirror signatures in `api/src/agent.py` and
  emit compatible events from `RAGService.async_agent_stream` (see `ToolCallResult` handling).
- If changing filters behavior, update `RAGConfig.get_file_filters_for_path` and
  the `filter_documents_by_include_globs` helper in `api/src/utils.py`.
- If adding document management features, implement them in `RAGDocumentManager` and
  expose through `RAGService` delegation for backward compatibility.

### Where to look for more context

- `README.md` (project overview & run commands)
- `api/services/rag_router.py` (HTTP API & validation)
- `api/src/rag.py` (indexing, persistence, core RAG operations, streaming)
- `api/src/document_manager.py` (document/file/URL management)
- `api/src/agent.py` (agent tools & system prompts)
- `api/src/utils.py` (shared utility functions)

Please apply changes as a single small PR with focused scope. Ask if any runtime
details are not discoverable from the repo (CI commands, private envs).
