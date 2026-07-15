"""Tests for the background processing job API routes.

These tests exercise the async enqueue routes through the TestClient, drain the
queue with the worker, and read job status back through the API. They confirm the
routes are additive: the existing synchronous index route still works, job reads
are scoped to a project so one tenant cannot see another's jobs, and enqueuing
requires reviewer access when login is required for real projects.

The lifecycle words queued, running, succeeded, and failed are the queue's own
status vocabulary. A failed job is a technical processing outcome, not an
engineering judgment about a project or a design.
"""

from __future__ import annotations

import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import update

from app.core import request_context
from app.core.config import get_settings
from app.db import models
from app.db.database import SessionLocal
from app.db.models.shared import _utcnow
from app.services import job_queue_service
from app import worker
from tests.test_pdf_indexing import _create_project, _make_pdf, _upload_pdf

SAMPLE_DXF = (
    __import__("pathlib").Path(__file__).resolve().parent.parent
    / "app"
    / "cad_samples"
    / "brookside_meadows.dxf"
)


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


@pytest.fixture
def strict_login():
    """Require login for real projects for the duration of a test."""

    settings = get_settings()
    old = settings.AUTH_REQUIRE_LOGIN_FOR_REAL_PROJECTS
    settings.AUTH_REQUIRE_LOGIN_FOR_REAL_PROJECTS = True
    yield
    settings.AUTH_REQUIRE_LOGIN_FOR_REAL_PROJECTS = old


def _headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def _register(client: TestClient) -> dict:
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": f"async_{uuid.uuid4().hex[:10]}@example.com",
            "password": "password123",
            "display_name": "Async Reviewer",
            "organization_name": None,
        },
    )
    assert response.status_code == 201, response.text
    return response.json()


def _create_project_with_token(
    client: TestClient, token: str, name: str = "Async Auth Jobs Project"
) -> str:
    response = client.post(
        "/api/v1/projects",
        headers=_headers(token),
        json={
            "project_name": name,
            "project_type": "Subdivision",
            "jurisdiction": "Town",
            "review_type": "Review",
            "review_domain": "stormwater",
            "location_context": "Parcel",
        },
    )
    assert response.status_code == 201, response.text
    return response.json()["project_id"]


def _upload_dxf(client: TestClient, project_id: str, file_name: str = "api.dxf") -> str:
    response = client.post(
        f"/api/v1/projects/{project_id}/cad-files/upload",
        files={"file": (file_name, SAMPLE_DXF.read_bytes(), "application/dxf")},
        data={"uploaded_by": "Town Engineer"},
    )
    assert response.status_code == 200, response.text
    return response.json()["cad_file"]["cad_file_id"]


def _drain(worker_id: str = "test-api-worker") -> int:
    db = SessionLocal()
    try:
        return worker.process_available_jobs(db, worker_id=worker_id, limit=100)
    finally:
        db.close()


def test_enqueue_pdf_index_job_returns_202_and_processes(client: TestClient):
    pid = _create_project(client, "Async PDF Jobs Project")
    did = _upload_pdf(client, pid, _make_pdf(["Async page one", "Async page two"]))

    response = client.post(
        f"/api/v1/projects/{pid}/documents/{did}/index-pdf/jobs"
    )
    assert response.status_code == 202, response.text
    body = response.json()
    assert body["job_id"].startswith("job_")
    assert body["status"] == "queued"
    assert body["job_type"] == "pdf_index"

    _drain()

    status = client.get(f"/api/v1/projects/{pid}/jobs/{body['job_id']}")
    assert status.status_code == 200
    assert status.json()["status"] == "succeeded"
    assert status.json()["result"]["processing_status"] == "indexed_with_text"


def test_enqueue_cad_parse_job_returns_202(client: TestClient):
    pid = _create_project(client, "Async CAD Jobs Project")
    cad_file_id = _upload_dxf(client, pid)

    response = client.post(f"/api/v1/cad-files/{cad_file_id}/parse/jobs")
    assert response.status_code == 202, response.text
    body = response.json()
    assert body["status"] == "queued"
    assert body["job_type"] == "cad_parse"
    assert body["project_id"] == pid


def test_enqueue_cad_parse_job_missing_file_returns_404(client: TestClient):
    response = client.post("/api/v1/cad-files/cad_does_not_exist/parse/jobs")
    assert response.status_code == 404


def test_list_jobs_returns_enqueued_job(client: TestClient):
    pid = _create_project(client, "Async List Jobs Project")
    did = _upload_pdf(client, pid, _make_pdf(["List page"]))
    enqueue = client.post(
        f"/api/v1/projects/{pid}/documents/{did}/index-pdf/jobs"
    )
    job_id = enqueue.json()["job_id"]

    listed = client.get(f"/api/v1/projects/{pid}/jobs")
    assert listed.status_code == 200
    ids = [job["job_id"] for job in listed.json()]
    assert job_id in ids


def test_get_job_under_other_project_returns_404(client: TestClient):
    pid = _create_project(client, "Async Tenant Jobs Project")
    other = _create_project(client, "Async Tenant Other Project")
    did = _upload_pdf(client, pid, _make_pdf(["Tenant page"]))
    job_id = client.post(
        f"/api/v1/projects/{pid}/documents/{did}/index-pdf/jobs"
    ).json()["job_id"]

    # The job belongs to pid; reading it scoped to another project must 404.
    response = client.get(f"/api/v1/projects/{other}/jobs/{job_id}")
    assert response.status_code == 404


def test_enqueue_pdf_index_job_requires_reviewer(client: TestClient, strict_login):
    owner = _register(client)
    pid = _create_project_with_token(client, owner["access_token"])

    # Without a login the reviewer requirement rejects the enqueue request.
    anon = client.post(f"/api/v1/projects/{pid}/documents/doc_any/index-pdf/jobs")
    assert anon.status_code == 401

    # The project owner holds reviewer access and the job is accepted.
    ok = client.post(
        f"/api/v1/projects/{pid}/documents/doc_any/index-pdf/jobs",
        headers=_headers(owner["access_token"]),
    )
    assert ok.status_code == 202
    assert ok.json()["status"] == "queued"


def test_synchronous_index_pdf_still_works(client: TestClient):
    pid = _create_project(client, "Async Sync Sanity Project")
    did = _upload_pdf(client, pid, _make_pdf(["Sync page one"]))
    response = client.post(f"/api/v1/projects/{pid}/documents/{did}/index-pdf")
    assert response.status_code == 200, response.text
    assert response.json()["processing_status"] == "indexed_with_text"
