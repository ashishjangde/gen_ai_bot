"""
RQ Worker setup with Valkey.

Run locally:
    PYTHONPATH=. python -m mvp.app.queues.worker

Run via Docker:
    docker compose up worker
"""

import logging
import sys

from redis import Redis
from rq import Worker, Queue

from mvp.app.config.settings import settings

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def get_redis_connection() -> Redis:
    """Get Redis/Valkey connection for RQ."""
    return Redis.from_url(settings.valkey_url)


def run_worker():
    """Start the RQ worker."""
    logger.info(f"Starting RQ worker connected to {settings.valkey_url}")
    
    conn = get_redis_connection()
    
    # Create queues with priority order
    queues = [
        Queue("high", connection=conn),
        Queue("default", connection=conn),
        Queue("low", connection=conn),
    ]
    
    worker = Worker(queues, connection=conn)
    worker.work(with_scheduler=True)


if __name__ == "__main__":
    run_worker()
