"""
Queues package for RQ background job processing.

Usage:
    # In FastAPI routes - enqueue jobs
    from mvp.app.queues import enqueue_job
    from mvp.app.queues.tasks import process_file_task
    
    job_id = enqueue_job(process_file_task, arg1, arg2, priority="high")
    
    # Run worker (separate process)
    python -m mvp.app.queues.worker
"""

from mvp.app.queues.queue_manager import (
    enqueue_job,
    get_job_status,
    get_queue,
    get_redis_connection,
)
from mvp.app.queues.tasks import (
    process_file_task,
    update_embeddings_task,
)

__all__ = [
    "enqueue_job",
    "get_job_status",
    "get_queue",
    "get_redis_connection",
    "process_file_task",
    "update_embeddings_task",
]
