"""Real CAD (DXF) intake and parsing service.

This service registers a real DXF file, parses it with the ezdxf library, and
extracts review-support metadata: layers, entities, blocks, text, reference
candidates, and review-support findings. It compares extracted sheet and detail
references against the seeded Phase 6 plan sheets and raises review-support
findings when a reference has no match, a detail reference is ambiguous, a basin
label may conflict, or a layer cannot be categorized.

Phase 12 adds browser DXF upload, intake validation, a manual parse queue, a CAD
intake dashboard, and promotion of selected CAD findings into the workflow board.
Uploaded files are validated (extension, size, content type, readability), stored
under a safe generated file name (never the raw user file name), and registered
as a CAD file. Parse is triggered manually; there is no background worker.

Parsing extracts metadata from a real DXF file. It does not verify CAD, validate
geometry or design, certify compliance, or make final engineering decisions. DXF
is the only supported file type in this phase; DWG parsing is out of scope. There
is no action called approve. A parse queue status of "failed" means the parser
could not read the file (a technical parse failure), not an engineering failure.

Read side effects: get_cad_parse_summary, list_cad_layers, list_cad_text,
get_cad_file_review_context, get_cad_parse_queue, get_cad_intake_dashboard, and
list_unpromoted_cad_findings each write an audit event recording the access. This
is intentional so the decision history shows reviewer access.
"""

from __future__ import annotations

import re
import uuid
from datetime import datetime, timezone
from pathlib import Path

import ezdxf
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.safety import (
    ALLOWED_CAD_VALIDATION_STATUSES,
    ALLOWED_CAD_QUEUE_STATUSES,
)
from app.db import models
from app.services import plan_sheet_service, workflow_service
from app.services.cad import facility_identity, geometry, layer_taxonomy
from app.services.cad import reference_parser

PARSER_NAME = "ezdxf"
PARSER_VERSION = ezdxf.__version__

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

SAMPLE_DIR = Path(__file__).resolve().parent.parent / "cad_samples"
# Whitelisted bundled sample DXF fixtures. The client selects a sample by key so
# no arbitrary filesystem path is read. Browser upload is a later enhancement.
SAMPLE_DXF_FILES: dict[str, Path] = {
    "brookside_meadows": SAMPLE_DIR / "brookside_meadows.dxf",
    # Phase 13 resubmittal (round 2) revision of the Brookside Meadows sample,
    # used by the revision comparison demo and tests.
    "brookside_meadows_r2": SAMPLE_DIR / "brookside_meadows_r2.dxf",
}

LIMITATIONS_NOTE = (
    "DXF metadata extraction for review support only. It does not verify CAD, "
    "validate geometry or design, certify compliance, stamp drawings, or "
    "replace a licensed Professional Engineer."
)

CONTEXT_NOTE = (
    "This is extracted DXF review-support metadata, not a verification or "
    "validation of the CAD file or the design."
)

# Layer classification is delegated to the data-driven taxonomy in
# app.services.cad.layer_taxonomy. NEUTRAL_LAYERS is re-exported for callers
# that referenced it here.
NEUTRAL_LAYERS = layer_taxonomy.NEUTRAL_LAYERS

PIPE_RE = re.compile(r"\bP-\d+\b")
OUTFALL_RE = re.compile(r"\bOF-\d+\b")

# Safety limits for pathological files. Entities beyond the cap are counted
# but not persisted; a parse warning records the truncation. Text values are
# truncated to the maximum length. Partial parsing is allowed and visible.
MAX_PERSISTED_ENTITIES = 100_000
MAX_TEXT_VALUE_LENGTH = 2_000
MAX_LAYER_COUNT = 5_000


class CadIntakeError(Exception):
    """Raised when a CAD intake operation is not allowed."""

    def __init__(self, message: str, *, status_code: int = 400) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _short() -> str:
    return uuid.uuid4().hex[:12]


def _audit(
    db: Session,
    *,
    project_id: str,
    event_type: str,
    related_entity_type: str,
    related_entity_id: str,
    description: str,
    actor_type: str = "system",
    metadata: dict | None = None,
) -> None:
    db.add(
        models.AuditEvent(
            audit_event_id=f"audit_cad_{uuid.uuid4().hex[:12]}",
            project_id=project_id,
            event_type=event_type,
            actor_type=actor_type,
            related_entity_type=related_entity_type,
            related_entity_id=related_entity_id,
            description=description,
            timestamp=_now(),
            event_metadata=metadata or {},
        )
    )


def _layer_category(layer_name: str) -> str:
    return layer_taxonomy.layer_category(layer_name)


def _normalize(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "").strip().upper())


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


def request_cad_parse(db: Session, cad_file_id: str) -> models.CadParseRun:
    """Record a manual parse request for an uploaded DXF file and parse it.

    Parsing runs inline (there is no background worker). Sets parse_requested_at
    and parse_completed_at on the CAD file and writes a cad_parse_requested audit
    event in addition to the parse run's own audit events.
    """

    cad_file = get_cad_file(db, cad_file_id)
    if cad_file is None:
        raise CadIntakeError("CAD file not found.", status_code=404)

    cad_file.parse_requested_at = _now()
    _audit(
        db,
        project_id=cad_file.project_id,
        event_type="cad_parse_requested",
        related_entity_type="cad_file",
        related_entity_id=cad_file_id,
        description=f"Parse requested for {cad_file.file_name}.",
        actor_type="reviewer",
        metadata={"cad_file_id": cad_file_id},
    )
    db.commit()

    run = parse_dxf_file(db, cad_file_id)

    cad_file.parse_completed_at = _now()
    db.commit()
    db.refresh(run)
    return run


def get_cad_file(db: Session, cad_file_id: str) -> models.CadFileUpload | None:
    return db.scalars(
        select(models.CadFileUpload).where(
            models.CadFileUpload.cad_file_id == cad_file_id
        )
    ).first()


def list_cad_files(db: Session, project_id: str) -> list[models.CadFileUpload]:
    return list(
        db.scalars(
            select(models.CadFileUpload)
            .where(models.CadFileUpload.project_id == project_id)
            .order_by(models.CadFileUpload.created_at.desc())
        ).all()
    )


def get_cad_parse_run(db: Session, parse_run_id: str) -> models.CadParseRun | None:
    return db.scalars(
        select(models.CadParseRun).where(
            models.CadParseRun.parse_run_id == parse_run_id
        )
    ).first()


def list_cad_parse_runs(db: Session, project_id: str) -> list[models.CadParseRun]:
    return list(
        db.scalars(
            select(models.CadParseRun)
            .where(models.CadParseRun.project_id == project_id)
            .order_by(models.CadParseRun.started_at.desc())
        ).all()
    )


def list_cad_layers(
    db: Session, parse_run_id: str, *, audit: bool = True
) -> list[models.CadLayerExtract]:
    layers = list(
        db.scalars(
            select(models.CadLayerExtract)
            .where(models.CadLayerExtract.parse_run_id == parse_run_id)
            .order_by(models.CadLayerExtract.layer_name)
        ).all()
    )
    if audit and layers:
        run = get_cad_parse_run(db, parse_run_id)
        if run is not None:
            _audit(
                db,
                project_id=run.project_id,
                event_type="cad_layers_viewed",
                related_entity_type="cad_parse_run",
                related_entity_id=parse_run_id,
                description="CAD parse run layers viewed.",
                actor_type="reviewer",
                metadata={"parse_run_id": parse_run_id, "layer_count": len(layers)},
            )
            db.commit()
    return layers


def list_cad_entities(
    db: Session, parse_run_id: str
) -> list[models.CadEntityExtract]:
    return list(
        db.scalars(
            select(models.CadEntityExtract)
            .where(models.CadEntityExtract.parse_run_id == parse_run_id)
            .order_by(models.CadEntityExtract.id)
        ).all()
    )


def list_cad_blocks(db: Session, parse_run_id: str) -> list[models.CadBlockExtract]:
    return list(
        db.scalars(
            select(models.CadBlockExtract)
            .where(models.CadBlockExtract.parse_run_id == parse_run_id)
            .order_by(models.CadBlockExtract.block_name)
        ).all()
    )


def list_cad_text(
    db: Session, parse_run_id: str, *, audit: bool = True
) -> list[models.CadTextExtract]:
    texts = list(
        db.scalars(
            select(models.CadTextExtract)
            .where(models.CadTextExtract.parse_run_id == parse_run_id)
            .order_by(models.CadTextExtract.id)
        ).all()
    )
    if audit and texts:
        run = get_cad_parse_run(db, parse_run_id)
        if run is not None:
            _audit(
                db,
                project_id=run.project_id,
                event_type="cad_text_viewed",
                related_entity_type="cad_parse_run",
                related_entity_id=parse_run_id,
                description="CAD parse run text extracts viewed.",
                actor_type="reviewer",
                metadata={"parse_run_id": parse_run_id, "text_count": len(texts)},
            )
            db.commit()
    return texts


def list_cad_reference_candidates(
    db: Session, parse_run_id: str
) -> list[models.CadReferenceCandidate]:
    return list(
        db.scalars(
            select(models.CadReferenceCandidate)
            .where(models.CadReferenceCandidate.parse_run_id == parse_run_id)
            .order_by(models.CadReferenceCandidate.id)
        ).all()
    )


def list_cad_review_findings(
    db: Session, project_id: str
) -> list[models.CadReviewFinding]:
    return list(
        db.scalars(
            select(models.CadReviewFinding)
            .where(models.CadReviewFinding.project_id == project_id)
            .order_by(models.CadReviewFinding.created_at)
        ).all()
    )


def _entity_bounds(entity) -> tuple | None:
    """Return (x_min, y_min, x_max, y_max) in local drawing coordinates when a
    safe bound exists, else None. These are not georeferenced coordinates.
    Delegates to the geometry module, which covers polylines, arcs, circles,
    ellipses, splines, points, inserts, hatches, and dimensions and never
    fabricates coordinates for unsupported entities."""

    return geometry.entity_bounds(entity).bounds


def _entity_text(entity) -> str | None:
    try:
        dxftype = entity.dxftype()
        if dxftype == "MTEXT":
            return entity.plain_text()
        if dxftype == "TEXT":
            return entity.dxf.text
    except Exception:
        return None
    return None


def _classify_reference_type(normalized: str) -> str:
    if "WETLAND BUFFER" in normalized:
        return "wetland_buffer_label"
    if normalized.startswith("REV"):
        return "revision_note"
    parsed = reference_parser.parse_references(normalized)
    if any(p.reference_type == "detail_reference" for p in parsed):
        return "detail_reference"
    if "OUTFALL" in normalized or OUTFALL_RE.search(normalized):
        return "outfall_label"
    if (
        facility_identity.parse_facility_label(normalized) is not None
        and "SHEET" not in normalized
        and "SEE" not in normalized
    ):
        return "basin_label"
    if any(p.reference_type == "sheet_reference" for p in parsed):
        return "sheet_reference"
    if PIPE_RE.search(normalized):
        return "pipe_label"
    return "general_note"


def _seeded_sheet_map(db: Session, project_id: str) -> dict[str, str]:
    return {
        _normalize(s.sheet_number): s.sheet_id
        for s in plan_sheet_service.list_plan_sheets(db, project_id)
    }


def parse_dxf_file(db: Session, cad_file_id: str) -> models.CadParseRun:
    """Parse a registered DXF file and extract review-support metadata.

    Creates a parse run, layer, entity, block, and text extracts, reference
    candidates matched against seeded plan sheets, and review-support findings.
    Writes cad_parse_started and cad_parse_completed (or cad_parse_failed) audit
    events.
    """

    cad_file = get_cad_file(db, cad_file_id)
    if cad_file is None:
        raise CadIntakeError("CAD file not found.", status_code=404)

    run = models.CadParseRun(
        parse_run_id=f"cadrun_{_short()}",
        cad_file_id=cad_file_id,
        project_id=cad_file.project_id,
        parser_name=PARSER_NAME,
        parser_version=PARSER_VERSION,
        status="started",
        entity_count=0,
        layer_count=0,
        block_count=0,
        text_count=0,
        warning_count=0,
        limitations_note=LIMITATIONS_NOTE,
    )
    db.add(run)
    _audit(
        db,
        project_id=cad_file.project_id,
        event_type="cad_parse_started",
        related_entity_type="cad_parse_run",
        related_entity_id=run.parse_run_id,
        description=f"DXF parse started for {cad_file.file_name}.",
        metadata={"parse_run_id": run.parse_run_id, "cad_file_id": cad_file_id},
    )
    db.commit()

    try:
        doc = ezdxf.readfile(cad_file.storage_path)
    except (OSError, ezdxf.DXFError) as exc:
        run.status = "failed"
        run.completed_at = _now()
        run.error_message = f"DXF parse failed: {exc}"
        cad_file.upload_status = "parse_failed"
        _audit(
            db,
            project_id=cad_file.project_id,
            event_type="cad_parse_failed",
            related_entity_type="cad_parse_run",
            related_entity_id=run.parse_run_id,
            description="DXF parse failed.",
            metadata={"parse_run_id": run.parse_run_id, "error": str(exc)},
        )
        db.commit()
        db.refresh(run)
        return run

    msp = doc.modelspace()
    project_id = cad_file.project_id

    # Audit the DXF (ezdxf structural check) for warning counts only.
    warning_count = 0
    try:
        auditor = doc.audit()
        warning_count = len(auditor.errors) + len(auditor.fixes)
    except Exception:
        warning_count = 0

    # Layers.
    entities_by_layer: dict[str, list] = {}
    for entity in msp:
        entities_by_layer.setdefault(getattr(entity.dxf, "layer", "0"), []).append(
            entity
        )

    layer_extract_by_name: dict[str, models.CadLayerExtract] = {}
    layer_count = 0
    for layer in doc.layers:
        if layer_count >= MAX_LAYER_COUNT:
            # Pathological layer tables stop persisting here; the count so
            # far is kept and parsing continues.
            break
        name = layer.dxf.name
        members = entities_by_layer.get(name, [])
        has_text = any(e.dxftype() in {"TEXT", "MTEXT"} for e in members)
        has_geometry = any(e.dxftype() not in {"TEXT", "MTEXT"} for e in members)
        category = _layer_category(name)
        layer_extract = models.CadLayerExtract(
            layer_extract_id=f"cadlyr_{_short()}",
            parse_run_id=run.parse_run_id,
            cad_file_id=cad_file_id,
            project_id=project_id,
            layer_name=name,
            entity_count=len(members),
            has_text=has_text,
            has_geometry=has_geometry,
            review_category=category,
            requires_human_review=category == "unknown",
        )
        db.add(layer_extract)
        layer_extract_by_name[name] = layer_extract
        layer_count += 1

    # Entities and text. Entities beyond MAX_PERSISTED_ENTITIES are counted
    # but not persisted (graceful partial result); a parse warning finding
    # records the truncation below.
    entity_count = 0
    text_count = 0
    persisted_truncated = False
    text_extracts: list[models.CadTextExtract] = []
    for entity in msp:
        entity_count += 1
        if entity_count > MAX_PERSISTED_ENTITIES:
            persisted_truncated = True
            continue
        layer_name = getattr(entity.dxf, "layer", None)
        category = _layer_category(layer_name or "")
        bounds = _entity_bounds(entity)
        text_value = _entity_text(entity)
        if text_value and len(text_value) > MAX_TEXT_VALUE_LENGTH:
            text_value = text_value[:MAX_TEXT_VALUE_LENGTH]
        handle = getattr(entity.dxf, "handle", None)
        db.add(
            models.CadEntityExtract(
                entity_extract_id=f"caden_{_short()}",
                parse_run_id=run.parse_run_id,
                cad_file_id=cad_file_id,
                project_id=project_id,
                entity_type=entity.dxftype(),
                layer_name=layer_name,
                block_name=entity.dxf.name if entity.dxftype() == "INSERT" else None,
                handle=str(handle) if handle is not None else None,
                text_value=text_value,
                x_min=bounds[0] if bounds else None,
                y_min=bounds[1] if bounds else None,
                x_max=bounds[2] if bounds else None,
                y_max=bounds[3] if bounds else None,
                review_category=category,
                requires_human_review=category == "unknown",
            )
        )
        if text_value:
            text_count += 1
            normalized = _normalize(text_value)
            reference_type = _classify_reference_type(normalized)
            point = None
            try:
                point = entity.dxf.insert
            except Exception:
                point = None
            text_extract = models.CadTextExtract(
                text_extract_id=f"cadtxt_{_short()}",
                parse_run_id=run.parse_run_id,
                cad_file_id=cad_file_id,
                project_id=project_id,
                text_value=text_value,
                normalized_text=normalized,
                entity_type=entity.dxftype(),
                layer_name=layer_name,
                block_name=None,
                handle=str(handle) if handle is not None else None,
                x=float(point[0]) if point is not None else None,
                y=float(point[1]) if point is not None else None,
                review_category=category,
                reference_type=reference_type,
                requires_human_review=reference_type in {"unknown", "general_note"}
                or category == "unknown",
            )
            db.add(text_extract)
            text_extracts.append(text_extract)

    # Blocks.
    block_count = 0
    insert_counts: dict[str, int] = {}
    for entity in msp:
        if entity.dxftype() == "INSERT":
            insert_counts[entity.dxf.name] = insert_counts.get(entity.dxf.name, 0) + 1
    for block in doc.blocks:
        if block.name.startswith("*"):
            continue
        block_texts: list[str] = []
        block_layers: set[str] = set()
        for entity in block:
            block_layers.add(getattr(entity.dxf, "layer", "0"))
            value = _entity_text(entity)
            if value:
                block_texts.append(value)
        category = "titleblock" if "TITLE" in block.name.upper() else "unknown"
        db.add(
            models.CadBlockExtract(
                block_extract_id=f"cadblk_{_short()}",
                parse_run_id=run.parse_run_id,
                cad_file_id=cad_file_id,
                project_id=project_id,
                block_name=block.name,
                insert_count=insert_counts.get(block.name, 0),
                layer_names=sorted(block_layers),
                text_values=block_texts,
                review_category=category,
                requires_human_review=category == "unknown",
            )
        )
        block_count += 1

    db.flush()

    # Reference candidates and findings.
    sheet_map = _seeded_sheet_map(db, project_id)
    _build_reference_candidates(db, run, text_extracts, sheet_map)
    _build_layer_findings(db, run, list(layer_extract_by_name.values()))

    run.entity_count = entity_count
    run.layer_count = layer_count
    run.block_count = block_count
    run.text_count = text_count
    run.warning_count = warning_count
    run.completed_at = _now()
    run.status = "completed_with_warnings" if warning_count else "completed"
    cad_file.upload_status = "parsed"

    if persisted_truncated:
        _create_finding(
            db,
            run=run,
            finding_type="parse_warning",
            title="Entity inventory truncated at the persistence limit",
            description=(
                f"The drawing contains {entity_count} model-space entities, "
                f"above the {MAX_PERSISTED_ENTITIES} persistence limit. All "
                "entities were counted; entities beyond the limit were not "
                "stored individually. This is a partial parse for reviewer "
                "awareness."
            ),
            severity="low",
        )

    if warning_count:
        _create_finding(
            db,
            run=run,
            finding_type="parse_warning",
            title="DXF structural warnings detected",
            description=(
                f"The DXF audit reported {warning_count} structural item(s). "
                "Review the source file for completeness."
            ),
            severity="low",
        )

    # Drawing units and a paper-space inventory travel in the audit metadata.
    # Per-entity space tagging is future work; model space is the parsed
    # surface and paper-space content is inventoried here so titleblock
    # references are not counted as site geometry.
    units = geometry.drawing_units(doc)
    paperspace_counts: dict[str, int] = {}
    try:
        for layout in doc.layouts:
            if layout.name == "Model":
                continue
            paperspace_counts[layout.name] = len(list(layout))
    except Exception:
        paperspace_counts = {}

    _audit(
        db,
        project_id=project_id,
        event_type="cad_parse_completed",
        related_entity_type="cad_parse_run",
        related_entity_id=run.parse_run_id,
        description=(
            f"DXF parse completed with {entity_count} entities, {layer_count} "
            f"layers, {text_count} text values."
        ),
        metadata={
            "parse_run_id": run.parse_run_id,
            "entity_count": entity_count,
            "layer_count": layer_count,
            "text_count": text_count,
            "block_count": block_count,
            "warning_count": warning_count,
            "drawing_units": units.name,
            "drawing_units_code": units.insunits_code,
            "drawing_units_confidence": units.confidence,
            "paperspace_entity_counts": paperspace_counts,
            "persisted_entity_truncation": persisted_truncated,
        },
    )
    db.commit()
    db.refresh(run)
    return run


def _create_finding(
    db: Session,
    *,
    run: models.CadParseRun,
    finding_type: str,
    title: str,
    description: str,
    severity: str,
    source_reference_candidate_id: str | None = None,
    source_layer_extract_id: str | None = None,
    source_text_extract_id: str | None = None,
    linked_plan_sheet_id: str | None = None,
) -> models.CadReviewFinding:
    finding = models.CadReviewFinding(
        cad_review_finding_id=f"cadfind_{_short()}",
        parse_run_id=run.parse_run_id,
        cad_file_id=run.cad_file_id,
        project_id=run.project_id,
        finding_type=finding_type,
        title=title,
        description=description,
        severity=severity,
        source_reference_candidate_id=source_reference_candidate_id,
        source_layer_extract_id=source_layer_extract_id,
        source_text_extract_id=source_text_extract_id,
        linked_plan_sheet_id=linked_plan_sheet_id,
        status="draft",
        requires_human_review=True,
    )
    db.add(finding)
    _audit(
        db,
        project_id=run.project_id,
        event_type="cad_review_finding_created",
        related_entity_type="cad_review_finding",
        related_entity_id=finding.cad_review_finding_id,
        description=f"CAD review finding created: {finding_type}.",
        metadata={
            "cad_review_finding_id": finding.cad_review_finding_id,
            "finding_type": finding_type,
        },
    )
    return finding


def _build_reference_candidates(
    db: Session,
    run: models.CadParseRun,
    text_extracts: list[models.CadTextExtract],
    sheet_map: dict[str, str],
) -> None:
    basin_labels: list[tuple[str, models.CadTextExtract]] = []

    for text in text_extracts:
        normalized = text.normalized_text
        parsed = reference_parser.parse_references(normalized)

        for reference in parsed:
            if reference.reference_type == "detail_reference":
                sheet_token = reference.sheet_token
                matched_id = sheet_map.get(sheet_token)
                if reference.ambiguous:
                    confidence = "needs_human_review"
                    reason = (
                        reference.ambiguity_reason
                        or "Detail or sheet token is ambiguous and needs "
                        "human review."
                    )
                elif matched_id:
                    confidence = "high"
                    reason = (
                        f"Detail sheet {sheet_token} matches a seeded plan "
                        "sheet."
                    )
                else:
                    confidence = "low"
                    reason = (
                        f"Detail sheet {sheet_token} has no matching seeded "
                        "plan sheet."
                    )
                candidate = _add_candidate(
                    db,
                    run=run,
                    reference_text=reference.normalized_reference,
                    normalized_reference=sheet_token,
                    reference_type="detail_reference",
                    source_text=text,
                    matched_plan_sheet_id=None if reference.ambiguous else matched_id,
                    confidence_label=confidence,
                    match_reason=reason,
                )
                if reference.ambiguous:
                    _create_finding(
                        db,
                        run=run,
                        finding_type="unclear_detail_reference",
                        title=(
                            "Unclear detail reference: "
                            f"{reference.normalized_reference}"
                        ),
                        description=(
                            "The detail reference could not be resolved and "
                            "needs human review."
                        ),
                        severity="medium",
                        source_reference_candidate_id=candidate.candidate_id,
                        source_text_extract_id=text.text_extract_id,
                    )
                elif not matched_id:
                    _create_finding(
                        db,
                        run=run,
                        finding_type="missing_plan_sheet_match",
                        title=f"Detail references missing sheet {sheet_token}",
                        description=(
                            f"Sheet {sheet_token} referenced by a detail "
                            "callout has no matching seeded plan sheet."
                        ),
                        severity="medium",
                        source_reference_candidate_id=candidate.candidate_id,
                        source_text_extract_id=text.text_extract_id,
                    )
            else:
                sheet_token = reference.sheet_token
                matched_id = (
                    None if reference.ambiguous else sheet_map.get(sheet_token)
                )
                if reference.ambiguous:
                    confidence = "needs_human_review"
                    reason = (
                        reference.ambiguity_reason
                        or f"Sheet {sheet_token} is ambiguous."
                    )
                elif matched_id:
                    confidence = "high"
                    reason = f"Sheet {sheet_token} matches seeded plan sheet."
                else:
                    confidence = "needs_human_review"
                    reason = (
                        f"Sheet {sheet_token} has no matching seeded plan "
                        "sheet."
                    )
                candidate = _add_candidate(
                    db,
                    run=run,
                    reference_text=reference.raw_text,
                    normalized_reference=sheet_token,
                    reference_type="sheet_reference",
                    source_text=text,
                    matched_plan_sheet_id=matched_id,
                    confidence_label=confidence,
                    match_reason=reason,
                )
                if not matched_id and not reference.ambiguous:
                    _create_finding(
                        db,
                        run=run,
                        finding_type="missing_plan_sheet_match",
                        title=(
                            f"Referenced sheet {sheet_token} has no plan "
                            "sheet match"
                        ),
                        description=(
                            f"The DXF references sheet {sheet_token}, which "
                            "has no matching seeded plan sheet. Reviewer "
                            "confirmation needed."
                        ),
                        severity="medium",
                        source_reference_candidate_id=candidate.candidate_id,
                        source_text_extract_id=text.text_extract_id,
                    )

        if parsed:
            continue

        if text.reference_type == "basin_label":
            candidate = _add_candidate(
                db,
                run=run,
                reference_text=text.text_value,
                normalized_reference=normalized,
                reference_type="basin_label",
                source_text=text,
                matched_plan_sheet_id=None,
                confidence_label="medium",
                match_reason="Basin label extracted for reviewer confirmation.",
            )
            basin_labels.append((normalized, text))
        elif text.reference_type in {
            "pipe_label",
            "outfall_label",
            "wetland_buffer_label",
            "revision_note",
        }:
            _add_candidate(
                db,
                run=run,
                reference_text=text.text_value,
                normalized_reference=normalized,
                reference_type=text.reference_type,
                source_text=text,
                matched_plan_sheet_id=None,
                confidence_label="medium",
                match_reason=f"{text.reference_type.replace('_', ' ')} extracted "
                "for reviewer confirmation.",
            )

    _detect_basin_conflicts(db, run, basin_labels)


def _add_candidate(
    db: Session,
    *,
    run: models.CadParseRun,
    reference_text: str,
    normalized_reference: str,
    reference_type: str,
    source_text: models.CadTextExtract,
    matched_plan_sheet_id: str | None,
    confidence_label: str,
    match_reason: str,
) -> models.CadReferenceCandidate:
    candidate = models.CadReferenceCandidate(
        candidate_id=f"cadref_{_short()}",
        parse_run_id=run.parse_run_id,
        cad_file_id=run.cad_file_id,
        project_id=run.project_id,
        reference_text=reference_text,
        normalized_reference=normalized_reference,
        reference_type=reference_type,
        source_entity_id=None,
        source_text_id=source_text.text_extract_id,
        matched_plan_sheet_id=matched_plan_sheet_id,
        matched_plan_reference_id=None,
        confidence_label=confidence_label,
        match_reason=match_reason,
        requires_human_review=confidence_label in {"low", "needs_human_review"},
    )
    db.add(candidate)
    return candidate


def _detect_basin_conflicts(
    db: Session,
    run: models.CadParseRun,
    basin_labels: list[tuple[str, models.CadTextExtract]],
) -> None:
    """Raise possible naming inconsistencies between facility labels.

    Uses structured facility identities so different facility types that share
    a number (DETENTION BASIN 1 and INFILTRATION BASIN 1) are never flagged as
    the same facility. Each finding names both labels, the rule, and why the
    labels may refer to the same facility. These are possible naming
    inconsistencies that need reviewer confirmation, never confirmed design
    conflicts.
    """

    identities: list[facility_identity.FacilityIdentity] = []
    source_by_label: dict[str, models.CadTextExtract] = {}
    for normalized, text in basin_labels:
        location = None
        if text.x is not None and text.y is not None:
            location = (text.x, text.y)
        identity = facility_identity.parse_facility_label(
            normalized, location=location
        )
        if identity is None:
            continue
        identities.append(identity)
        source_by_label.setdefault(identity.normalized_label, text)

    for conflict in facility_identity.detect_facility_conflicts(identities):
        joined = ", ".join(conflict.labels)
        sample_text = source_by_label.get(conflict.labels[0])
        _create_finding(
            db,
            run=run,
            finding_type="possible_label_conflict",
            title=(
                "Possible facility naming inconsistency for "
                f"'{conflict.identifier or joined}'"
            ),
            description=(
                f"Labels: {joined}. {conflict.reason} Matching rule: "
                f"{conflict.rule}. Confidence: {conflict.confidence}."
            ),
            severity="medium",
            source_text_extract_id=(
                sample_text.text_extract_id if sample_text else None
            ),
        )


def _build_layer_findings(
    db: Session, run: models.CadParseRun, layers: list[models.CadLayerExtract]
) -> None:
    for layer in layers:
        if layer.review_category != "unknown":
            continue
        if layer.entity_count == 0:
            continue
        if layer.layer_name.upper() in NEUTRAL_LAYERS:
            continue
        _create_finding(
            db,
            run=run,
            finding_type="unknown_layer_category",
            title=f"Layer '{layer.layer_name}' could not be categorized",
            description=(
                f"Layer '{layer.layer_name}' has {layer.entity_count} entities "
                "but no recognized review category. Reviewer categorization "
                "needed."
            ),
            severity="low",
            source_layer_extract_id=layer.layer_extract_id,
        )


def get_cad_parse_summary(
    db: Session, parse_run_id: str, *, audit: bool = True
) -> dict | None:
    run = get_cad_parse_run(db, parse_run_id)
    if run is None:
        return None
    layers = list_cad_layers(db, parse_run_id, audit=False)
    candidates = list_cad_reference_candidates(db, parse_run_id)
    findings = list(
        db.scalars(
            select(models.CadReviewFinding).where(
                models.CadReviewFinding.parse_run_id == parse_run_id
            )
        ).all()
    )

    layers_by_category: dict[str, int] = {}
    for layer in layers:
        layers_by_category[layer.review_category] = (
            layers_by_category.get(layer.review_category, 0) + 1
        )
    references_by_type: dict[str, int] = {}
    references_by_confidence: dict[str, int] = {}
    for candidate in candidates:
        references_by_type[candidate.reference_type] = (
            references_by_type.get(candidate.reference_type, 0) + 1
        )
        references_by_confidence[candidate.confidence_label] = (
            references_by_confidence.get(candidate.confidence_label, 0) + 1
        )
    findings_by_type: dict[str, int] = {}
    for finding in findings:
        findings_by_type[finding.finding_type] = (
            findings_by_type.get(finding.finding_type, 0) + 1
        )

    if audit:
        _audit(
            db,
            project_id=run.project_id,
            event_type="cad_parse_summary_viewed",
            related_entity_type="cad_parse_run",
            related_entity_id=parse_run_id,
            description="CAD parse summary viewed.",
            actor_type="reviewer",
            metadata={"parse_run_id": parse_run_id},
        )
        db.commit()

    return {
        "parse_run_id": parse_run_id,
        "cad_file_id": run.cad_file_id,
        "project_id": run.project_id,
        "status": run.status,
        "entity_count": run.entity_count,
        "layer_count": run.layer_count,
        "block_count": run.block_count,
        "text_count": run.text_count,
        "warning_count": run.warning_count,
        "reference_candidate_count": len(candidates),
        "finding_count": len(findings),
        "layers_by_category": layers_by_category,
        "references_by_type": references_by_type,
        "references_by_confidence": references_by_confidence,
        "findings_by_type": findings_by_type,
        "limitations_note": run.limitations_note,
    }


def compare_cad_references_to_plan_sheets(
    db: Session, parse_run_id: str
) -> dict | None:
    """Compare extracted sheet and detail references to seeded plan sheets.

    Recomputes matches against the current plan sheets, ensures a missing-match
    finding exists for each unmatched sheet or detail reference (idempotent), and
    returns the comparison view. Writes a cad_reference_comparison_run audit
    event.
    """

    run = get_cad_parse_run(db, parse_run_id)
    if run is None:
        return None
    sheet_map = _seeded_sheet_map(db, run.project_id)
    sheet_number_by_id = {
        s.sheet_id: s.sheet_number
        for s in plan_sheet_service.list_plan_sheets(db, run.project_id)
    }
    candidates = [
        c
        for c in list_cad_reference_candidates(db, parse_run_id)
        if c.reference_type in {"sheet_reference", "detail_reference"}
    ]
    # Any candidate that already has a finding (from parse time or a prior
    # comparison) is skipped, so a comparison never double-flags a reference.
    existing_finding_candidate_ids = {
        f.source_reference_candidate_id
        for f in db.scalars(
            select(models.CadReviewFinding).where(
                models.CadReviewFinding.parse_run_id == parse_run_id
            )
        ).all()
        if f.source_reference_candidate_id is not None
    }

    rows = []
    matched_count = 0
    new_findings: list[models.CadReviewFinding] = []
    for candidate in candidates:
        matched_id = sheet_map.get(candidate.normalized_reference)
        candidate.matched_plan_sheet_id = matched_id
        if matched_id:
            matched_count += 1
            candidate.confidence_label = "high"
            candidate.match_reason = (
                f"{candidate.normalized_reference} matches seeded plan sheet."
            )
            candidate.requires_human_review = False
        else:
            if candidate.confidence_label != "needs_human_review":
                candidate.confidence_label = "low"
            candidate.requires_human_review = True
            if candidate.candidate_id not in existing_finding_candidate_ids:
                new_findings.append(
                    _create_finding(
                        db,
                        run=run,
                        finding_type="missing_plan_sheet_match",
                        title=(
                            f"Reference {candidate.reference_text} has no plan "
                            "sheet match"
                        ),
                        description=(
                            f"Reference {candidate.reference_text} has no matching "
                            "seeded plan sheet. Reviewer confirmation needed."
                        ),
                        severity="medium",
                        source_reference_candidate_id=candidate.candidate_id,
                    )
                )
        rows.append(
            {
                "candidate_id": candidate.candidate_id,
                "reference_text": candidate.reference_text,
                "normalized_reference": candidate.normalized_reference,
                "reference_type": candidate.reference_type,
                "matched_plan_sheet_id": matched_id,
                "matched_sheet_number": sheet_number_by_id.get(matched_id)
                if matched_id
                else None,
                "confidence_label": candidate.confidence_label,
                "match_reason": candidate.match_reason,
            }
        )

    all_findings = list(
        db.scalars(
            select(models.CadReviewFinding).where(
                models.CadReviewFinding.parse_run_id == parse_run_id
            )
        ).all()
    )

    _audit(
        db,
        project_id=run.project_id,
        event_type="cad_reference_comparison_run",
        related_entity_type="cad_parse_run",
        related_entity_id=parse_run_id,
        description="CAD reference comparison to plan sheets run.",
        actor_type="reviewer",
        metadata={
            "parse_run_id": parse_run_id,
            "matched_count": matched_count,
            "unmatched_count": len(candidates) - matched_count,
        },
    )
    db.commit()

    return {
        "parse_run_id": parse_run_id,
        "project_id": run.project_id,
        "total_candidates": len(candidates),
        "matched_count": matched_count,
        "unmatched_count": len(candidates) - matched_count,
        "rows": rows,
        "findings": all_findings,
        "note": CONTEXT_NOTE,
    }


def create_workflow_items_from_cad_findings(
    db: Session, project_id: str
) -> dict:
    """Create workflow board items from CAD review findings that need tracking.

    Idempotent per finding: a finding already linked to a workflow item is
    skipped. Writes a cad_workflow_items_created audit event.
    """

    if db.get(models.Project, project_id) is None:
        raise CadIntakeError("Project not found.", status_code=404)

    workflow_service.ensure_workflow_board(db, project_id)
    findings = [
        f
        for f in list_cad_review_findings(db, project_id)
        if f.linked_workflow_item_id is None
        and f.status not in {"excluded_from_packet"}
    ]
    created_ids: list[str] = []
    for finding in findings:
        item = models.WorkflowItem(
            workflow_item_id=f"wfi_{_short()}",
            project_id=project_id,
            packet_id=None,
            packet_item_id=None,
            title=finding.title,
            description=finding.description,
            source_type="cad_review_finding",
            source_id=finding.cad_review_finding_id,
            severity=finding.severity,
            status="draft",
            assigned_role="plan_reviewer",
            reviewer_note=None,
            target_date=None,
            section_type="plan_sheet_cad",
            evidence_types=["cad_file"],
            requires_human_review=True,
        )
        db.add(item)
        finding.linked_workflow_item_id = item.workflow_item_id
        finding.promoted_to_workflow = True
        finding.promoted_workflow_item_id = item.workflow_item_id
        created_ids.append(item.workflow_item_id)

    _audit(
        db,
        project_id=project_id,
        event_type="cad_workflow_items_created",
        related_entity_type="workflow_board",
        related_entity_id=project_id,
        description=f"{len(created_ids)} workflow items created from CAD findings.",
        metadata={"created_count": len(created_ids)},
    )
    db.commit()
    return {
        "created_count": len(created_ids),
        "workflow_item_ids": created_ids,
        "note": (
            "Workflow items created from CAD review findings. Each needs human "
            "review and does not approve, certify, or validate anything."
        ),
    }


def get_cad_file_review_context(db: Session, cad_file_id: str) -> dict | None:
    """Return the CAD file with its latest parse run, summary, and findings.

    Read side effect: writes a cad_review_context_viewed audit event.
    """

    cad_file = get_cad_file(db, cad_file_id)
    if cad_file is None:
        return None
    run = db.scalars(
        select(models.CadParseRun)
        .where(models.CadParseRun.cad_file_id == cad_file_id)
        .order_by(models.CadParseRun.started_at.desc())
    ).first()

    summary = None
    layers: list = []
    candidates: list = []
    findings: list = []
    if run is not None:
        summary = get_cad_parse_summary(db, run.parse_run_id, audit=False)
        layers = list_cad_layers(db, run.parse_run_id, audit=False)
        candidates = list_cad_reference_candidates(db, run.parse_run_id)
        findings = list(
            db.scalars(
                select(models.CadReviewFinding).where(
                    models.CadReviewFinding.parse_run_id == run.parse_run_id
                )
            ).all()
        )

    _audit(
        db,
        project_id=cad_file.project_id,
        event_type="cad_review_context_viewed",
        related_entity_type="cad_file",
        related_entity_id=cad_file_id,
        description="CAD file review context viewed.",
        actor_type="reviewer",
        metadata={"cad_file_id": cad_file_id},
    )
    db.commit()

    return {
        "cad_file": cad_file,
        "parse_run": run,
        "summary": summary,
        "layers": layers,
        "reference_candidates": candidates,
        "findings": findings,
        "note": CONTEXT_NOTE,
    }


def _latest_parse_run(
    db: Session, cad_file_id: str
) -> models.CadParseRun | None:
    return db.scalars(
        select(models.CadParseRun)
        .where(models.CadParseRun.cad_file_id == cad_file_id)
        .order_by(models.CadParseRun.started_at.desc())
    ).first()


def _queue_status_for(
    cad_file: models.CadFileUpload, run: models.CadParseRun | None
) -> str:
    """Derive the parse queue status for a CAD file from its latest parse run.

    A status of "failed" means the parser could not read the file (a technical
    parse failure), not an engineering failure or a final decision about the plan.
    """

    if run is None:
        if cad_file.validation_status == "needs_human_review":
            return "needs_human_review"
        return "queued"
    if run.status == "started":
        return "parsing"
    if run.status in ALLOWED_CAD_QUEUE_STATUSES:
        return run.status
    return "queued"


def get_cad_parse_queue(db: Session, project_id: str) -> list[dict]:
    """Return the parse queue for a project: one row per uploaded CAD file.

    Each row carries the upload and validation state, the derived queue status,
    and the latest parse run summary so a reviewer can see files needing parse,
    files being parsed, parse failures, and runs needing human review.

    Read side effect: writes a cad_parse_queue_viewed audit event.
    """

    if db.get(models.Project, project_id) is None:
        raise CadIntakeError("Project not found.", status_code=404)

    files = list_cad_files(db, project_id)
    rows: list[dict] = []
    for cad_file in files:
        run = _latest_parse_run(db, cad_file.cad_file_id)
        queue_status = _queue_status_for(cad_file, run)
        finding_count = 0
        if run is not None:
            finding_count = len(
                list(
                    db.scalars(
                        select(models.CadReviewFinding).where(
                            models.CadReviewFinding.parse_run_id
                            == run.parse_run_id
                        )
                    ).all()
                )
            )
        rows.append(
            {
                "cad_file_id": cad_file.cad_file_id,
                "project_id": project_id,
                "file_name": cad_file.original_file_name or cad_file.file_name,
                "upload_source": cad_file.upload_source,
                "upload_status": cad_file.upload_status,
                "validation_status": cad_file.validation_status,
                "validation_message": cad_file.validation_message,
                "queue_status": queue_status,
                "parse_run_id": run.parse_run_id if run else None,
                "parse_status": run.status if run else None,
                "warning_count": run.warning_count if run else 0,
                "error_message": run.error_message if run else None,
                "finding_count": finding_count,
                "parse_requested_at": cad_file.parse_requested_at,
                "parse_completed_at": cad_file.parse_completed_at,
                "requires_human_review": queue_status
                in {"needs_human_review", "failed"},
            }
        )

    _audit(
        db,
        project_id=project_id,
        event_type="cad_parse_queue_viewed",
        related_entity_type="project",
        related_entity_id=project_id,
        description="CAD parse queue viewed.",
        actor_type="reviewer",
        metadata={"file_count": len(rows)},
    )
    db.commit()
    return rows


def list_unpromoted_cad_findings(
    db: Session, project_id: str, *, audit: bool = True
) -> list[models.CadReviewFinding]:
    """Return CAD review findings not yet promoted to a workflow item.

    A finding is unpromoted when it has no linked workflow item and has not been
    flagged promoted. Excluded findings are skipped. Read side effect (when audit
    is True): writes a cad_unpromoted_findings_viewed audit event.
    """

    findings = [
        f
        for f in list_cad_review_findings(db, project_id)
        if f.linked_workflow_item_id is None
        and not f.promoted_to_workflow
        and f.status != "excluded_from_packet"
    ]
    if audit:
        _audit(
            db,
            project_id=project_id,
            event_type="cad_unpromoted_findings_viewed",
            related_entity_type="project",
            related_entity_id=project_id,
            description="Unpromoted CAD review findings viewed.",
            actor_type="reviewer",
            metadata={"unpromoted_count": len(findings)},
        )
        db.commit()
    return findings


def get_cad_intake_dashboard(db: Session, project_id: str) -> dict:
    """Return a CAD intake dashboard summary for a project.

    Counts uploaded files, queue statuses, validation statuses, parse runs by
    status, CAD findings, and unpromoted versus promoted findings. Read side
    effect: writes a cad_intake_dashboard_viewed audit event.
    """

    if db.get(models.Project, project_id) is None:
        raise CadIntakeError("Project not found.", status_code=404)

    files = list_cad_files(db, project_id)
    queue_status_counts: dict[str, int] = {}
    validation_status_counts: dict[str, int] = {}
    files_needing_parse = 0
    files_with_parse_failures = 0
    for cad_file in files:
        run = _latest_parse_run(db, cad_file.cad_file_id)
        queue_status = _queue_status_for(cad_file, run)
        queue_status_counts[queue_status] = (
            queue_status_counts.get(queue_status, 0) + 1
        )
        validation = cad_file.validation_status or "unknown"
        validation_status_counts[validation] = (
            validation_status_counts.get(validation, 0) + 1
        )
        if queue_status in {"queued", "needs_human_review"}:
            files_needing_parse += 1
        if queue_status == "failed":
            files_with_parse_failures += 1

    parse_runs = list_cad_parse_runs(db, project_id)
    parse_status_counts: dict[str, int] = {}
    for run in parse_runs:
        parse_status_counts[run.status] = (
            parse_status_counts.get(run.status, 0) + 1
        )
    parse_runs_needing_human_review = sum(
        1
        for run in parse_runs
        if run.status in {"needs_human_review", "failed", "completed_with_warnings"}
    )

    all_findings = list_cad_review_findings(db, project_id)
    unpromoted = [
        f
        for f in all_findings
        if f.linked_workflow_item_id is None
        and not f.promoted_to_workflow
        and f.status != "excluded_from_packet"
    ]
    promoted_count = sum(
        1
        for f in all_findings
        if f.linked_workflow_item_id is not None or f.promoted_to_workflow
    )

    _audit(
        db,
        project_id=project_id,
        event_type="cad_intake_dashboard_viewed",
        related_entity_type="project",
        related_entity_id=project_id,
        description="CAD intake dashboard viewed.",
        actor_type="reviewer",
        metadata={"file_count": len(files)},
    )
    db.commit()

    return {
        "project_id": project_id,
        "total_files": len(files),
        "files_needing_parse": files_needing_parse,
        "files_with_parse_failures": files_with_parse_failures,
        "parse_runs_needing_human_review": parse_runs_needing_human_review,
        "total_findings": len(all_findings),
        "unpromoted_findings_count": len(unpromoted),
        "promoted_findings_count": promoted_count,
        "queue_status_counts": queue_status_counts,
        "validation_status_counts": validation_status_counts,
        "parse_status_counts": parse_status_counts,
        "limitations_note": LIMITATIONS_NOTE,
    }


def _build_workflow_item_from_finding(
    finding: models.CadReviewFinding, reviewer_note: str | None
) -> models.WorkflowItem:
    return models.WorkflowItem(
        workflow_item_id=f"wfi_{_short()}",
        project_id=finding.project_id,
        packet_id=None,
        packet_item_id=None,
        title=finding.title,
        description=finding.description,
        source_type="cad_review_finding",
        source_id=finding.cad_review_finding_id,
        severity=finding.severity,
        status="draft",
        assigned_role="plan_reviewer",
        reviewer_note=reviewer_note or None,
        target_date=None,
        section_type="plan_sheet_cad",
        evidence_types=["cad_file"],
        requires_human_review=True,
    )


def promote_cad_finding_to_workflow(
    db: Session,
    cad_review_finding_id: str,
    *,
    reviewer_name: str = "reviewer",
    reviewer_note: str | None = None,
    commit: bool = True,
) -> dict:
    """Promote a single CAD review finding into a workflow board item.

    Idempotent: a finding already linked to a workflow item is not promoted
    again, which prevents duplicate workflow items from the same CAD finding.
    Writes a cad_finding_promoted audit event when a new item is created.
    """

    finding = db.scalars(
        select(models.CadReviewFinding).where(
            models.CadReviewFinding.cad_review_finding_id == cad_review_finding_id
        )
    ).first()
    if finding is None:
        raise CadIntakeError("CAD review finding not found.", status_code=404)

    workflow_service.ensure_workflow_board(db, finding.project_id)

    if finding.linked_workflow_item_id is not None or finding.promoted_to_workflow:
        return {
            "cad_review_finding_id": cad_review_finding_id,
            "workflow_item_id": finding.linked_workflow_item_id
            or finding.promoted_workflow_item_id,
            "created": False,
            "already_promoted": True,
            "note": (
                "This CAD finding is already promoted to a workflow item. No "
                "duplicate workflow item was created."
            ),
        }

    item = _build_workflow_item_from_finding(finding, reviewer_note)
    db.add(item)
    finding.linked_workflow_item_id = item.workflow_item_id
    finding.promoted_to_workflow = True
    finding.promoted_workflow_item_id = item.workflow_item_id
    _audit(
        db,
        project_id=finding.project_id,
        event_type="cad_finding_promoted",
        related_entity_type="cad_review_finding",
        related_entity_id=cad_review_finding_id,
        description=(
            f"CAD finding promoted to workflow item by {reviewer_name}."
        ),
        actor_type="reviewer",
        metadata={
            "cad_review_finding_id": cad_review_finding_id,
            "workflow_item_id": item.workflow_item_id,
        },
    )
    if commit:
        db.commit()
    return {
        "cad_review_finding_id": cad_review_finding_id,
        "workflow_item_id": item.workflow_item_id,
        "created": True,
        "already_promoted": False,
        "note": (
            "Workflow item created from CAD review finding. It needs human "
            "review and does not approve, certify, or validate anything."
        ),
    }


def promote_selected_cad_findings_to_workflow(
    db: Session,
    project_id: str,
    cad_review_finding_ids: list[str],
    *,
    reviewer_name: str = "reviewer",
    reviewer_note: str | None = None,
) -> dict:
    """Promote selected CAD review findings into workflow items.

    Each finding is promoted at most once, so re-promoting an already promoted
    finding does not create a duplicate workflow item. Writes a
    cad_findings_promoted_selected audit event.
    """

    if db.get(models.Project, project_id) is None:
        raise CadIntakeError("Project not found.", status_code=404)

    results: list[dict] = []
    created_ids: list[str] = []
    created_count = 0
    already_promoted_count = 0
    not_found_count = 0
    for finding_id in cad_review_finding_ids:
        try:
            result = promote_cad_finding_to_workflow(
                db,
                finding_id,
                reviewer_name=reviewer_name,
                reviewer_note=reviewer_note,
                commit=False,
            )
        except CadIntakeError:
            not_found_count += 1
            results.append(
                {
                    "cad_review_finding_id": finding_id,
                    "workflow_item_id": None,
                    "created": False,
                    "already_promoted": False,
                    "note": "CAD review finding not found.",
                }
            )
            continue
        results.append(result)
        if result["created"]:
            created_count += 1
            if result["workflow_item_id"]:
                created_ids.append(result["workflow_item_id"])
        elif result["already_promoted"]:
            already_promoted_count += 1

    _audit(
        db,
        project_id=project_id,
        event_type="cad_findings_promoted_selected",
        related_entity_type="workflow_board",
        related_entity_id=project_id,
        description=(
            f"{created_count} workflow item(s) created from selected CAD "
            f"findings by {reviewer_name}."
        ),
        actor_type="reviewer",
        metadata={
            "requested_count": len(cad_review_finding_ids),
            "created_count": created_count,
            "already_promoted_count": already_promoted_count,
            "not_found_count": not_found_count,
        },
    )
    db.commit()
    return {
        "project_id": project_id,
        "requested_count": len(cad_review_finding_ids),
        "created_count": created_count,
        "already_promoted_count": already_promoted_count,
        "not_found_count": not_found_count,
        "workflow_item_ids": created_ids,
        "results": results,
        "note": (
            "Selected CAD findings promoted to workflow items. Each needs human "
            "review and does not approve, certify, or validate anything."
        ),
    }


def ensure_cad_intake(db: Session, project_id: str) -> None:
    """Register and parse the sample DXF once if no CAD file exists.

    Used at startup so the read endpoints and frontend have data without a
    manual call. Gated on no CAD file existing for the project.
    """

    if db.get(models.Project, project_id) is None:
        return
    existing = (
        db.query(models.CadFileUpload)
        .filter(models.CadFileUpload.project_id == project_id)
        .first()
    )
    if existing is not None:
        return
    try:
        cad_file = create_cad_file_from_sample(db, project_id=project_id)
        parse_dxf_file(db, cad_file.cad_file_id)
    except CadIntakeError:
        # Sample missing or project absent: leave intake empty rather than fail
        # startup.
        return
