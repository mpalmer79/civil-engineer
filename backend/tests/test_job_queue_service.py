"""Unit tests for the durable background job queue service.

These tests drive app.services.job_queue_service directly against the shared
test database using SessionLocal, without the API or the worker loop. A throwaway
handler is registered so the queue accepts a probe job type that does no real
processing, which keeps these tests focused on the queue mechanics: enqueue,
deduplication, claiming, completion, retry with backoff, permanent failure,
reclaiming a stale lease, and tenant-scoped reads.

The lifecycle words queued, running, succeeded, and failed are the queue's own
status vocabulary. A failed job here is a technical processing outcome for a unit
of deferred work; it carries no engineering judgment about a project or a design.
"""

from __future__ import annotations

import uuid
from datetime import timedelta

import pytest
from sqlalchemy import update

from app.core import request_context
from app.core.config import get_settings
from app.db import models
from app.db.database import SessionLocal
from app.db.models.shared import _utcnow
from app.services import job_queue_service
from app.services.job_queue_service import (
    JobQueueError,
    STATUS_FAILED,
    STATUS_QUEUED,
    STATUS_RUNNING,
    STATUS_SUCCEEDED,
)

# A probe handler that does no real processing. Registering it lets the queue
# accept this job type so the tests can exercise the queue mechanics in isolation.
TEST_JOB_TYPE = "test_probe_job"


def _noop_handler(db, payload):
    return {"echo": payload}


job_queue_service.register_handler(TEST_JOB_TYPE, _noop_handler)


def _pid() -> str:
    """Return a unique project id so tests never collide on deduplication."""

    return f"proj_probe_{uuid.uuid4().hex[:12]}"


def _enqueue(db, project_id, payload, **kwargs):
    return job_queue_service.enqueue(
        db,
        job_type=TEST_JOB_TYPE,
        project_id=project_id,
        payload=payload,
        **kwargs,
    )


@pytest.fixture(autouse=True)
def _clean_queue_and_context(client):
    """Give each test a quiet queue and a cleared request context.

    Depending on the session-scoped client fixture ensures the application has
    started and created the tables. Any queued or running rows left by an earlier
    test are moved to a terminal state so claim_next and reclaim_stale act only on
    the row a test creates.
    """

    request_context.reset()
    db = SessionLocal()
    try:
        db.execute(
            update(models.ProcessingJob)
            .where(models.ProcessingJob.status.in_((STATUS_QUEUED, STATUS_RUNNING)))
            .values(status=STATUS_FAILED, finished_at=_utcnow(), updated_at=_utcnow())
        )
        db.commit()
    finally:
        db.close()
    yield
    request_context.reset()


@pytest.fixture
def db():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


def test_enqueue_creates_queued_job_and_captures_request_id(db):
    request_context.set_request_id("req_probe_abc")
    job = _enqueue(db, _pid(), {"document_id": "doc_1"})
    assert job.status == STATUS_QUEUED
    assert job.attempts == 0
    assert job.request_id == "req_probe_abc"
    assert job.job_id.startswith("job_")


def test_enqueue_dedupes_active_jobs(db):
    pid = _pid()
    payload = {"document_id": "doc_dedupe"}
    first = _enqueue(db, pid, payload)
    again = _enqueue(db, pid, payload)
    # A repeated request for the same input returns the existing active job.
    assert again.job_id == first.job_id

    different = _enqueue(db, pid, {"document_id": "doc_other"})
    assert different.job_id != first.job_id

    forced = _enqueue(db, pid, payload, dedupe=False)
    assert forced.job_id != first.job_id


def test_enqueue_unregistered_job_type_raises(db):
    with pytest.raises(JobQueueError):
        job_queue_service.enqueue(
            db,
            job_type="not_a_registered_type",
            project_id=_pid(),
            payload={},
        )


def test_claim_next_transitions_queued_to_running(db):
    pid = _pid()
    _enqueue(db, pid, {"n": 1})
    _enqueue(db, pid, {"n": 2})

    first = job_queue_service.claim_next(db, worker_id="worker-a")
    assert first is not None
    assert first.status == STATUS_RUNNING
    assert first.attempts == 1
    assert first.locked_by == "worker-a"
    assert first.started_at is not None

    second = job_queue_service.claim_next(db, worker_id="worker-a")
    assert second is not None
    assert second.job_id != first.job_id

    # Nothing else is due, so a further claim returns None.
    assert job_queue_service.claim_next(db, worker_id="worker-a") is None


def test_claim_next_skips_future_available_at(db):
    pid = _pid()
    job = _enqueue(db, pid, {"n": 1})
    future = _utcnow() + timedelta(hours=1)
    db.execute(
        update(models.ProcessingJob)
        .where(models.ProcessingJob.job_id == job.job_id)
        .values(available_at=future)
    )
    db.commit()
    # The only queued job is not yet due, so nothing is claimed.
    assert job_queue_service.claim_next(db, worker_id="worker-a") is None


def test_complete_marks_succeeded_and_clears_lock(db):
    _enqueue(db, _pid(), {"n": 1})
    claimed = job_queue_service.claim_next(db, worker_id="worker-a")
    assert claimed is not None
    done = job_queue_service.complete(db, claimed, {"processing_status": "indexed"})
    assert done.status == STATUS_SUCCEEDED
    assert done.result == {"processing_status": "indexed"}
    assert done.finished_at is not None
    assert done.locked_by is None
    assert done.error is None


def test_fail_requeues_with_backoff_before_attempts_exhausted(db):
    _enqueue(db, _pid(), {"n": 1}, max_attempts=3)
    claimed = job_queue_service.claim_next(db, worker_id="worker-a")
    assert claimed is not None and claimed.attempts == 1
    result = job_queue_service.fail(db, claimed, "temporary glitch")
    # Below the attempt ceiling the job returns to the queue with a future
    # availability so a transient fault backs off instead of spinning.
    assert result.status == STATUS_QUEUED
    assert result.attempts == 1
    assert result.error == "temporary glitch"
    # Availability is pushed past the claim time by the backoff window.
    assert result.available_at > result.started_at
    assert result.locked_by is None


def test_fail_marks_failed_when_attempts_exhausted(db, monkeypatch):
    monkeypatch.setattr(get_settings(), "WORKER_RETRY_BACKOFF_SECONDS", 0)
    _enqueue(db, _pid(), {"n": 1}, max_attempts=1)
    claimed = job_queue_service.claim_next(db, worker_id="worker-a")
    assert claimed is not None and claimed.attempts == 1
    result = job_queue_service.fail(db, claimed, "still failing")
    # The single allowed attempt is used, so the job reaches its terminal state.
    assert result.status == STATUS_FAILED
    assert result.error == "still failing"
    assert result.finished_at is not None


def test_fail_permanent_marks_failed_regardless_of_attempts(db):
    _enqueue(db, _pid(), {"n": 1}, max_attempts=5)
    claimed = job_queue_service.claim_next(db, worker_id="worker-a")
    assert claimed is not None and claimed.attempts == 1
    result = job_queue_service.fail_permanent(db, claimed, "missing input")
    # A permanent fault stops retrying even with attempts left.
    assert result.status == STATUS_FAILED
    assert result.attempts < result.max_attempts
    assert result.error == "missing input"
    assert result.finished_at is not None


def test_reclaim_stale_requeues_expired_lease(db):
    pid = _pid()
    _enqueue(db, pid, {"n": 1})
    claimed = job_queue_service.claim_next(db, worker_id="worker-a")
    assert claimed is not None and claimed.status == STATUS_RUNNING
    # Simulate a worker that died: push the lock time far into the past.
    past = _utcnow() - timedelta(seconds=3600)
    db.execute(
        update(models.ProcessingJob)
        .where(models.ProcessingJob.job_id == claimed.job_id)
        .values(locked_at=past)
    )
    db.commit()

    count = job_queue_service.reclaim_stale(db, older_than_seconds=1)
    assert count == 1
    db.expire_all()
    reclaimed = job_queue_service.get_job(db, job_id=claimed.job_id, project_id=pid)
    assert reclaimed is not None
    assert reclaimed.status == STATUS_QUEUED
    assert reclaimed.locked_by is None


def test_get_job_enforces_tenant_scope(db):
    pid = _pid()
    job = _enqueue(db, pid, {"n": 1})
    assert job_queue_service.get_job(db, job_id=job.job_id, project_id=pid) is not None
    # A read scoped to a different project must not see the job.
    assert (
        job_queue_service.get_job(db, job_id=job.job_id, project_id="proj_other")
        is None
    )


def test_list_jobs_scopes_to_project_and_orders_newest_first(db):
    pid = _pid()
    other = _pid()
    first = _enqueue(db, pid, {"seq": 1})
    second = _enqueue(db, pid, {"seq": 2})
    outside = _enqueue(db, other, {"seq": 3})

    jobs = job_queue_service.list_jobs(db, project_id=pid)
    ids = [job.job_id for job in jobs]
    assert set(ids) == {first.job_id, second.job_id}
    assert outside.job_id not in ids
    # Newest first: the most recently enqueued job leads the list.
    assert ids[0] == second.job_id
