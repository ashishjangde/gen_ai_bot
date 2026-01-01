"""
FastAPI Application Entry Point

A scalable ChatGPT-like platform with:
- Intelligent routing (RouterService)
- Multi-source search (Tavily, Qdrant, Mem0)
- Background processing (RQ + Valkey)
- Async database (PostgreSQL + SQLAlchemy)
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from mvp.app.api.v1 import router as api_router
from mvp.app.config.settings import settings
from mvp.app.services import get_chat_service, get_memory_service, get_search_service

# Configure logging
logging.basicConfig(
    level=logging.DEBUG if settings.debug else logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


# =============================================================================
# Lifespan - Startup/Shutdown
# =============================================================================
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan handler.
    
    Startup:
    - Initialize chat service (includes router, search, memory)
    - Connect to databases
    
    Shutdown:
    - Close all connections gracefully
    """
    logger.info("🚀 Starting application...")
    
    # Initialize services
    try:
        chat_service = await get_chat_service()
        logger.info("✅ ChatService initialized")
    except Exception as e:
        logger.error(f"❌ Failed to initialize ChatService: {e}")
    
    yield
    
    # Shutdown
    logger.info("🛑 Shutting down application...")
    try:
        if chat_service:
            await chat_service.close()
        logger.info("✅ Services closed")
    except Exception as e:
        logger.error(f"❌ Error during shutdown: {e}")


# =============================================================================
# App Factory
# =============================================================================
def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    
    app = FastAPI(
        title="AI Chat Platform",
        description="A ChatGPT-like platform with intelligent routing and multi-source retrieval",
        version="1.0.0",
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc",
    )
    
    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Configure for production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Include API routes
    app.include_router(api_router)
    
    # Root endpoint
    @app.get("/")
    async def root():
        return {
            "name": "AI Chat Platform",
            "version": "1.0.0",
            "docs": "/docs",
        }
    
    # Global exception handler
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        logger.error(f"Unhandled exception: {exc}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal server error"},
        )
    
    return app


# Create app instance
app = create_app()


# =============================================================================
# Entry Point
# =============================================================================
if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
    )
