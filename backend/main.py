from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from app.router import api_router
from app.advices.global_exception_handler import GlobalExceptionHandler
from app.config.settings import settings


limiter = Limiter(key_func=get_remote_address)



app = FastAPI(
    debug=settings.debug,
    title="AI Chat Platform",
    description="""
## 🤖 AI Chat Platform with RAG & Memory

A production-ready AI chat application featuring:
- **Retrieval-Augmented Generation (RAG)** - Query your documents
- **Long-Term Memory** - AI remembers user preferences
- **Real-time Web Search** - Get latest information
- **Document Processing** - PDF, CSV, TXT, JSON support

### Authentication
All endpoints require JWT authentication. Use `/api/v1/auth/login` to get tokens.
    """,
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    contact={
        "name": "Ashish Jangde",
        "url": "https://github.com/ashishjangde",
    },
)

# Rate limiting
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # Next.js dev
        "http://localhost:5173",  # Vite dev
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

GlobalExceptionHandler.register_exception_handlers(app)

app.include_router(api_router)


@app.get("/health", include_in_schema=False)
async def health_check():
    """Health check endpoint for container orchestration"""
    health_status = {
        "status": "healthy",
        "env": settings.env,
        "version": "1.0.0",
    }
    return health_status



if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)