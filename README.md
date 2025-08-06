# RAG Application

A modern **Retrieval-Augmented Generation (RAG)** application with a **FastAPI** backend and **SvelteKit** frontend. Upload documents, create vector indices, and query your knowledge base with an elegant web interface.

**Created by [Ayfri](https://github.com/Ayfri)** - French student and developer passionate about experimenting with new technologies. Check out my other projects at [ayfri.com](https://ayfri.com).

## 🏗️ Architecture

- **Frontend**: SvelteKit + TypeScript + TailwindCSS
- **Backend**: FastAPI + LlamaIndex + OpenAI
- **Database**: File-based vector storage
- **Configuration**: Per-RAG JSON configuration files

## 📁 Project Structure

```
RAG/
├── api/                    # FastAPI backend
│   ├── data/              # Runtime data (not in Git)
│   │   ├── configs/<rag-name>.json # Per-RAG configurations
│   │   ├── files/<rag-name>/  # Source documents
│   │   ├── indices/<rag-name>/ # Vector indices
│   │   └── resumes/<rag-name>.md # Auto-generated project summaries
│   ├── main.py            # API entry point
│   ├── services/
│   │   └── rag_router.py  # RAG API routes
│   ├── src/
│   │   ├── agent.py       # Agent and tools implementation
│   │   ├── config.py      # Configuration management
│   │   ├── openai_models.py # OpenAI models management
│   │   ├── rag.py         # RAGService implementation
│   │   ├── rag_config.py  # RAG configuration classes
│   │   └── types.py       # Shared TypedDict definitions
│   └── requirements.txt   # Python dependencies
├── package.json           # Frontend dependencies
├── README.md              # This file
└── src/                   # SvelteKit frontend
    ├── lib/
    │   ├── components/    # Reusable Svelte components
    │   ├── helpers/       # Utility functions
    │   └── stores/        # State management
    └── routes/
        ├── api/           # API proxy routes
        ├── +layout.svelte # App layout
        └── +page.svelte   # Main page
```

## 🚀 Quick Start

### Prerequisites

- **Node.js 22+** with **pnpm** (for local development)
- **Python 3.13+** (for local development)
- **Docker & Docker Compose** (for containerized deployment)
- **OpenAI API Key**

### 1. Environment Setup

Create a `.env` file at the project root:

```env
API_DEBUG=False
API_HOST=0.0.0.0
API_PORT=8000
OPENAI_API_KEY=sk-...
PORT=5173
PUBLIC_API_URL=http://localhost:8000
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

### 4. Docker Setup (Alternative)

For containerized deployment, use Docker Compose:

```powershell
# Option 1: Create .env file with your OpenAI API key
echo "OPENAI_API_KEY=sk-your-api-key-here" > .env

# Option 2: Set environment variable directly
$env:OPENAI_API_KEY="sk-your-api-key-here"

# Build and start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

**Optimized Builds**: The Docker setup includes intelligent caching:
- **Dependencies**: Cached separately from source code
- **Source code**: Rebuilds only when files change
- **Configuration**: Includes all necessary config files (`svelte.config.js`, `vite.config.ts`, `tsconfig.json`, `.npmrc`)
- **Production mode**: Frontend runs in production mode with `node build/index.js`

The application will be available at:
- **Frontend**: `http://localhost:5173`
- **Backend API**: `http://localhost:8000`
- **API Documentation**: `http://localhost:8000/docs`

**Data Persistence**: All RAG data is stored in a Docker volume (`rag_data`) and persists between container restarts.

## 🎯 Features

### 🤖 Agentic AI Workflow
- **Real-time tool usage**: Watch the AI agent use multiple tools as it works
- **Web search integration**: AI can search the internet for current information using OpenAI's web search
- **Document retrieval**: Smart search through your uploaded documents
- **File operations**: AI can read and explore files in your RAG directories
- **Progressive streaming**: See responses build up token-by-token with live tool indicators
- **Tool activity visualization**: Real-time display of web searches, document retrieval, and file operations

### 📊 RAG Management
- Create new RAG indices from uploaded documents
- List all available RAGs
- Delete RAGs and their associated data
- **Configure individual RAG settings** (OpenAI models, system prompts)

### ⚙️ RAG Configuration
- **Per-RAG model selection**: Choose different OpenAI chat models (GPT-4o, GPT-4o-mini, etc.)
- **Custom embedding models**: Select from various OpenAI embedding models
- **System prompt customization**: Define how the AI should respond for each RAG
- **AI-powered prompt generation**: Generate system prompts from descriptions using AI
- **Persistent settings**: Configuration stored in JSON files per RAG

### 📄 Document Management
- Upload files via drag-and-drop or file picker
- **Folder upload support**: Upload entire directories at once
- **Symbolic link support**: Link to external files and directories
- **URL management**: Add and remove website URLs as documents
- **Advanced file filtering**: Configure include/exclude patterns for specific folders and symlinks
- Support for PDF, TXT, DOCX, and Markdown files
- View and delete documents in each RAG
- **Manual reindexing**: Rebuild indices on demand
- Smart file listing with type indicators and symlink targets
- **Project summaries**: Auto-generated summaries for better context understanding

### 🔍 Intelligent Querying
- Ask questions about your documents
- **Real-time agentic streaming**: Watch the AI use tools in real-time
- **Tool activity visualization**: See web searches and document retrieval as they happen
- **Progressive response building**: Responses appear token-by-token with inline tool usage
- Clean, readable response formatting with tool activity indicators
- **Context-aware responses** based on per-RAG system prompts
- **File reading and exploration**: AI can read and list files in your document directories

### 💬 Chat Session Management
- **Persistent chat history**: Sessions saved locally via IndexedDB
- **Unlimited storage**: No server-side storage limitations
- **Session organization**: Create, rename, and delete chat sessions
- **RAG-specific sessions**: Separate chat history for each RAG
- **Automatic session creation**: New sessions created when starting conversations
- **Session browser**: View all past conversations with preview and timestamps
- **Message editing**: Edit and update chat messages
- **Session clearing**: Clear message history while keeping sessions

### 🎨 Modern UI
- Responsive design with TailwindCSS
- Dark/light theme support
- Intuitive file management
- Real-time loading states and error handling
- **Configuration modal** for easy RAG customization
- **System prompt generator** with AI assistance
- **File filter configuration** for advanced document management
- **Syntax highlighting** for code and markdown content
- **Notification system** for user feedback

## 🛠️ Technology Stack

### Backend
- **FastAPI 0.116+** - Modern Python web framework
- **LlamaIndex 0.12+** - RAG framework
- **OpenAI API** - Language model and embeddings
- **Uvicorn** - ASGI server
- **BeautifulSoup** - HTML parsing
- **html2text** - HTML to markdown conversion

### Frontend
- **SvelteKit 2.25+** - Full-stack framework
- **Svelte 5.36+** - Component framework with modern runes
- **TypeScript 5.8+** - Type-safe JavaScript
- **TailwindCSS 4.1+** - Utility-first CSS framework
- **Vite 7.0+** - Fast build tool
- **Lucide Svelte** - Beautiful icons
- **Shiki** - Syntax highlighting
- **Marked** - Markdown rendering
- **DOMPurify** - XSS protection

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
5. Use the **AI prompt generator** to create system prompts from descriptions
6. Save your configuration

**Available Models:**
- **Chat**: gpt-4.1, gpt-4.1-mini, gpt-4.1-nano, gpt-4o, o3, o3-mini, o4-mini
- **Embeddings**: text-embedding-3-large, text-embedding-3-small, text-embedding-ada-002

### Querying Documents

1. Select a RAG from the sidebar
2. Type your question in the query box (a new session will be created automatically if none exists)
3. The AI will stream its response in real-time, showing:
   - **Tool usage**: See when the AI searches the web or your documents
   - **Progressive responses**: Text appears as it's generated
   - **Live tool activity**: Inline indicators show search results and document retrieval
   - **File operations**: Watch the AI read and explore files
4. View the complete AI-generated answer with all sources and documents used

### Managing Chat Sessions

- **View sessions**: Click the "Sessions" button to see all your chat history
- **Create sessions**: New sessions are created automatically when you start chatting
- **Switch sessions**: Click on any session to resume that conversation
- **Rename sessions**: Click the edit icon to give sessions meaningful names
- **Delete sessions**: Remove sessions you no longer need
- **Edit messages**: Modify existing chat messages
- **Clear sessions**: Remove message history while keeping the session
- **Persistent storage**: All conversations are saved locally in your browser

### Managing Files

- **Add files**: Use the "Add File" button in the Documents section
- **Add folders**: Use the "Add Folder" button to upload entire directories
- **Create symlinks**: Use the "Link" button to reference external files/folders
- **Add URLs**: Use the "Add URL" button to include website content
- **Configure filters**: Set include/exclude patterns for specific folders and symlinks
- **Delete files**: Click the trash icon next to any file
- **Delete URLs**: Click the trash icon next to any URL
- **Manual reindex**: Use the "Reindex" button to rebuild the vector index
- **File types**: Files, directories, symbolic links, and URLs are clearly distinguished

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

### RAG Management
| Method   | Endpoint                | Description                                 |
|----------|-------------------------|---------------------------------------------|
| `GET`    | `/rag`                  | List all RAGs                               |
| `POST`   | `/rag/{name}`           | Create or rebuild a RAG                     |
| `DELETE` | `/rag/{name}`           | Delete a RAG                                |

### RAG Configuration
| Method   | Endpoint                        | Description                                 |
|----------|---------------------------------|---------------------------------------------|
| `GET`    | `/rag/{name}/config`            | Get RAG configuration                       |
| `PUT`    | `/rag/{name}/config`            | Update RAG configuration                    |
| `GET`    | `/rag/models`                   | Get available OpenAI models                 |
| `POST`   | `/rag/{name}/generate-prompt`   | Generate system prompt from description     |

### File & Folder Management
| Method   | Endpoint                              | Description                                 |
|----------|---------------------------------------|---------------------------------------------|
| `GET`    | `/rag/{name}/files`                   | List RAG files and directories              |
| `POST`   | `/rag/{name}/files`                   | Upload file or create folder                |
| `DELETE` | `/rag/{name}/files/{filename}`        | Delete file                                 |
| `POST`   | `/rag/{name}/symlink`                 | Create symbolic link                        |
| `POST`   | `/rag/{name}/reindex`                 | Manually reindex RAG                        |

### URL Management
| Method   | Endpoint                        | Description                                 |
|----------|---------------------------------|---------------------------------------------|
| `GET`    | `/rag/{name}/urls`              | List URLs                                   |
| `POST`   | `/rag/{name}/urls`              | Add URL                                     |
| `DELETE` | `/rag/{name}/urls`              | Remove URL                                  |

### Query
| Method   | Endpoint                        | Description                                 |
|----------|---------------------------------|---------------------------------------------|
| `POST`   | `/rag/{name}/stream`            | Stream agentic query response with real-time tool usage |

## 🔒 Security Notes

- API keys are loaded from environment variables
- File uploads are validated by type
- CORS is configured for local development
- Production deployments should use HTTPS
- XSS protection via DOMPurify

## 📦 Deployment

### Docker Compose (Recommended)

The easiest way to deploy the entire application:

```powershell
# Clone the repository
git clone <repository-url>
cd RAG

# Create environment file
echo "OPENAI_API_KEY=sk-your-api-key-here" > .env

# Start all services
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f
```

### Individual Services

#### Frontend (Cloudflare Pages)
```powershell
pnpm build
# Deploy ./build directory to Cloudflare Pages
```

#### Backend (Docker)
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
