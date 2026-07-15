"""Document registration, upload, validation, and safe storage.

Registration records intake metadata; upload validates and stores a real file
under a safe generated file name. These are review-support intake steps and
never imply approval or an engineering determination.
"""

from __future__ import annotations

import hashlib
from pathlib import Path

from sqlalchemy.orm import Session

from app.core.safety import reject_prohibited_language
from app.db import models
from app.services import real_intake_service as _intake_pkg
from app.services.auth_service import ActorContext, audit_kwargs
from app.services.real_intake_service._common import (
    DEMO_ACTOR_NAME,
    _now,
    _require_project,
    _short,
    ensure_demo_actor,
    record_audit_event,
)
from app.services.real_intake_service.errors import IntakeError
from app.services.storage import storage_service
from app.services.storage.base import StorageError


def register_document(
    db: Session,
    *,
    project_id: str,
    original_file_name: str,
    document_type: str,
    purpose: str | None = None,
    expected_key_information: str | None = None,
    content_type: str | None = None,
    file_size_bytes: int | None = None,
    revision_label: str | None = None,
    revision_date: str | None = None,
    uploaded_by_name: str = DEMO_ACTOR_NAME,
) -> models.Document:
    """Register document metadata for a project and emit a document_registered
    event. Registration records intake metadata; it never implies approval."""

    project = _require_project(db, project_id)
    if not (original_file_name or "").strip():
        raise IntakeError("original_file_name is required.", status_code=422)
    reject_prohibited_language(document_type, field="document_type")

    # Enforce the per-organization document limit before any mutation, when
    # enforcement is enabled. A no-op for the demo org and in advisory mode.
    from app.services import usage_service

    usage_service.check_limit(
        db,
        category="document_uploaded",
        organization_id=project.organization_id,
    )
    reject_prohibited_language(purpose, field="purpose")

    ensure_demo_actor(db)
    now = _now()
    safe_name = Path(original_file_name).name
    document_id = f"doc_user_{_short()}"
    document = models.Document(
        document_id=document_id,
        project_id=project_id,
        file_name=safe_name,
        original_file_name=safe_name,
        document_type=(document_type or "other").strip() or "other",
        status="registered",
        purpose=(purpose or "").strip(),
        expected_key_information=(expected_key_information or "").strip(),
        intentionally_missing_or_conflicting_information=None,
        source_mode="user_registered",
        upload_status="not_uploaded",
        processing_status="metadata_recorded",
        content_type=content_type,
        file_size_bytes=file_size_bytes,
        revision_label=revision_label,
        revision_date=revision_date,
        uploaded_by_name=uploaded_by_name,
        registered_at=now,
        is_superseded=False,
    )
    db.add(document)
    record_audit_event(
        db,
        project_id=project_id,
        event_type="document_registered",
        related_entity_type="document",
        related_entity_id=document_id,
        description=(
            f"Reviewer registered document '{safe_name}' "
            f"({document.document_type})."
        ),
        actor_type="reviewer",
        actor_display_name=uploaded_by_name,
        metadata={
            "source_mode": "user_registered",
            "processing_status": "metadata_recorded",
            "revision_label": revision_label,
        },
    )
    # Record advisory usage for the registered document (best-effort, skips the
    # demo organization, never blocks registration).
    from app.services import usage_service

    usage_service.record_usage_safe(
        db,
        category="document_uploaded",
        organization_id=project.organization_id,
        project_id=project_id,
    )
    db.commit()
    db.refresh(document)
    return document


def upload_document(
    db: Session,
    *,
    project_id: str,
    original_file_name: str | None,
    content_type: str | None,
    content_bytes: bytes,
    document_type: str = "other",
    purpose: str | None = None,
    revision_label: str | None = None,
    uploaded_by_name: str = DEMO_ACTOR_NAME,
    actor: ActorContext | None = None,
) -> models.Document:
    """Validate, store, and register a real uploaded document file.

    Storage uses a safe generated file name (never the raw user file name).
    A sha256 checksum is computed and stored. The raw bytes are not parsed in
    this sprint. Rejected uploads raise IntakeError and write a
    document_upload_rejected audit event without storing the file.
    """

    _require_project(db, project_id)
    ensure_demo_actor(db)
    if actor is not None:
        uploaded_by_name = actor.display_name
    reject_prohibited_language(document_type, field="document_type")

    size_bytes = len(content_bytes)
    safe_name = Path(original_file_name or "uploaded").name
    error = validate_project_upload(
        file_name=original_file_name, size_bytes=size_bytes
    )
    if error is not None:
        record_audit_event(
            db,
            project_id=project_id,
            event_type="document_upload_rejected",
            related_entity_type="document",
            related_entity_id=project_id,
            description=f"Document upload rejected: {error}",
            actor_type="reviewer",
            actor_display_name=uploaded_by_name,
            metadata={
                "original_file_name": safe_name,
                "size_bytes": size_bytes,
            },
        )
        db.commit()
        raise IntakeError(error, status_code=422)

    checksum = hashlib.sha256(content_bytes).hexdigest()
    now = _now()
    document_id = f"doc_user_{_short()}"

    record_audit_event(
        db,
        **audit_kwargs(actor),
        project_id=project_id,
        event_type="document_upload_started",
        related_entity_type="document",
        related_entity_id=document_id,
        description=f"Reviewer started upload of '{safe_name}'.",
        actor_type="reviewer",
        actor_display_name=uploaded_by_name,
        metadata={"size_bytes": size_bytes},
    )

    # Store the file through the configured storage provider (local or S3). Only
    # a safe, generated storage key is recorded; the raw filesystem path and any
    # object storage credentials are never stored on the document or in audit
    # metadata.
    try:
        stored = storage_service.save_document_file(
            project_id=project_id,
            document_id=document_id,
            original_filename=safe_name,
            content_bytes=content_bytes,
            content_type=content_type,
        )
    except StorageError as exc:
        record_audit_event(
            db,
            **audit_kwargs(actor),
            project_id=project_id,
            event_type="document_storage_failed",
            related_entity_type="document",
            related_entity_id=document_id,
            description="Document storage failed.",
            actor_type="reviewer",
            actor_display_name=uploaded_by_name,
            metadata={"size_bytes": size_bytes, "status": "storage_failed"},
        )
        db.commit()
        raise IntakeError(
            "The uploaded file could not be stored. A reviewer should retry.",
            status_code=502,
        ) from exc

    document = models.Document(
        document_id=document_id,
        project_id=project_id,
        file_name=f"doc_{_short()}{Path(safe_name).suffix.lower()}",
        original_file_name=safe_name,
        document_type=(document_type or "other").strip() or "other",
        status="uploaded",
        purpose=(purpose or "").strip(),
        expected_key_information="",
        intentionally_missing_or_conflicting_information=None,
        source_mode="user_uploaded",
        upload_status="stored",
        processing_status="parsing_not_available",
        storage_provider=stored.provider,
        storage_key=stored.storage_key,
        storage_bucket=stored.bucket,
        storage_etag=stored.etag,
        storage_version_id=stored.version_id,
        file_available=True,
        last_storage_check_at=now,
        content_type=content_type,
        file_size_bytes=size_bytes,
        checksum_sha256=checksum,
        revision_label=revision_label,
        uploaded_by_name=uploaded_by_name,
        uploaded_at=now,
        registered_at=now,
        is_superseded=False,
    )
    db.add(document)
    record_audit_event(
        db,
        **audit_kwargs(actor),
        project_id=project_id,
        event_type="document_stored",
        related_entity_type="document",
        related_entity_id=document_id,
        description=(
            f"Reviewer uploaded document '{safe_name}' "
            f"({size_bytes} bytes), stored via {stored.provider}."
        ),
        actor_type="reviewer",
        actor_display_name=uploaded_by_name,
        metadata={
            "source_mode": "user_uploaded",
            "storage_provider": stored.provider,
            "checksum_sha256": checksum,
            "file_size_bytes": size_bytes,
            "content_type": content_type,
            "processing_status": "parsing_not_available",
            "status": "stored",
        },
    )
    db.commit()
    db.refresh(document)
    return document


def validate_project_upload(
    *, file_name: str | None, size_bytes: int
) -> str | None:
    """Return an error message if the upload is not allowed, else None.

    Checks extension against the configured allow-list and size against the
    configured maximum. These are review-support intake checks, never an
    engineering determination.
    """

    settings = _intake_pkg.get_settings()
    extension = Path(file_name or "").suffix.lower()
    allowed = settings.allowed_project_upload_extensions_set
    if extension not in allowed:
        return (
            f"Unsupported file extension '{extension or '(none)'}'. Allowed "
            f"types: {', '.join(sorted(allowed))}."
        )
    if size_bytes <= 0:
        return "The uploaded file is empty (zero bytes)."
    max_bytes = settings.MAX_PROJECT_UPLOAD_BYTES
    if size_bytes > max_bytes:
        return (
            f"The uploaded file is {size_bytes} bytes, which exceeds the "
            f"{max_bytes} byte limit."
        )
    return None


def save_uploaded_project_file(
    *, content_bytes: bytes, project_id: str, original_file_name: str
) -> tuple[str, str]:
    """Write uploaded bytes to disk under a safe generated file name.

    The stored file name is generated and preserves only the validated
    extension. It is never derived from the user file name, which prevents
    path traversal. Returns (stored_file_name, storage_path).
    """

    settings = _intake_pkg.get_settings()
    upload_root = Path(settings.PROJECT_UPLOAD_DIR).resolve()
    project_dir = upload_root / project_id
    project_dir.mkdir(parents=True, exist_ok=True)
    extension = Path(original_file_name).suffix.lower()
    stored_file_name = f"doc_{_short()}{extension}"
    storage_path = project_dir / stored_file_name
    storage_path.write_bytes(content_bytes)
    return stored_file_name, str(storage_path)
