"""Durable file storage API routes (Sprint 6).

Adds an access-controlled document download, a storage-status read, and a storage
health check. Files are stored and read through the storage provider abstraction
(local or S3-compatible). Responses never include raw filesystem paths, storage
keys, object storage credentials, or signed URLs in audit metadata. Access
control from Sprint 5 is preserved: download and storage status require project
read access; the public demo remains readable when configured.
"""

from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session

from app.db import models
from app.db.database import get_db
from app.schemas.file_storage import DocumentStorageStatus, StorageHealthResponse
from app.services.access_control_service import (
    get_current_user,
    get_optional_user,
    require_project_read,
)
from app.services.real_intake_service import record_audit_event
from app.services.storage import storage_service
from app.services.storage.base import StorageError

router = APIRouter(tags=["file-storage"])


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _require_document(
    db: Session, project_id: str, document_id: str
) -> models.Document:
    document = db.get(models.Document, document_id)
    if document is None or document.project_id != project_id:
        raise HTTPException(status_code=404, detail="Document not found")
    return document


@router.get(
    "/projects/{project_id}/documents/{document_id}/download",
)
def download_document(
    project_id: str,
    document_id: str,
    user: models.UserAccount | None = Depends(get_optional_user),
    db: Session = Depends(get_db),
) -> Response:
    actor = require_project_read(db, project_id, user)
    document = _require_document(db, project_id, document_id)

    if not storage_service.document_file_exists(document):
        record_audit_event(
            db,
            project_id=project_id,
            event_type="document_file_unavailable",
            related_entity_type="document",
            related_entity_id=document_id,
            description="A reviewer requested a file that is not available in storage.",
            actor_type="reviewer",
            actor_id=actor.user_id,
            actor_display_name=actor.display_name,
            metadata={
                "document_id": document_id,
                "storage_provider": document.storage_provider or "local",
                "status": "file_unavailable",
            },
            user_id=actor.user_id,
            user_email=actor.user_email,
            organization_id=actor.organization_id,
            access_level=actor.access_level,
        )
        document.file_available = False
        document.last_storage_check_at = _now()
        db.commit()
        raise HTTPException(
            status_code=404,
            detail="The stored file is not available. A reviewer should re-upload it.",
        )

    try:
        content = storage_service.read_document_bytes(document)
    except StorageError as exc:
        raise HTTPException(
            status_code=exc.status_code,
            detail="The stored file is not available.",
        ) from exc

    document.download_count = (document.download_count or 0) + 1
    document.last_downloaded_at = _now()
    document.last_storage_check_at = _now()
    document.file_available = True
    record_audit_event(
        db,
        project_id=project_id,
        event_type="document_downloaded",
        related_entity_type="document",
        related_entity_id=document_id,
        description=(
            f"Reviewer downloaded document "
            f"'{document.original_file_name or document.file_name}'."
        ),
        actor_type="reviewer",
        actor_id=actor.user_id,
        actor_display_name=actor.display_name,
        metadata={
            "document_id": document_id,
            "storage_provider": document.storage_provider or "local",
            "file_size_bytes": document.file_size_bytes,
            "content_type": document.content_type,
            "status": "downloaded",
        },
        user_id=actor.user_id,
        user_email=actor.user_email,
        organization_id=actor.organization_id,
        access_level=actor.access_level,
    )
    db.commit()

    media_type = document.content_type or "application/octet-stream"
    safe_name = document.original_file_name or document.file_name or "download"
    return Response(
        content=content,
        media_type=media_type,
        headers={
            "Content-Disposition": f'attachment; filename="{safe_name}"',
        },
    )


@router.get(
    "/projects/{project_id}/documents/{document_id}/storage-status",
    response_model=DocumentStorageStatus,
)
def document_storage_status(
    project_id: str,
    document_id: str,
    user: models.UserAccount | None = Depends(get_optional_user),
    db: Session = Depends(get_db),
) -> DocumentStorageStatus:
    require_project_read(db, project_id, user)
    document = _require_document(db, project_id, document_id)

    available = storage_service.document_file_exists(document)
    document.file_available = available
    document.last_storage_check_at = _now()
    db.commit()

    message = None
    if not available:
        message = (
            "The file is not available in storage. Upload or re-upload a file to "
            "make it retrieval ready."
        )
    return DocumentStorageStatus(
        document_id=document.document_id,
        project_id=document.project_id,
        file_available=available,
        storage_provider=document.storage_provider,
        processing_status=document.processing_status,
        upload_status=document.upload_status,
        content_type=document.content_type,
        file_size_bytes=document.file_size_bytes,
        checksum_sha256=document.checksum_sha256,
        original_file_name=document.original_file_name,
        uploaded_at=document.uploaded_at,
        last_storage_check_at=document.last_storage_check_at,
        download_count=document.download_count or 0,
        last_downloaded_at=document.last_downloaded_at,
        message=message,
    )


@router.get("/storage/health", response_model=StorageHealthResponse)
def storage_health(
    user: models.UserAccount = Depends(get_current_user),
) -> StorageHealthResponse:
    info = storage_service.storage_health()
    return StorageHealthResponse(
        provider=info.get("provider", "unknown"),
        configured=bool(info.get("configured")),
        detail=(
            "Local development storage is configured."
            if info.get("provider") == "local"
            else "Object storage configuration was checked."
        ),
    )
