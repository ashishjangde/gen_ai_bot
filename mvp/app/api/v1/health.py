"""
Health check endpoints.
"""

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(tags=["Health"])


class HealthResponse(BaseModel):
    status: str
    version: str = "1.0.0"


class DetailedHealthResponse(BaseModel):
    status: str
    version: str = "1.0.0"
    database: str = "unknown"
    qdrant: str = "unknown"
    valkey: str = "unknown"


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """Basic health check."""
    return HealthResponse(status="healthy")


@router.get("/health/detailed", response_model=DetailedHealthResponse)
async def detailed_health_check():
    """
    Detailed health check with service status.
    
    Checks connectivity to:
    - PostgreSQL database
    - Qdrant vector store
    - Valkey cache
    """
    db_status = "unknown"
    qdrant_status = "unknown"
    valkey_status = "unknown"
    
    # Check database
    try:
        from mvp.app.db.database import engine
        async with engine.connect() as conn:
            await conn.execute("SELECT 1")
        db_status = "healthy"
    except Exception as e:
        db_status = f"unhealthy: {str(e)[:50]}"
    
    # Check Qdrant
    try:
        from qdrant_client import QdrantClient
        from mvp.app.config.settings import settings
        client = QdrantClient(url=settings.qdrant_url)
        client.get_collections()
        qdrant_status = "healthy"
    except Exception as e:
        qdrant_status = f"unhealthy: {str(e)[:50]}"
    
    # Check Valkey
    try:
        import valkey.asyncio as valkey_client
        from mvp.app.config.settings import settings
        client = valkey_client.from_url(settings.valkey_url)
        await client.ping()
        await client.close()
        valkey_status = "healthy"
    except Exception as e:
        valkey_status = f"unhealthy: {str(e)[:50]}"
    
    overall = "healthy" if all(
        s == "healthy" for s in [db_status, qdrant_status, valkey_status]
    ) else "degraded"
    
    return DetailedHealthResponse(
        status=overall,
        database=db_status,
        qdrant=qdrant_status,
        valkey=valkey_status,
    )
