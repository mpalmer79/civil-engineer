"""Upload create, validate, and save orchestration for CAD (DXF) intake.

Registers bundled sample DXF fixtures and browser-uploaded DXF files. Uploaded
files are validated (extension, size, content type, readability), stored under a
safe generated file name (never the raw user file name), and registered as a CAD
file. DXF is the only supported file type in this phase; DWG parsing is out of
scope.
"""

from __future__ import annotations

from pathlib import Path

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.safety import (
    ALLOWED_CAD_VALIDATION_STATUSES,
    ALLOWED_CAD_QUEUE_STATUSES,
)
from app.db import models
from app.services.cad_intake_service._common import _audit, _short
from app.services.cad_intake_service.errors import CadIntakeError, LIMITATIONS_NOTE

# Supported upload surface for this phase. DXF only; DWG parsing is future work.
SUPPORTED_UPLOAD_EXTENSIONS: set[str] = {".dxf"}
# DXF files are sent by browsers with a wide range of content types (or none at
# all). We accept the common DXF media types plus generic binary and text types,
# and rely on extension and the DXF readability check as authoritative. Clearly
# wrong types (for example application/pdf) are rejected.
DXF_CONTENT_TYPES: set[str] = {
    "application/dxf",
    "application/x-dxf",
    "image/vnd.dxf",
    "image/x-dxf",
    "application/x-autocad",
    "text/plain",
}
GENERIC_CONTENT_TYPES: set[str] = {
    "",
    "application/octet-stream",
    "binary/octet-stream",
}
ALLOWED_UPLOAD_CONTENT_TYPES: set[str] = DXF_CONTENT_TYPES | GENERIC_CONTENT_TYPES

# The bundled fixtures live at app/cad_samples. This module sits one package
# level deeper than the historical single-file module, so the sample directory
# is resolved three parents up (uploads.py -> cad_intake_service -> services ->
# app) to keep the same resolved path.
SAMPLE_DIR = Path(__file__).resolve().parent.parent.parent / "cad_samples"
# Whitelisted bundled sample DXF fixtures. The client selects a sample by key so
# no arbitrary filesystem path is read. Browser upload is a later enhancement.
SAMPLE_DXF_FILES: dict[str, Path] = {
    "brookside_meadows": SAMPLE_DIR / "brookside_meadows.dxf",
    # Phase 13 resubmittal (round 2) revision of the Brookside Meadows sample,
    # used by the revision comparison demo and tests.
    "brookside_meadows_r2": SAMPLE_DIR / "brookside_meadows_r2.dxf",
}


def create_cad_file_upload(
    db: Session,
    *,
    project_id: str,
    file_name: str,
    file_type: str,
    file_size_bytes: int,
    storage_path: str,
    uploaded_by: str,
    original_file_name: str | None = None,
    stored_file_name: str | None = None,
    content_type: str | None = None,
    upload_source: str = "sample",
    validation_status: str = "accepted",
    validation_message: str = "DXF registered for review-support parsing.",
    max_file_size_bytes: int | None = None,
) -> models.CadFileUpload:
    """Register a CAD file record. Only the dxf file type is accepted."""

    if db.get(models.Project, project_id) is None:
        raise CadIntakeError("Project not found.", status_code=404)
    if file_type != "dxf":
        raise CadIntakeError(
            "Only DXF files are supported in this phase. DWG parsing is future "
            "work.",
            status_code=422,
        )

    upload_status = (
        "needs_human_review"
        if validation_status == "needs_human_review"
        else "uploaded"
    )
    cad_file = models.CadFileUpload(
        cad_file_id=f"cad_{_short()}",
        project_id=project_id,
        file_name=file_name,
        file_type=file_type,
        file_size_bytes=file_size_bytes,
        storage_path=storage_path,
        upload_status=upload_status,
        uploaded_by=uploaded_by,
        limitations_note=LIMITATIONS_NOTE,
        original_file_name=original_file_name or file_name,
        stored_file_name=stored_file_name or file_name,
        content_type=content_type,
        upload_source=upload_source,
        validation_status=validation_status,
        validation_message=validation_message,
        max_file_size_bytes=(
            max_file_size_bytes
            if max_file_size_bytes is not None
            else get_settings().CAD_MAX_UPLOAD_BYTES
        ),
    )
    db.add(cad_file)
    _audit(
        db,
        project_id=project_id,
        event_type="cad_file_created",
        related_entity_type="cad_file",
        related_entity_id=cad_file.cad_file_id,
        description=f"CAD file record created for {file_name}.",
        metadata={
            "cad_file_id": cad_file.cad_file_id,
            "file_type": file_type,
            "upload_source": upload_source,
            "validation_status": validation_status,
        },
    )
    db.commit()
    db.refresh(cad_file)
    return cad_file


def create_cad_file_from_sample(
    db: Session,
    *,
    project_id: str,
    sample_key: str = "brookside_meadows",
    uploaded_by: str = "reviewer",
) -> models.CadFileUpload:
    """Register a bundled sample DXF fixture as a CAD file for intake.

    The sample is resolved from a whitelist so no arbitrary path is read.
    """

    path = SAMPLE_DXF_FILES.get(sample_key)
    if path is None or not path.exists():
        raise CadIntakeError(
            f"Unknown sample DXF '{sample_key}'.", status_code=404
        )
    return create_cad_file_upload(
        db,
        project_id=project_id,
        file_name=path.name,
        file_type="dxf",
        file_size_bytes=path.stat().st_size,
        storage_path=str(path),
        uploaded_by=uploaded_by,
    )


def get_cad_upload_limits() -> dict:
    """Return the documented browser DXF upload limits and validation rules."""

    settings = get_settings()
    max_bytes = settings.CAD_MAX_UPLOAD_BYTES
    return {
        "supported_extensions": sorted(SUPPORTED_UPLOAD_EXTENSIONS),
        "supported_file_types": ["dxf"],
        "max_file_size_bytes": max_bytes,
        "max_file_size_mb": round(max_bytes / 1_000_000, 2),
        "allowed_validation_statuses": sorted(ALLOWED_CAD_VALIDATION_STATUSES),
        "allowed_queue_statuses": sorted(ALLOWED_CAD_QUEUE_STATUSES),
        "note": (
            "DXF is the only supported file type. Uploaded files are stored "
            "under a safe generated file name and parsed for review-support "
            "metadata only. Upload does not verify CAD, validate geometry or "
            "design, certify compliance, or replace a licensed Professional "
            "Engineer."
        ),
    }


def validate_cad_upload_file(
    *,
    file_name: str | None,
    content_type: str | None,
    size_bytes: int,
    content_bytes: bytes | None = None,
) -> tuple[str, str]:
    """Validate a browser DXF upload.

    Returns a (validation_status, validation_message) pair. validation_status is
    one of accepted, rejected, or needs_human_review. The file name is used only
    to read the extension; it never affects where the file is stored. These
    checks are review-support intake checks, not an engineering determination.
    """

    extension = Path(file_name or "").suffix.lower()
    if extension not in SUPPORTED_UPLOAD_EXTENSIONS:
        return (
            "rejected",
            (
                f"Unsupported file extension '{extension or '(none)'}'. Only "
                "DXF files are supported in this phase. DWG parsing is future "
                "work."
            ),
        )
    if size_bytes <= 0:
        return ("rejected", "The uploaded file is empty (zero bytes).")
    max_bytes = get_settings().CAD_MAX_UPLOAD_BYTES
    if size_bytes > max_bytes:
        return (
            "rejected",
            (
                f"The uploaded file is {size_bytes} bytes, which exceeds the "
                f"{max_bytes} byte limit."
            ),
        )
    normalized_type = (content_type or "").strip().lower()
    if normalized_type and normalized_type not in ALLOWED_UPLOAD_CONTENT_TYPES:
        return (
            "rejected",
            (
                f"Unsupported content type '{content_type}'. Upload a DXF file."
            ),
        )
    if content_bytes is not None:
        text = content_bytes.decode("utf-8", errors="ignore").upper()
        if "SECTION" not in text or "EOF" not in text:
            return (
                "needs_human_review",
                (
                    "The file was stored but does not look like a readable DXF "
                    "text file. A reviewer should confirm it before parsing."
                ),
            )
    return (
        "accepted",
        "DXF upload accepted for review-support parsing.",
    )


def save_uploaded_dxf_file(
    *, content_bytes: bytes, project_id: str
) -> tuple[str, str]:
    """Write uploaded bytes to disk under a safe generated file name.

    The stored file name is generated and never derived from the user file name,
    which prevents path traversal. Returns (stored_file_name, storage_path).
    """

    settings = get_settings()
    # Resolve the per-project upload directory under the configured root. Both
    # parts are server controlled, so no user input reaches the path.
    upload_root = Path(settings.CAD_UPLOAD_DIR).resolve()
    project_dir = upload_root / project_id
    project_dir.mkdir(parents=True, exist_ok=True)
    stored_file_name = f"cad_{_short()}.dxf"
    storage_path = project_dir / stored_file_name
    storage_path.write_bytes(content_bytes)
    return stored_file_name, str(storage_path)


def create_cad_file_from_upload(
    db: Session,
    *,
    project_id: str,
    original_file_name: str | None,
    content_type: str | None,
    content_bytes: bytes,
    uploaded_by: str = "reviewer",
) -> models.CadFileUpload:
    """Validate, store, and register a browser-uploaded DXF file.

    Rejected uploads raise CadIntakeError and are not stored. Accepted and
    needs_human_review uploads are stored under a safe generated file name and
    registered. Writes a cad_upload_accepted or cad_upload_rejected audit event.
    """

    if db.get(models.Project, project_id) is None:
        raise CadIntakeError("Project not found.", status_code=404)

    size_bytes = len(content_bytes)
    validation_status, validation_message = validate_cad_upload_file(
        file_name=original_file_name,
        content_type=content_type,
        size_bytes=size_bytes,
        content_bytes=content_bytes,
    )
    # Keep only the base name as metadata. Any directory components in the user
    # file name (for example a path traversal attempt) are dropped here and never
    # reach the storage path.
    safe_original = Path(original_file_name or "uploaded.dxf").name

    if validation_status == "rejected":
        _audit(
            db,
            project_id=project_id,
            event_type="cad_upload_rejected",
            related_entity_type="cad_file",
            related_entity_id=project_id,
            description=f"DXF upload rejected: {validation_message}",
            actor_type="reviewer",
            metadata={
                "original_file_name": safe_original,
                "validation_status": validation_status,
                "size_bytes": size_bytes,
            },
        )
        db.commit()
        raise CadIntakeError(validation_message, status_code=422)

    stored_file_name, storage_path = save_uploaded_dxf_file(
        content_bytes=content_bytes, project_id=project_id
    )
    cad_file = create_cad_file_upload(
        db,
        project_id=project_id,
        file_name=safe_original,
        file_type="dxf",
        file_size_bytes=size_bytes,
        storage_path=storage_path,
        uploaded_by=uploaded_by,
        original_file_name=safe_original,
        stored_file_name=stored_file_name,
        content_type=content_type,
        upload_source="browser_upload",
        validation_status=validation_status,
        validation_message=validation_message,
    )
    _audit(
        db,
        project_id=project_id,
        event_type="cad_upload_accepted",
        related_entity_type="cad_file",
        related_entity_id=cad_file.cad_file_id,
        description=(
            f"DXF upload {validation_status} for {safe_original}."
        ),
        actor_type="reviewer",
        metadata={
            "cad_file_id": cad_file.cad_file_id,
            "validation_status": validation_status,
            "stored_file_name": stored_file_name,
        },
    )
    db.commit()
    db.refresh(cad_file)
    return cad_file
