"""Background processing job API routes.

These endpoints let a caller schedule file processing on the background worker
instead of the request thread, then poll for the outcome. They are additive: the
existing synchronous index and parse routes are unchanged and remain the default
for small, interactive files. The async routes are the path for large files and
higher load, and require the worker process to be running.

Authorization mirrors the synchronous routes exactly: enqueuing requires
reviewer access to the project, and reading a job requires project read access.
Job reads are scoped to the project so one tenant cannot see another's jobs.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db import models
from app.db.database import get_db
from app.schemas.jobs import JobResponse

# Importing job_handlers registers the handlers so enqueue accepts these types.
from app.services import cad_intake_service, job_handlers, job_queue_service
from app.services.access_control_service import (
    get_optional_user,
    require_project_read,
    require_project_reviewer,
)

router = APIRouter(tags=["jobs"])

_ = job_handlers.register_all


def _handle(exc: Exception) -> HTTPException:
    status_code = getattr(exc, "status_code", 400)
    message = getattr(exc, "message", str(exc))
    return HTTPException(status_code=status_code, detail=message)


@router.post(
    "/projects/{project_id}/documents/{document_id}/index-pdf/jobs",
    response_model=JobResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
def enqueue_pdf_index_job(
    project_id: str,
    document_id: str,
    user: models.UserAccount | None = Depends(get_optional_user),
    db: Session = Depends(get_db),
) -> JobResponse:
    """Schedule PDF indexing for a document on the background worker."""

    actor = require_project_reviewer(db, project_id, user)
    try:
        job = job_queue_service.enqueue(
            db,
            job_type=job_handlers.JOB_PDF_INDEX,
            project_id=project_id,
            payload={
                "project_id": project_id,
                "document_id": document_id,
                "actor_name": actor.display_name,
            },
        )
    except job_queue_service.JobQueueError as exc:
        raise _handle(exc) from exc
    return JobResponse.model_validate(job)


@router.post(
    "/cad-files/{cad_file_id}/parse/jobs",
    response_model=JobResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
def enqueue_cad_parse_job(
    cad_file_id: str,
    user: models.UserAccount | None = Depends(get_optional_user),
    db: Session = Depends(get_db),
) -> JobResponse:
    """Schedule DXF parsing for a CAD file on the background worker."""

    cad_file = cad_intake_service.get_cad_file(db, cad_file_id)
    if cad_file is None:
        raise HTTPException(status_code=404, detail="CAD file not found.")
    require_project_reviewer(db, cad_file.project_id, user)
    try:
        job = job_queue_service.enqueue(
            db,
            job_type=job_handlers.JOB_CAD_PARSE,
            project_id=cad_file.project_id,
            payload={"cad_file_id": cad_file_id},
        )
    except job_queue_service.JobQueueError as exc:
        raise _handle(exc) from exc
    return JobResponse.model_validate(job)


@router.get(
    "/projects/{project_id}/jobs/{job_id}",
    response_model=JobResponse,
)
def get_job(
    project_id: str,
    job_id: str,
    user: models.UserAccount | None = Depends(get_optional_user),
    db: Session = Depends(get_db),
) -> JobResponse:
    """Return one job's status, scoped to the project."""

    require_project_read(db, project_id, user)
    job = job_queue_service.get_job(db, job_id=job_id, project_id=project_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found.")
    return JobResponse.model_validate(job)


@router.get(
    "/projects/{project_id}/jobs",
    response_model=list[JobResponse],
)
def list_jobs(
    project_id: str,
    user: models.UserAccount | None = Depends(get_optional_user),
    db: Session = Depends(get_db),
) -> list[JobResponse]:
    """Return recent jobs for a project, newest first."""

    require_project_read(db, project_id, user)
    jobs = job_queue_service.list_jobs(db, project_id=project_id)
    return [JobResponse.model_validate(job) for job in jobs]
