"""Background processing worker.

Run as a separate process alongside the API:

    python -m app.worker

The worker claims queued jobs from the processing_jobs table, runs the
registered handler for each, and records success or failure with retry and
backoff. It creates its own database sessions, exactly like the seed and
lifespan code paths, and binds each job's correlation id so its audit trail and
logs join to the request that enqueued it.

Importing app.services.job_handlers registers the handlers. The worker never
approves, certifies, or validates anything; it only runs the same review-support
processing a reviewer could trigger inline.
"""

from __future__ import annotations

import os
import signal
import time
import uuid

from sqlalchemy.orm import Session

from app.core import request_context
from app.core.config import get_settings
from app.core.logging import log_event
from app.db import models
from app.db.database import SessionLocal
from app.services import job_handlers, job_queue_service

# Importing job_handlers registers the handlers; keep the reference so linters
# do not treat the import as unused.
_ = job_handlers.register_all


def process_job(db: Session, job: models.ProcessingJob) -> models.ProcessingJob:
    """Run one claimed job's handler and record the outcome.

    A permanent domain error (bad or missing input) fails the job without a
    retry. Any other error is treated as transient and retried with backoff.
    The correlation id from the enqueuing request is rebound so the handler's
    audit rows and logs share that id.
    """

    request_context.reset()
    request_context.set_request_id(job.request_id or request_context.new_request_id())
    request_context.bind_project(job.project_id)
    try:
        handler = job_queue_service.get_handler(job.job_type)
        try:
            result = handler(db, dict(job.payload or {}))
        except job_handlers.PERMANENT_ERRORS as exc:
            db.rollback()
            message = getattr(exc, "message", None) or str(exc)
            return job_queue_service.fail_permanent(db, job, message)
        except Exception as exc:  # noqa: BLE001 - transient failures are retried
            db.rollback()
            log_event(
                "job_handler_error",
                job_id=job.job_id,
                job_type=job.job_type,
                error_type=type(exc).__name__,
            )
            return job_queue_service.fail(db, job, "Processing failed.")
        return job_queue_service.complete(db, job, result)
    finally:
        request_context.reset()


def process_available_jobs(db: Session, *, worker_id: str, limit: int = 100) -> int:
    """Claim and process due jobs until the queue is empty. Returns the count.

    Used by the run loop for one pass and directly by tests to drain the queue
    without starting the loop.
    """

    job_queue_service.reclaim_stale(db)
    processed = 0
    while processed < limit:
        job = job_queue_service.claim_next(db, worker_id=worker_id)
        if job is None:
            break
        process_job(db, job)
        processed += 1
    return processed


def run_worker(*, worker_id: str | None = None) -> None:  # pragma: no cover
    """Run the worker loop until interrupted.

    Not exercised by the unit tests, which drive process_available_jobs
    directly; this is the deployed entry point.
    """

    settings = get_settings()
    worker_id = worker_id or f"worker-{os.getpid()}-{uuid.uuid4().hex[:8]}"
    stopping = {"value": False}

    def _stop(_signum, _frame) -> None:
        stopping["value"] = True

    signal.signal(signal.SIGTERM, _stop)
    signal.signal(signal.SIGINT, _stop)

    log_event("worker_started", worker_id=worker_id)
    while not stopping["value"]:
        db = SessionLocal()
        try:
            processed = process_available_jobs(db, worker_id=worker_id)
        finally:
            db.close()
        if processed == 0:
            time.sleep(settings.WORKER_POLL_INTERVAL_SECONDS)
    log_event("worker_stopped", worker_id=worker_id)


if __name__ == "__main__":  # pragma: no cover
    run_worker()
