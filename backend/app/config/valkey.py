import redis.asyncio as redis
from app.config.settings import settings

# Valkey connection pool (Redis-compatible)
valkey_pool: redis.ConnectionPool | None = None


async def get_valkey_pool() -> redis.ConnectionPool:
    """Get or create Valkey connection pool"""
    global valkey_pool
    if valkey_pool is None:
        valkey_pool = redis.ConnectionPool.from_url(
            settings.valkey_url,
            decode_responses=True,
            max_connections=10,
        )
    return valkey_pool


async def get_valkey_client() -> redis.Redis:
    """Get Valkey client from pool"""
    pool = await get_valkey_pool()
    return redis.Redis(connection_pool=pool)


async def close_valkey_pool() -> None:
    """Close Valkey connection pool"""
    global valkey_pool
    if valkey_pool is not None:
        await valkey_pool.disconnect()
        valkey_pool = None
