"""Durable background job queue over the processing_jobs table.

The queue lets file processing run on a background worker instead of the request
thread. A route enqueues a job and returns immediately; a worker claims the job,
runs the registered handler, and records the outcome with retry and backoff. The
queue is backed by the database, so a job survives a restart and its lifecycle is
auditable.

Job claiming is safe under concurrent workers on both supported backends. On
PostgreSQL it uses SELECT ... FOR UPDATE SKIP LOCKED. On SQLite, which serializes
writers, a compare-and-set update guards the claim. Nothing here changes the
professional boundary: a job only schedules review-support processing.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta
from typing import Any, Callable

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.logging import log_event
from app.db import models
from app.db.models.shared import _utcnow

STATUS_QUEUED = "queued"
STATUS_RUNNING = "running"
STATUS_SUCCEEDED = "succeeded"
STATUS_FAILED = "failed"

ACTIVE_STATUSES = (STATUS_QUEUED, STATUS_RUNNING)
TERMINAL_STATUSES = (STATUS_SUCCEEDED, STATUS_FAILED)

# How many queued candidates a single claim attempt will skip past when another
# worker wins the compare-and-set race before giving up for this poll.
_CLAIM_MAX_SKIPS = 10


class JobQueueError(Exception):
    """A job could not be enqueued or read. Carries a safe HTTP status."""

    def __init__(self, message: str, status_code: int = 400) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code


# Handler registry. A handler receives a worker session and the job payload and
# returns a non-sensitive result summary. Registration happens at import of
# app.services.job_handlers, which the API and the worker both import.
JobHandler = Callable[[Session, dict[str, Any]], dict[str, Any]]
_HANDLERS: dict[str, JobHandler] = {}


def register_handler(job_type: str, handler: JobHandler) -> None:
    """Register the handler that runs a given job type."""

    _HANDLERS[job_type] = handler


def is_registered(job_type: str) -> bool:
    return job_type in _HANDLERS


def get_handler(job_type: str) -> JobHandler:
    handler = _HANDLERS.get(job_type)
    if handler is None:
        raise JobQueueError(f"No handler registered for job type: {job_type}", 400)
    return handler


def registered_job_types() -> tuple[str, ...]:
    return tuple(sorted(_HANDLERS))


def _find_active_duplicate(
    db: Session, *, job_type: str, project_id: str, payload: dict[str, Any]
) -> models.ProcessingJob | None:
    """Return an existing queued or running job with the same input, if any."""

    rows = (
        db.execute(
            select(models.ProcessingJob).where(
                models.ProcessingJob.job_type == job_type,
                models.ProcessingJob.project_id == project_id,
                models.ProcessingJob.status.in_(ACTIVE_STATUSES),
            )
        )
        .scalars()
        .all()
    )
    for job in rows:
        if (job.payload or {}) == payload:
            return job
    return None


def enqueue(
    db: Session,
    *,
    job_type: str,
    project_id: str,
    payload: dict[str, Any],
    max_attempts: int | None = None,
    dedupe: bool = True,
) -> models.ProcessingJob:
    """Enqueue a job, or return the existing active job for the same input.

    Deduplication keeps a repeated request from stacking identical work: if a
    queued or running job already covers this input, that job is returned and no
    new row is created.
    """

    if not is_registered(job_type):
        raise JobQueueError(f"Unknown job type: {job_type}", 400)

    if dedupe:
        existing = _find_active_duplicate(
            db, job_type=job_type, project_id=project_id, payload=payload
        )
        if existing is not None:
            return existing

    settings = get_settings()
    from app.core.request_context import get_request_id

    job = models.ProcessingJob(
        job_id=f"job_{uuid.uuid4().hex}",
        job_type=job_type,
        project_id=project_id,
        payload=payload,
        status=STATUS_QUEUED,
        attempts=0,
        max_attempts=max_attempts or settings.WORKER_MAX_ATTEMPTS,
        available_at=_utcnow(),
        request_id=get_request_id(),
    )
    db.add(job)
    db.commit()
    db.refresh(job)
    log_event("job_enqueued", job_id=job.job_id, job_type=job_type)
    return job


def claim_next(
    db: Session, *, worker_id: str, now: datetime | None = None
) -> models.ProcessingJob | None:
    """Claim the oldest due queued job for a worker, or return None.

    Safe under concurrent workers: PostgreSQL skips rows locked by other workers,
    and a compare-and-set update ensures only one worker transitions a given row
    out of the queued state on any backend.
    """

    now = now or _utcnow()
    is_postgres = db.bind.dialect.name == "postgresql"

    for _ in range(_CLAIM_MAX_SKIPS):
        stmt = (
            select(models.ProcessingJob)
            .where(
                models.ProcessingJob.status == STATUS_QUEUED,
                models.ProcessingJob.available_at <= now,
            )
            .order_by(
                models.ProcessingJob.available_at,
                models.ProcessingJob.created_at,
            )
            .limit(1)
        )
        if is_postgres:
            stmt = stmt.with_for_update(skip_locked=True)

        candidate = db.execute(stmt).scalars().first()
        if candidate is None:
            db.rollback()
            return None

        result = db.execute(
            update(models.ProcessingJob)
            .where(
                models.ProcessingJob.job_id == candidate.job_id,
                models.ProcessingJob.status == STATUS_QUEUED,
            )
            .values(
                status=STATUS_RUNNING,
                attempts=models.ProcessingJob.attempts + 1,
                locked_by=worker_id,
                locked_at=now,
                started_at=now,
                updated_at=now,
            )
        )
        if result.rowcount == 1:
            db.commit()
            claimed = db.get(models.ProcessingJob, candidate.job_id)
            log_event(
                "job_claimed",
                job_id=candidate.job_id,
                job_type=candidate.job_type,
                worker_id=worker_id,
                attempt=claimed.attempts if claimed else None,
            )
            return claimed
        # Another worker won the race; drop the transaction and try the next.
        db.rollback()
    return None


def complete(
    db: Session, job: models.ProcessingJob, result: dict[str, Any]
) -> models.ProcessingJob:
    """Mark a job succeeded with its non-sensitive result summary."""

    now = _utcnow()
    job.status = STATUS_SUCCEEDED
    job.result = result
    job.error = None
    job.finished_at = now
    job.locked_by = None
    job.locked_at = None
    job.updated_at = now
    db.commit()
    db.refresh(job)
    log_event("job_succeeded", job_id=job.job_id, job_type=job.job_type)
    return job


def fail(
    db: Session, job: models.ProcessingJob, error: str
) -> models.ProcessingJob:
    """Record a job failure, retrying with backoff until max attempts.

    The error is a safe, client-shown reason and never a stack trace. On the
    final attempt the job is marked failed; otherwise it returns to the queue
    with an exponential backoff so a transient fault does not spin.
    """

    now = _utcnow()
    safe_error = (error or "Processing failed.").strip()[:500]
    job.error = safe_error
    job.locked_by = None
    job.locked_at = None
    job.updated_at = now

    if job.attempts >= job.max_attempts:
        job.status = STATUS_FAILED
        job.finished_at = now
        log_event(
            "job_failed",
            job_id=job.job_id,
            job_type=job.job_type,
            attempts=job.attempts,
        )
    else:
        backoff = get_settings().WORKER_RETRY_BACKOFF_SECONDS * (
            2 ** max(job.attempts - 1, 0)
        )
        job.status = STATUS_QUEUED
        job.available_at = now + timedelta(seconds=backoff)
        log_event(
            "job_retry_scheduled",
            job_id=job.job_id,
            job_type=job.job_type,
            attempt=job.attempts,
            backoff_seconds=backoff,
        )
    db.commit()
    db.refresh(job)
    return job


def fail_permanent(
    db: Session, job: models.ProcessingJob, error: str
) -> models.ProcessingJob:
    """Mark a job failed with no further retries.

    Used for a permanent fault, such as an unreadable file or a missing record,
    where retrying the same input cannot succeed.
    """

    now = _utcnow()
    job.status = STATUS_FAILED
    job.error = (error or "Processing failed.").strip()[:500]
    job.finished_at = now
    job.locked_by = None
    job.locked_at = None
    job.updated_at = now
    db.commit()
    db.refresh(job)
    log_event(
        "job_failed_permanent",
        job_id=job.job_id,
        job_type=job.job_type,
        attempts=job.attempts,
    )
    return job


def reclaim_stale(
    db: Session, *, older_than_seconds: int | None = None, now: datetime | None = None
) -> int:
    """Requeue running jobs whose worker lease has expired. Returns the count.

    A worker that dies mid-job leaves the row in the running state. After the
    stale timeout the job is returned to the queue so another worker can run it.
    The attempt already counted at claim time is kept, so a job that repeatedly
    kills its worker still exhausts its attempts rather than looping forever.
    """

    now = now or _utcnow()
    timeout = older_than_seconds or get_settings().WORKER_STALE_SECONDS
    cutoff = now - timedelta(seconds=timeout)
    result = db.execute(
        update(models.ProcessingJob)
        .where(
            models.ProcessingJob.status == STATUS_RUNNING,
            models.ProcessingJob.locked_at < cutoff,
        )
        .values(
            status=STATUS_QUEUED,
            locked_by=None,
            locked_at=None,
            available_at=now,
            updated_at=now,
        )
    )
    db.commit()
    count = result.rowcount or 0
    if count:
        log_event("jobs_reclaimed", count=count)
    return count


def get_job(
    db: Session, *, job_id: str, project_id: str
) -> models.ProcessingJob | None:
    """Return a job scoped to its project, or None. Enforces tenant isolation."""

    job = db.get(models.ProcessingJob, job_id)
    if job is None or job.project_id != project_id:
        return None
    return job


def list_jobs(
    db: Session, *, project_id: str, limit: int = 50
) -> list[models.ProcessingJob]:
    """Return recent jobs for a project, newest first."""

    return list(
        db.execute(
            select(models.ProcessingJob)
            .where(models.ProcessingJob.project_id == project_id)
            .order_by(models.ProcessingJob.created_at.desc())
            .limit(limit)
        )
        .scalars()
        .all()
    )
