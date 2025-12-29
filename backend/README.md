# 🤖 AI Chat Platform with RAG & Memory

A production-ready AI chat application featuring **Retrieval-Augmented Generation (RAG)**, **Long-Term Memory**, **Real-time Web Search**, and **Document Processing**.

Built with modern async Python, LangGraph agents, and scalable architecture.

![Python](https://img.shields.io/badge/Python-3.12-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115-green)
![LangGraph](https://img.shields.io/badge/LangGraph-Latest-purple)
![Docker](https://img.shields.io/badge/Docker-Compose-blue)

---

## 🏗️ Architecture

```mermaid
graph TB
    subgraph Client
        FE[Frontend App]
    end

    subgraph API["FastAPI Backend"]
        AUTH[Auth Service]
        CHAT[Chat Service]
        AGENT[LangGraph Agent]
    end

    subgraph Workers["Background Workers"]
        RQ[RQ Workers]
    end

    subgraph Storage
        PG[(PostgreSQL)]
        QD[(Qdrant Vector DB)]
        VK[(Valkey/Redis)]
        OCI[(Oracle Cloud Storage)]
    end

    subgraph Memory
        STM[Short-Term Memory]
        LTM[Long-Term Memory - Mem0]
    end

    subgraph External
        LLM[Groq LLM API]
        TAVILY[Tavily Web Search]
    end

    FE --> AUTH
    FE --> CHAT
    CHAT --> AGENT
    AGENT --> LLM
    AGENT --> TAVILY
    CHAT --> RQ
    RQ --> QD
    RQ --> OCI
    CHAT --> STM
    CHAT --> LTM
    STM --> VK
    AUTH --> PG
    CHAT --> PG
```

---

## ✨ Features

### 🔐 Authentication

- JWT-based authentication with access & refresh tokens
- HTTP-only cookie support (secure) + Bearer token (dev)
- Session management with automatic limits
- Email verification with OTP

### 💬 Intelligent Chat

- **LangGraph Agent**: Structured AI workflows with tool calling
- **Web Search**: Real-time information via Tavily API
- **RAG**: Query your uploaded documents
- **Streaming**: Server-Sent Events for real-time responses

### 🧠 Memory System

- **Short-Term Memory (STM)**: Recent conversation in Valkey (fast)
- **Long-Term Memory (LTM)**: User facts & preferences via Mem0
- **Token Optimization**: ~2000 tokens per request (efficient!)

### 📄 Document Processing

- **Unified Upload**: PDF, CSV, TXT, MD, JSON support
- **Background Processing**: Async via RQ workers
- **Cloud Storage**: Oracle OCI Object Storage
- **Web Scraping**: Extract & embed web pages

### 🚀 Production Ready

- Async everywhere (SQLAlchemy, FastAPI)
- Structured logging (JSON in prod, colored in dev)
- Rate limiting & CORS protection
- Health checks for all services
- Docker Compose for easy deployment

---

## 🛠️ Tech Stack

| Category             | Technology                                   |
| -------------------- | -------------------------------------------- |
| **Backend**          | FastAPI, Python 3.12, Uvicorn                |
| **AI/ML**            | LangGraph, LangChain, HuggingFace Embeddings |
| **LLM**              | Groq (Llama 3.3 70B)                         |
| **Vector DB**        | Qdrant                                       |
| **Database**         | PostgreSQL 16 + SQLAlchemy (async)           |
| **Cache/Queue**      | Valkey (Redis-compatible)                    |
| **Task Queue**       | Python RQ                                    |
| **Storage**          | Oracle Cloud Object Storage                  |
| **Search**           | Tavily API                                   |
| **Memory**           | Mem0                                         |
| **Auth**             | JWT (PyJWT), bcrypt                          |
| **Containerization** | Docker, Docker Compose                       |

---

## 📁 Project Structure

```
backend/
├── app/
│   ├── advices/              # Response handlers, exception handling
│   ├── config/               # Settings, DB, Valkey, OCI, RQ config
│   ├── db/                   # Database connection
│   ├── exceptions/           # Custom exceptions
│   ├── middlewares/          # Auth dependencies
│   ├── modules/
│   │   ├── user_service/     # Auth, users, sessions
│   │   └── chat_service/     # Chat, RAG, memory, agents
│   │       ├── jobs/         # Background jobs (PDF, CSV, web)
│   │       ├── models/       # SQLAlchemy models
│   │       ├── repositories/ # Data access layer
│   │       ├── router/       # API endpoints
│   │       ├── schema/       # Pydantic schemas
│   │       ├── services/     # Business logic
│   │       └── tools/        # Embedder, LLM tools
│   └── schema/               # Shared schemas
├── alembic/                  # Database migrations
├── main.py                   # App entrypoint
├── Dockerfile
└── dev-docker-compose.yml
```

---

## 🚀 Quick Start

### Prerequisites

- Docker & Docker Compose
- Python 3.12+
- [uv](https://github.com/astral-sh/uv) (fast Python package manager)

### 1. Clone & Setup

```bash
git clone https://github.com/yourusername/gen_ai_proj.git
cd gen_ai_proj/backend

# Copy environment file
cp .env.example .env
```

### 2. Configure Environment

```bash
# .env
DATABASE_URL=postgresql+asyncpg://devuser:devpassword@postgres:5432/devdb

# Required
LLM_API_KEY=your_groq_api_key

# Optional - for web search
TAVILY_API_KEY=your_tavily_key

# Optional - for cloud storage
OCI_NAMESPACE=your_namespace
OCI_BUCKET_NAME=your_bucket
```

### 3. Run with Docker

```bash
docker compose -f dev-docker-compose.yml up -d --build
```

### 4. Run Migrations

```bash
docker exec dev_backend uv run alembic upgrade head
```

### 5. Access

- **API Docs**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health

---

## 📚 API Endpoints

### Authentication

| Method | Endpoint                | Description          |
| ------ | ----------------------- | -------------------- |
| POST   | `/api/v1/auth/register` | Register new user    |
| POST   | `/api/v1/auth/login`    | Login & get tokens   |
| POST   | `/api/v1/auth/refresh`  | Refresh access token |
| GET    | `/api/v1/users/me`      | Get current user     |

### Chat Sessions

| Method | Endpoint                     | Description               |
| ------ | ---------------------------- | ------------------------- |
| POST   | `/api/v1/chat/sessions`      | Create session            |
| GET    | `/api/v1/chat/sessions`      | List sessions             |
| GET    | `/api/v1/chat/sessions/{id}` | Get session with messages |
| DELETE | `/api/v1/chat/sessions/{id}` | Delete session            |

### Messaging

| Method | Endpoint                                 | Description                  |
| ------ | ---------------------------------------- | ---------------------------- |
| POST   | `/api/v1/chat/sessions/{id}/messages`    | Send message (SSE streaming) |
| POST   | `/api/v1/chat/sessions/{id}/upload`      | Upload file (PDF/CSV/TXT)    |
| POST   | `/api/v1/chat/sessions/{id}/sources/web` | Scrape web page              |

---

## 🧪 Example Usage

### Send a Message with Web Search

```bash
curl -X POST "http://localhost:8000/api/v1/chat/sessions/{session_id}/messages" \
  -H "Authorization: Bearer {token}" \
  -H "Content-Type: application/json" \
  -d '{
    "content": "What are the latest AI news today?",
    "enable_web_search": true
  }'
```

### Upload a Document

```bash
curl -X POST "http://localhost:8000/api/v1/chat/sessions/{session_id}/upload" \
  -H "Authorization: Bearer {token}" \
  -F "file=@document.pdf"
```

---

## 🔧 Development

### Local Setup (without Docker)

```bash
# Install dependencies
uv sync

# Run database
docker run -d -p 5432:5432 -e POSTGRES_PASSWORD=postgres postgres:16

# Run migrations
uv run alembic upgrade head

# Start server
uv run uvicorn main:app --reload

# Start worker (separate terminal)
uv run rq worker --url redis://localhost:6379/0
```

---

## 📝 License

MIT License - feel free to use for your own projects!

---

## 👨‍💻 Author

**Ashish Jangde**

- GitHub: [@ashishjangde](https://github.com/ashishjangde)
- LinkedIn: [Ashish Jangde](https://linkedin.com/in/ashishjangde)

---

## 🙏 Acknowledgments

- [LangGraph](https://github.com/langchain-ai/langgraph) - Agent orchestration
- [Qdrant](https://qdrant.tech/) - Vector database
- [Groq](https://groq.com/) - Fast LLM inference
- [Tavily](https://tavily.com/) - Web search API
