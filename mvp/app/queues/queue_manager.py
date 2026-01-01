"""
RQ Queue Manager - Centralized job queuing with Valkey.

This module provides utilities to enqueue jobs to RQ.
Jobs are processed by separate worker processes for scalability.
"""

from redis import Redis
from rq import Queue
from typing import Callable, Any

from mvp.app.config.settings import settings

# Global queue instances (lazy initialized)
_redis_conn: Redis = None
_high_queue: Queue = None
_default_queue: Queue = None
_low_queue: Queue = None


def get_redis_connection() -> Redis:
    """Get or create Redis/Valkey connection."""
    global _redis_conn
    if _redis_conn is None:
        _redis_conn = Redis.from_url(settings.valkey_url)
    return _redis_conn


def get_queue(priority: str = "default") -> Queue:
    """
    Get a queue by priority.
    
    Args:
        priority: 'high', 'default', or 'low'
    """
    global _high_queue, _default_queue, _low_queue
    
    conn = get_redis_connection()
    
    if priority == "high":
        if _high_queue is None:
            _high_queue = Queue("high", connection=conn)
        return _high_queue
    elif priority == "low":
        if _low_queue is None:
            _low_queue = Queue("low", connection=conn)
        return _low_queue
    else:
        if _default_queue is None:
            _default_queue = Queue("default", connection=conn)
        return _default_queue


def enqueue_job(
    func: Callable,
    *args,
    priority: str = "default",
    job_timeout: int = 600,  # 10 minutes default
    result_ttl: int = 3600,  # Keep result for 1 hour
    **kwargs
) -> str:
    """
    Enqueue a job to be processed by RQ workers.
    
    Args:
        func: The function to execute (must be importable by workers)
        *args: Positional arguments for the function
        priority: 'high', 'default', or 'low'
        job_timeout: Max execution time in seconds
        result_ttl: How long to keep result
        **kwargs: Keyword arguments for the function
    
    Returns:
        Job ID
    """
    queue = get_queue(priority)
    job = queue.enqueue(
        func,
        *args,
        job_timeout=job_timeout,
        result_ttl=result_ttl,
        **kwargs
    )
    return job.id


def get_job_status(job_id: str, queue_name: str = "default") -> dict:
    """
    Get the status of a job.
    
    Returns:
        {"status": "queued|started|finished|failed", "result": ..., "error": ...}
    """
    from rq.job import Job
    
    conn = get_redis_connection()
    try:
        job = Job.fetch(job_id, connection=conn)
        return {
            "status": job.get_status(),
            "result": job.result if job.is_finished else None,
            "error": str(job.exc_info) if job.is_failed else None,
        }
    except Exception as e:
        return {"status": "not_found", "error": str(e)}
