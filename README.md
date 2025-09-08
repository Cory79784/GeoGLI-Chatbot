# UNCCD GeoGLI Chatbot

A minimal, runnable chatbot for UNCCD Global Land Indicator queries built with **FastAPI + LangGraph** backend and a green floating web widget frontend.

## 🏗️ Architecture Overview

This project follows a **frontend-backend separation architecture** for better development, deployment, and scalability:

- **Backend**: Python FastAPI application with RAG system (port 8000)
- **Frontend**: Static HTML/JS/CSS with green floating chat widget (any port)
- **Communication**: RESTful API with Server-Sent Events (SSE) for real-time streaming

### 🎯 Architecture Benefits

**🔄 Separation of Concerns:**
- Backend handles AI/ML processing, data storage, and business logic
- Frontend focuses on user interface and user experience
- Clear API contract between services

**🚀 Independent Development:**
- Frontend and backend teams can work simultaneously
- Different technology stacks and deployment strategies
- Independent scaling and versioning

**📦 Flexible Deployment:**
- Deploy backend on AI-optimized servers (GPU, high memory)
- Serve frontend from CDN or static hosting (fast, global)
- Easy to switch frontend frameworks (React, Vue, Angular) without touching backend

**🔧 Easy Maintenance:**
- Update AI models without touching UI
- Redesign frontend without affecting backend logic
- Independent testing and debugging

## 📁 Project Structure

```
geoGLI chatbot MVP/
├── backend/                      # 🐍 Python FastAPI Backend
│   ├── app/                     # Core application code
│   │   ├── main.py             # FastAPI app + routes  
│   │   ├── router_graph.py     # LangGraph state machine
│   │   ├── schemas.py          # Pydantic v2 models
│   │   ├── utils/              # SSE and session utilities
│   │   ├── rag/                # RAG system (FAISS + BGE-M3)
│   │   ├── connectors/         # Route A stubs (commented)
│   │   └── llm/                # LLM provider (placeholder)
│   ├── corpus/                 # Document corpus for ingestion
│   ├── requirements.txt        # Python dependencies
│   ├── env.example            # Environment variables template
│   ├── Makefile               # Backend development commands
│   └── Dockerfile             # Backend containerization
├── frontend/                   # 🌐 Static Frontend
│   ├── index.html             # Green floating chat widget
│   ├── package.json           # Frontend metadata & scripts
│   └── Dockerfile             # Frontend containerization
├── docker-compose.yml          # 🐳 Container orchestration
├── start.bat                  # 🚀 Windows quick start script
└── README.md                  # This documentation
```

## Features

- 🌍 **RAG-based Q&A** using FAISS vector search and BGE-M3 embeddings
- 📡 **Real-time streaming** with Server-Sent Events (SSE)
- 🟢 **Green floating widget** (vanilla HTML/JS)
- 🔄 **LangGraph routing** between structured and RAG queries
- 📚 **Multi-format ingestion** (PDF, Markdown, HTML)
- 🚀 **Ready-to-run** with simple setup

## 🚀 Quick Start

### Method 1: One-Click Setup (Recommended)

**Windows Users**: Use the automated setup script
```cmd
# Double-click to run or execute in command prompt
start.bat
```

This script will:
1. ✅ Set up Python virtual environment
2. ✅ Install all dependencies (with compatibility fixes)
3. ✅ Configure environment variables
4. ✅ Build the vector search index
5. ✅ Start both backend and frontend

**Note**: The script automatically detects and fixes the `huggingface_hub` compatibility issue.

### Method 2: Manual Setup

#### 🐍 Backend Setup (Windows)

**Using Command Prompt:**
```cmd
cd backend

# 1. Create and activate virtual environment
python -m venv .venv
call .venv\Scripts\activate.bat

# 2. Install dependencies
pip install -r requirements.txt

# 2a. Fix dependency compatibility if needed
# If you get "ImportError: cannot import name 'cached_download'":
# pip install huggingface_hub==0.13.4 --force-reinstall
# Or use: fix-dependencies.bat

# 3. Copy environment template
copy env.example .env

# 4. Build vector index (uses demo document)
python -m app.rag.ingest --input .\corpus --rebuild

# 5. Start backend server
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

**Using PowerShell:**
```powershell
cd backend

# Enable script execution if needed
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass

# 1. Create and activate virtual environment
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# 2. Install dependencies
pip install -r requirements.txt

# 3. Copy environment template
Copy-Item env.example .env

# 4. Build vector index
python -m app.rag.ingest --input .\corpus --rebuild

# 5. Start backend server
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload   or delete reload
```

**Using Makefile (Linux/Mac):**
```bash
cd backend
make install    # Install dependencies
make ingest     # Build index from corpus/
make run        # Start server
```

#### 🌐 Frontend Setup

**Option 1: Direct File Access (Simplest)**
```cmd
# Open the HTML file directly in your browser
start frontend\index.html
```

**Option 2: Local HTTP Server (Recommended for Development)**
```cmd
cd frontend

# Using Python built-in server
python -m http.server 3000
# Then open: http://localhost:3000
```

**Option 3: Using npm scripts**
```cmd
cd frontend
npm run dev     # Serves on http://localhost:3000
# or
npm run serve   # Serves on http://localhost:8080
```

### Method 3: Docker Deployment

**Full Stack with Docker Compose:**
```cmd
# Build and start both services
docker-compose up --build

# Access:
# Backend: http://localhost:8000
# Frontend: http://localhost:3000
```

**Individual Services:**
```cmd
# Backend only
cd backend
docker build -t geogli-backend .
docker run -p 8000:8000 geogli-backend

# Frontend only  
cd frontend
docker build -t geogli-frontend .
docker run -p 3000:80 geogli-frontend
```

## API Endpoints

- `GET /health` → `{"status": "ok"}`
- `GET /query/stream` → SSE streaming endpoint
  - Query params: `q` (required), `session_id`, `route_hint`, `top_k`
- `POST /query` → Non-streaming endpoint (optional)

## ⚙️ Configuration

### 🐍 Backend Configuration

Edit `backend/.env` to customize the backend behavior:

```env
# Application Environment
APP_ENV=dev

# CORS Settings - Add your frontend URLs here
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:8080

# RAG System Settings
EMBEDDING_BACKEND=bge-m3          # or openai_compat
INDEX_PATH=./storage/faiss        # Vector store location
TOP_K=6                          # Number of documents to retrieve

# LLM Provider Settings (placeholder)
LLM_PROVIDER=openai_compatible
LLM_BASE_URL=
LLM_API_KEY=
```

### 🌐 Frontend Configuration

Update the API endpoint in `frontend/index.html` if your backend runs on a different URL:

```javascript
// Configuration - Update this URL to point to your backend
const API_BASE_URL = 'http://localhost:8000';
```

**Common Configurations:**
- **Local Development**: `http://localhost:8000`
- **Docker Setup**: `http://localhost:8000` 
- **Production**: `https://your-backend-domain.com`

### 🔗 CORS Configuration

The backend is configured to accept requests from common frontend ports:
- `http://localhost:3000` (React, Vue development servers)
- `http://localhost:8080` (Alternative development port)

To add more origins, update the `ALLOWED_ORIGINS` in `backend/.env`:
```env
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:8080,https://yourdomain.com
```

## Current Implementation

- ✅ **Route B (RAG)**: Active - uses FAISS + BGE-M3 embeddings
- ⏸️ **Route A (Structured)**: Disabled - connector stubs are commented out
- 🔄 **LLM**: Placeholder implementation for testing

## Adding Documents

1. **Add documents** to `backend/corpus/` directory
   - Supported: PDF, Markdown (.md), HTML files
   - Can create subdirectories for organization

2. **Rebuild index**:
   ```cmd
   cd backend
   python -m app.rag.ingest --input .\corpus --rebuild
   ```

3. **Restart backend** to load new index

## Performance Tuning

Key variables in code (marked with `# TODO: PERFORMANCE`):

- `CHUNK_SIZE=700` (words per chunk)
- `CHUNK_OVERLAP=150` (word overlap)
- `TOP_K=6` (retrieved documents)
- `EMBEDDING_BACKEND=bge-m3|openai_compat`

## Enabling Route A (Structured Queries)

Route A connectors are implemented but commented out. To enable:

1. **Uncomment connector code** in `backend/app/connectors/*.py`
2. **Install additional dependencies**:
   ```bash
   pip install psycopg2-binary elasticsearch owslib
   ```
3. **Add connection settings** to `backend/.env`:
   ```env
   POSTGIS_CONNECTION_STRING=postgresql://user:pass@host:5432/db
   ELASTICSEARCH_HOST=localhost:9200
   OGC_WMS_URL=https://example.com/wms
   ```
4. **Update router logic** in `backend/app/router_graph.py`

## 🛠️ Development Guide

### 🐍 Backend Development

**Development Setup:**
```cmd
cd backend

# Install in development mode
pip install -r requirements.txt

# Run with auto-reload for development
make run
# or
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# Test endpoints
make test
# or
curl http://localhost:8000/health
```

**Key Development Features:**
- ✅ **Auto-reload** on code changes
- ✅ **Interactive API docs** at `http://localhost:8000/docs`
- ✅ **Health monitoring** at `http://localhost:8000/health`
- ✅ **CORS enabled** for cross-origin requests

**Adding New Documents:**
```cmd
# 1. Add documents to corpus directory
cp your-document.pdf backend/corpus/

# 2. Rebuild the search index
cd backend
python -m app.rag.ingest --input ./corpus --rebuild

# 3. Restart the backend to load new index
```

### 🌐 Frontend Development

**Development Setup:**
```cmd
cd frontend

# Serve with Python (recommended for development)
python -m http.server 3000

# Or use npm scripts
npm run dev     # http://localhost:3000
npm run serve   # http://localhost:8080
```

**Frontend Architecture:**
- 📄 **Single HTML file** with embedded CSS and JavaScript
- 🔄 **EventSource API** for real-time SSE streaming  
- 💾 **localStorage** for session management
- 🎨 **Pure CSS** styling (no frameworks)

**Development Tips:**
1. **Use a local server** for proper CORS handling (not file:// protocol)
2. **Update API_BASE_URL** in `index.html` to point to your backend
3. **Monitor Network tab** in browser dev tools for SSE events
4. **Check Console** for JavaScript errors and API responses

### 🔄 Frontend-Backend Communication

**API Communication Flow:**
```
Frontend (port 3000) ←→ Backend (port 8000)
     │                        │
     │── HTTP GET /health ────→│ Health check
     │                        │
     │── EventSource /query/stream ──→│ SSE streaming
     │                        │
     │←─ event: token ────────│ Real-time tokens
     │←─ event: final ────────│ Complete response
```

**Testing the Integration:**
```cmd
# 1. Start backend
cd backend && make run

# 2. Start frontend  
cd frontend && python -m http.server 3000

# 3. Open browser to http://localhost:3000
# 4. Test chat functionality
```

## 🧪 Testing Guide

### 🔍 Backend API Testing

**Health Check:**
```bash
# Test if backend is running
curl http://localhost:8000/health
# Expected: {"status":"ok"}
```

**Streaming Endpoint Test:**
```bash
# Test SSE streaming in browser
http://localhost:8000/query/stream?q=hello

# Or using curl (will show raw SSE events)
curl -N -H "Accept: text/event-stream" \
  "http://localhost:8000/query/stream?q=what%20are%20land%20indicators"
```

**Interactive API Documentation:**
```
Open: http://localhost:8000/docs
- ✅ Test all endpoints interactively
- ✅ View request/response schemas  
- ✅ Try different parameters
```

### 🌐 Frontend Testing

**Manual Testing:**
1. **Open frontend**: `http://localhost:3000` (or direct file access)
2. **Test chat functionality**:
   - Type: "What are land degradation indicators?"
   - Verify: Real-time streaming response
   - Check: Source links appear
   - Confirm: Session persistence across page reloads

**Browser Developer Tools:**
```javascript
// Check in Console tab
console.log(localStorage.getItem('geogli_session_id'));

// Monitor Network tab for:
// - EventSource connection to /query/stream
// - SSE events (token, final, error)
// - CORS headers
```

### 🔄 End-to-End Testing

**Complete Workflow Test:**
```cmd
# 1. Start both services
cd backend && make run &
cd frontend && python -m http.server 3000 &

# 2. Test the complete flow
# - Health check: curl http://localhost:8000/health
# - Open frontend: http://localhost:3000  
# - Send test message
# - Verify streaming response
# - Check source citations
```

**Test Queries:**
- ✅ "What are the main land degradation indicators?"
- ✅ "How is vegetation productivity measured?"  
- ✅ "Tell me about soil organic carbon trends"
- ✅ "What is the GeoGLI system?"

## Dependencies

### Backend
- **Core**: FastAPI, uvicorn, pydantic v2
- **LangGraph**: langgraph, langchain-core  
- **RAG**: sentence-transformers, faiss-cpu
- **Documents**: PyPDF2, beautifulsoup4, markdown
- **Utils**: python-dotenv

### Frontend
- **Pure HTML/CSS/JavaScript** - no build process required
- **EventSource API** for SSE streaming
- **localStorage** for session management

## TODOs & Future Enhancements

### TODO-1: Chunking Strategy
**Current**: Fixed word-length chunking (700 words, 150 overlap)
**Consider**: Semantic chunking for better context preservation

### TODO-2: OCR & Table Extraction  
**Current**: Text-only extraction from PDFs
**Consider**: OCR for images and structured table extraction

### TODO-3: Geographic Coverage
**Current**: No country/year restrictions, general hints only
**Consider**: Structured metadata extraction and filtering

### TODO-4: LLM Integration
**Current**: Mock responses for testing
**Consider**: OpenAI-compatible API integration

## License

This is a minimal MVP implementation for UNCCD GeoGLI chatbot development.

## 🚨 Troubleshooting

### Common Issues & Solutions

**❌ Backend won't start:**
```cmd
# Check Python version (requires 3.11+)
python --version

# Verify virtual environment is activated
# Windows: Should show (.venv) in prompt
# Check dependencies
pip list | grep fastapi
```

**❌ ImportError: cannot import name 'cached_download' from 'huggingface_hub':**
This is a dependency compatibility issue between `sentence-transformers` and `huggingface_hub`.

```cmd
# Solution 1: Use fixed compatible versions (recommended)
pip install -r requirements.txt --force-reinstall

# Solution 2: Use updated versions
pip install -r requirements-updated.txt --force-reinstall

# Solution 3: Manual fix
pip install huggingface_hub==0.13.4 --force-reinstall
```

**❌ Frontend can't connect to backend:**
```javascript
// Check CORS settings in backend/.env
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:8080

// Verify API_BASE_URL in frontend/index.html
const API_BASE_URL = 'http://localhost:8000';

// Test backend directly
curl http://localhost:8000/health
```

**❌ No search results:**
```cmd
# Rebuild the vector index
cd backend
python -m app.rag.ingest --input ./corpus --rebuild

# Check if documents exist
ls corpus/
```

**❌ SSE streaming not working:**
- ✅ Use HTTP server (not file://) for frontend
- ✅ Check browser Network tab for EventSource connection
- ✅ Verify CORS headers in response
- ✅ Test with curl: `curl -N -H "Accept: text/event-stream" "http://localhost:8000/query/stream?q=test"`

### 🔧 Development Tips

**Performance Optimization:**
```python
# In backend code, look for these TODO markers:
# TODO: PERFORMANCE - CHUNK_SIZE=700
# TODO: PERFORMANCE - CHUNK_OVERLAP=150  
# TODO: PERFORMANCE - TOP_K=6
```

**Adding Custom Documents:**
1. Copy files to `backend/corpus/`
2. Run: `python -m app.rag.ingest --input ./corpus --rebuild`
3. Restart backend to load new index

**Monitoring & Debugging:**
- Backend logs: Check terminal running uvicorn
- Frontend logs: Browser Developer Console
- API docs: `http://localhost:8000/docs`
- Health check: `http://localhost:8000/health`

## 📞 Support

**For issues and questions:**

1. **Check logs first**:
   - Backend: Terminal running uvicorn
   - Frontend: Browser Developer Console

2. **Verify setup**:
   - ✅ Backend health: `curl http://localhost:8000/health`
   - ✅ CORS settings match your frontend URL
   - ✅ Vector index is built: Check `backend/storage/faiss/`
   - ✅ Documents in corpus: `ls backend/corpus/`

3. **Test components separately**:
   - Backend API: Use `http://localhost:8000/docs`
   - Frontend: Check Network tab for API calls
   - Integration: Monitor SSE events in DevTools

4. **Common fixes**:
   - Restart both services
   - Rebuild vector index
   - Check firewall/antivirus blocking ports
   - Verify Python virtual environment is activated