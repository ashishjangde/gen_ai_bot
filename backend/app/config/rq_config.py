from redis import Redis
from rq import Queue
from app.config.settings import settings

# RQ uses sync Redis client
def get_rq_redis() -> Redis:
    """Get Redis client for RQ (sync)"""
    return Redis.from_url(settings.valkey_url)


def get_queue(name: str = "default") -> Queue:
    """Get RQ queue"""
    return Queue(name, connection=get_rq_redis())


# Queue names
QUEUE_DEFAULT = "default"
QUEUE_DOCUMENTS = "documents"  # PDF, CSV, web scraping
QUEUE_MEMORY = "memory"  # Mem0 extraction
