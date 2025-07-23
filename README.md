# RAG Application

A modern **Retrieval-Augmented Generation (RAG)** application with a **FastAPI** backend and **SvelteKit** frontend. Upload documents, create vector indices, and query your knowledge base with an elegant web interface.

## 🏗️ Architecture

- **Frontend**: SvelteKit + TypeScript + TailwindCSS
- **Backend**: FastAPI + LlamaIndex + OpenAI
- **Database**: File-based vector storage

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
│   └── indices/<rag-name>/ # Vector indices
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

### 📊 RAG Management
- Create new RAG indices from uploaded documents
- List all available RAGs
- Delete RAGs and their associated data

### 📄 Document Management
- Upload files via drag-and-drop or file picker
- Support for PDF, TXT, DOCX, and Markdown files
- View and delete documents in each RAG
- Automatic index rebuilding after file changes

### 🔍 Intelligent Querying
- Ask questions about your documents
- Real-time streaming responses
- Standard and streaming query modes
- Clean, readable response formatting

### 🎨 Modern UI
- Responsive design with TailwindCSS
- Dark/light theme support
- Intuitive file management
- Real-time loading states and error handling

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

### Querying Documents

1. Select a RAG from the sidebar
2. Type your question in the query box
3. Choose **"Ask"** for a complete response or **"Stream"** for real-time output
4. View the AI-generated answer based on your documents

### Managing Files

- **Add files**: Use the "Add File" button in the Documents section
- **Delete files**: Click the trash icon next to any file
- **Auto-rebuild**: Indices automatically update when files change

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
| `POST` | `/rag/{name}/query` | Query RAG |
| `POST` | `/rag/{name}/stream` | Stream query response |
| `GET` | `/rag/{name}/files` | List RAG files |
| `POST` | `/rag/{name}/files` | Upload file |
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
