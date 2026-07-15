"""Integration tests for the background worker.

These tests drive app.worker.process_available_jobs against the real registered
handlers. Data is seeded through the API with the client fixture, then the worker
drains the queue using SessionLocal, exactly as the deployed worker process does.
The run loop itself is not started; the tests call the single drain pass directly.

The lifecycle words queued, running, succeeded, and failed are the queue's own
status vocabulary. A failed job is a technical processing outcome for a unit of
deferred review-support work, not an engineering judgment about a project.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select, update

from app.core import request_context
from app.core.config import get_settings
from app.db import models
from app.db.database import SessionLocal
from app.db.models.shared import _utcnow
from app.services import job_handlers, job_queue_service, pdf_indexing_service
from app import worker
from tests.test_pdf_indexing import _create_project, _make_pdf, _upload_pdf

SAMPLE_DXF = (
    Path(__file__).resolve().parent.parent
    / "app"
    / "cad_samples"
    / "brookside_meadows.dxf"
)

# Throwaway handlers used to exercise the transient versus permanent failure
# classification without touching real files. One raises a plain error the worker
# treats as transient; the other raises a domain error the worker treats as
# permanent and does not retry.
TRANSIENT_JOB_TYPE = "test_worker_transient"
PERMANENT_JOB_TYPE = "test_worker_permanent"


def _transient_handler(db, payload):
    raise RuntimeError("transient boom")


def _permanent_handler(db, payload):
    raise pdf_indexing_service.PdfIndexingError("permanent boom", status_code=422)


job_queue_service.register_handler(TRANSIENT_JOB_TYPE, _transient_handler)
job_queue_service.register_handler(PERMANENT_JOB_TYPE, _permanent_handler)


@pytest.fixture(autouse=True)
def _isolate_queue(client):
    """Quiet the queue before each test and clear request context after."""

    request_context.reset()
    db = SessionLocal()
    try:
        db.execute(
            update(models.ProcessingJob)
            .where(
                models.ProcessingJob.status.in_(
                    (job_queue_service.STATUS_QUEUED, job_queue_service.STATUS_RUNNING)
                )
            )
            .values(
                status=job_queue_service.STATUS_FAILED,
                finished_at=_utcnow(),
                updated_at=_utcnow(),
            )
        )
        db.commit()
    finally:
        db.close()
    yield
    request_context.reset()


def _upload_dxf(client: TestClient, project_id: str, file_name: str = "worker.dxf") -> str:
    response = client.post(
        f"/api/v1/projects/{project_id}/cad-files/upload",
        files={"file": (file_name, SAMPLE_DXF.read_bytes(), "application/dxf")},
        data={"uploaded_by": "Town Engineer"},
    )
    assert response.status_code == 200, response.text
    return response.json()["cad_file"]["cad_file_id"]


def _drain(worker_id: str = "test-worker", limit: int = 100) -> int:
    db = SessionLocal()
    try:
        return worker.process_available_jobs(db, worker_id=worker_id, limit=limit)
    finally:
        db.close()


def _snapshot(job_id: str, project_id: str) -> dict | None:
    db = SessionLocal()
    try:
        job = job_queue_service.get_job(db, job_id=job_id, project_id=project_id)
        if job is None:
            return None
        return {
            "status": job.status,
            "attempts": job.attempts,
            "max_attempts": job.max_attempts,
            "result": dict(job.result) if job.result else None,
            "error": job.error,
        }
    finally:
        db.close()


def _enqueue(project_id: str, job_type: str, payload: dict, **kwargs) -> str:
    db = SessionLocal()
    try:
        job = job_queue_service.enqueue(
            db,
            job_type=job_type,
            project_id=project_id,
            payload=payload,
            **kwargs,
        )
        return job.job_id
    finally:
        db.close()


def test_worker_processes_pdf_index_job_end_to_end(client: TestClient):
    pid = _create_project(client, "Worker PDF Project")
    did = _upload_pdf(
        client,
        pid,
        _make_pdf(["Worker stormwater page one", "Outlet detail page two"]),
    )
    job_id = _enqueue(
        pid,
        job_handlers.JOB_PDF_INDEX,
        {"project_id": pid, "document_id": did},
    )
    processed = _drain()
    assert processed >= 1

    snap = _snapshot(job_id, pid)
    assert snap is not None
    assert snap["status"] == job_queue_service.STATUS_SUCCEEDED
    assert snap["result"]["processing_status"] == "indexed_with_text"

    # The document is now indexed through the same path the synchronous route uses.
    pages = client.get(f"/api/v1/projects/{pid}/documents/{did}/pages").json()
    assert len(pages) == 2
    doc = client.get(f"/api/v1/projects/{pid}/documents").json()[0]
    assert doc["processing_status"] == "indexed_with_text"
    assert doc["indexed_at"] is not None


def test_worker_processes_cad_parse_job_end_to_end(client: TestClient):
    pid = _create_project(client, "Worker CAD Project")
    cad_file_id = _upload_dxf(client, pid)
    job_id = _enqueue(pid, job_handlers.JOB_CAD_PARSE, {"cad_file_id": cad_file_id})

    processed = _drain()
    assert processed >= 1

    snap = _snapshot(job_id, pid)
    assert snap is not None
    assert snap["status"] == job_queue_service.STATUS_SUCCEEDED
    assert snap["result"]["cad_file_id"] == cad_file_id
    assert snap["result"]["status"] in {"completed", "completed_with_warnings"}

    # A parse run row now records the extracted review-support metadata.
    db = SessionLocal()
    try:
        runs = (
            db.execute(
                select(models.CadParseRun).where(
                    models.CadParseRun.cad_file_id == cad_file_id
                )
            )
            .scalars()
            .all()
        )
        assert runs
    finally:
        db.close()
    context = client.get(f"/api/v1/cad-files/{cad_file_id}/review-context").json()
    assert context["cad_file"]["upload_status"] == "parsed"


def test_worker_fails_cad_parse_for_missing_file_permanently(client: TestClient):
    pid = _create_project(client, "Worker Missing CAD Project")
    job_id = _enqueue(
        pid,
        job_handlers.JOB_CAD_PARSE,
        {"cad_file_id": "cad_does_not_exist"},
    )
    _drain()

    snap = _snapshot(job_id, pid)
    assert snap is not None
    # A missing record is a permanent fault: no retry, so a single attempt only.
    assert snap["status"] == job_queue_service.STATUS_FAILED
    assert snap["attempts"] == 1
    assert snap["error"]


def test_worker_retries_transient_but_fails_permanent_immediately(
    client: TestClient, monkeypatch
):
    # Zero backoff so a requeued transient job is due again within one drain pass.
    monkeypatch.setattr(get_settings(), "WORKER_RETRY_BACKOFF_SECONDS", 0)
    pid = "proj_worker_classify"

    transient_id = _enqueue(pid, TRANSIENT_JOB_TYPE, {"n": 1}, max_attempts=2)
    permanent_id = _enqueue(pid, PERMANENT_JOB_TYPE, {"n": 2}, max_attempts=3)

    _drain(worker_id="classify-worker")

    transient = _snapshot(transient_id, pid)
    assert transient is not None
    # A plain error is transient: the worker retried until attempts were used up.
    assert transient["status"] == job_queue_service.STATUS_FAILED
    assert transient["attempts"] == 2

    permanent = _snapshot(permanent_id, pid)
    assert permanent is not None
    # A domain error is permanent: it stops after the first attempt, no retry.
    assert permanent["status"] == job_queue_service.STATUS_FAILED
    assert permanent["attempts"] == 1
