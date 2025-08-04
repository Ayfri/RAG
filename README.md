# RAG Application

A modern **Retrieval-Augmented Generation (RAG)** application with a **FastAPI** backend and **SvelteKit** frontend. Upload documents, create vector indices, and query your knowledge base with an elegant web interface.

## 🏗️ Architecture

- **Frontend**: SvelteKit + TypeScript + TailwindCSS
- **Backend**: FastAPI + LlamaIndex + OpenAI
- **Database**: File-based vector storage
- **Configuration**: Per-RAG JSON configuration files

## 📁 Project Structure

```
RAG/
├── api/                    # FastAPI backend
│   ├── main.py            # API entry point
│   ├── services/
│   │   └── rag_router.py  # RAG API routes
│   ├── src/
│   │   ├── config.py      # Configuration management
│   │   └── rag.py         # RAGService implementation
│   └── requirements.txt   # Python dependencies
├── src/                   # SvelteKit frontend
│   ├── routes/
│   │   ├── api/           # API proxy routes
│   │   ├── +layout.svelte # App layout
│   │   └── +page.svelte   # Main page
│   └── lib/
│       └── components/    # Reusable Svelte components
├── data/                  # Runtime data (not in Git)
│   ├── files/<rag-name>/  # Source documents
│   ├── indices/<rag-name>/ # Vector indices
│   └── configs/<rag-name>.json # Per-RAG configurations
├── package.json           # Frontend dependencies
└── README.md              # This file
```

## 🚀 Quick Start

### Prerequisites

- **Node.js 18+** with **pnpm**
- **Python 3.12+**
- **OpenAI API Key**

### 1. Environment Setup

Create a `.env` file at the project root:

```env
OPENAI_API_KEY=sk-...
API_HOST=0.0.0.0
API_PORT=8000
API_DEBUG=False
```

### 2. Backend Setup

```powershell
# Create Python virtual environment
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# Install dependencies
pip install -r api/requirements.txt

# Start the FastAPI server
uvicorn api.main:app --reload
```

The API will be available at `http://localhost:8000` with documentation at `http://localhost:8000/docs`.

### 3. Frontend Setup

```powershell
# Install frontend dependencies
pnpm install

# Start the development server
pnpm dev
```

The web app will be available at `http://localhost:5173`.

## 🎯 Features

### 🤖 Agentic AI Workflow
- **Real-time tool usage**: Watch the AI agent use multiple tools as it works
- **Web search integration**: AI can search the internet for current information
- **Document retrieval**: Smart search through your uploaded documents
- **File operations**: AI can read and explore files in your RAG directories
- **Progressive streaming**: See responses build up token-by-token with live tool indicators

### 📊 RAG Management
- Create new RAG indices from uploaded documents
- List all available RAGs
- Delete RAGs and their associated data
- **Configure individual RAG settings** (OpenAI models, system prompts)

### ⚙️ RAG Configuration
- **Per-RAG model selection**: Choose different OpenAI chat models (GPT-4o, GPT-4o-mini, etc.)
- **Custom embedding models**: Select from various OpenAI embedding models
- **System prompt customization**: Define how the AI should respond for each RAG
- **Persistent settings**: Configuration stored in JSON files per RAG

### 📄 Document Management
- Upload files via drag-and-drop or file picker
- **Folder upload support**: Upload entire directories at once
- **Symbolic link support**: Link to external files and directories
- Support for PDF, TXT, DOCX, and Markdown files
- View and delete documents in each RAG
- **Manual reindexing**: Rebuild indices on demand
- Smart file listing with type indicators and symlink targets

### 🔍 Intelligent Querying
- Ask questions about your documents
- **Real-time agentic streaming**: Watch the AI use tools in real-time
- **Tool activity visualization**: See web searches and document retrieval as they happen
- **Progressive response building**: Responses appear token-by-token with inline tool usage
- Clean, readable response formatting with tool activity indicators
- **Context-aware responses** based on per-RAG system prompts

### 🎨 Modern UI
- Responsive design with TailwindCSS
- Dark/light theme support
- Intuitive file management
- Real-time loading states and error handling
- **Configuration modal** for easy RAG customization

## 🛠️ Technology Stack

### Frontend
- **SvelteKit 2.25+** - Full-stack framework
- **Svelte 5.36+** - Component framework with modern runes
- **TypeScript 5.8+** - Type-safe JavaScript
- **TailwindCSS 4.1+** - Utility-first CSS framework
- **Lucide Svelte** - Beautiful icons
- **Vite 7.0+** - Fast build tool

### Backend
- **FastAPI 0.116+** - Modern Python web framework
- **LlamaIndex 0.12+** - RAG framework
- **OpenAI API** - Language model and embeddings
- **Uvicorn** - ASGI server

## 📖 Usage

### Creating a RAG

1. Click **"New RAG"** in the top-right corner
2. Enter a unique name for your RAG
3. Upload one or more documents (PDF, TXT, DOCX, MD)
4. Wait for the vector index to be created

### Configuring a RAG

1. Click the **settings icon** (⚙️) next to any RAG in the sidebar
2. Choose your preferred **OpenAI chat model** (GPT-4o, GPT-4o-mini, etc.)
3. Select an **embedding model** for document processing
4. Customize the **system prompt** to define the AI's behavior
5. Save your configuration

**Available Models:**
- **Chat**: gpt-4o, gpt-4o-mini, gpt-4-turbo, gpt-4, gpt-3.5-turbo
- **Embeddings**: text-embedding-3-large, text-embedding-3-small, text-embedding-ada-002

### Querying Documents

1. Select a RAG from the sidebar
2. Type your question in the query box
3. The AI will stream its response in real-time, showing:
   - **Tool usage**: See when the AI searches the web or your documents
   - **Progressive responses**: Text appears as it's generated
   - **Live tool activity**: Inline indicators show search results and document retrieval
4. View the complete AI-generated answer with all sources and documents used

### Managing Files

- **Add files**: Use the "Add File" button in the Documents section
- **Add folders**: Use the "Add Folder" button to upload entire directories
- **Create symlinks**: Use the "Link" button to reference external files/folders
- **Delete files**: Click the trash icon next to any file
- **Manual reindex**: Use the "Reindex" button to rebuild the vector index
- **File types**: Files, directories, and symbolic links are clearly distinguished

## 🔧 Development

### Code Style
- **Indentation**: Tabs
- **Quotes**: Single quotes when possible
- **Semicolons**: Always use
- **Sorting**: Alphabetical order for imports, properties, functions

### Frontend Commands

```powershell
pnpm dev          # Start development server
pnpm build        # Build for production
pnpm preview      # Preview production build
pnpm check        # Type checking
pnpm check:watch  # Type checking in watch mode
```

### Backend Commands

```powershell
uvicorn api.main:app --reload  # Development server with auto-reload
```

## 🌐 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/rag` | List all RAGs |
| `POST` | `/rag/{name}` | Create/rebuild RAG |
| `DELETE` | `/rag/{name}` | Delete RAG |
| `GET` | `/rag/{name}/config` | Get RAG configuration |
| `PUT` | `/rag/{name}/config` | Update RAG configuration |
| `POST` | `/rag/{name}/stream` | Stream agentic query response with real-time tool usage |
| `GET` | `/rag/{name}/files` | List RAG files and directories |
| `POST` | `/rag/{name}/files` | Upload file |
| `POST` | `/rag/{name}/symlink` | Create symbolic link |
| `POST` | `/rag/{name}/reindex` | Manually reindex RAG |
| `DELETE` | `/rag/{name}/files/{filename}` | Delete file |

## 🔒 Security Notes

- API keys are loaded from environment variables
- File uploads are validated by type
- CORS is configured for local development
- Production deployments should use HTTPS

## 📦 Deployment

### Frontend (Cloudflare Pages)
```powershell
pnpm build
# Deploy ./build directory to Cloudflare Pages
```

### Backend (Docker)
```dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY api/ ./
RUN pip install -r requirements.txt
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

## 🤝 Contributing

1. Follow the established code style
2. Keep files under 200 lines when possible
3. Use descriptive commit messages
4. Test both frontend and backend changes

## 📄 License

See [LICENSE](./LICENSE) file for details.
