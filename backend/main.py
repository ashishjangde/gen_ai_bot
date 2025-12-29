from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from app.router import api_router
from app.advices.global_exception_handler import GlobalExceptionHandler
from app.config.settings import settings
from app.config.logging import setup_logging, app_logger


# Rate limiter
limiter = Limiter(key_func=get_remote_address)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    # Startup
    setup_logging()
    app_logger.info("Application starting up...")
    app_logger.info(f"Environment: {settings.env}")
    app_logger.info(f"Debug mode: {settings.debug}")
    
    yield
    
    # Shutdown
    app_logger.info("Application shutting down...")


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
    lifespan=lifespan,
    contact={
        "name": "Ashish Jangde",
        "url": "https://github.com/ashishjangde",
    },
)

# Rate limiting
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS - Configure for your frontend domain
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # Next.js dev
        "http://localhost:5173",  # Vite dev
        "https://your-frontend.vercel.app",  # Production frontend
    ] if settings.env == "production" else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Exception handlers
GlobalExceptionHandler.register_exception_handlers(app)

# Routes
app.include_router(api_router)


@app.get("/health", include_in_schema=False)
async def health_check():
    """Health check endpoint for container orchestration"""
    health_status = {
        "status": "healthy",
        "env": settings.env,
        "version": "1.0.0",
    }
    
    # Check database connection
    try:
        from app.db.db_connection import async_session_factory
        async with async_session_factory() as session:
            await session.execute("SELECT 1")
        health_status["database"] = "connected"
    except Exception as e:
        health_status["database"] = f"error: {str(e)}"
        health_status["status"] = "degraded"
    
    # Check Valkey/Redis
    try:
        from app.config.valkey import get_valkey_client
        client = await get_valkey_client()
        await client.ping()
        health_status["cache"] = "connected"
    except Exception as e:
        health_status["cache"] = f"error: {str(e)}"
    
    return health_status


@app.get("/", include_in_schema=False)
async def root():
    """Root endpoint - redirect to docs"""
    return {
        "message": "AI Chat Platform API",
        "docs": "/docs",
        "health": "/health",
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)