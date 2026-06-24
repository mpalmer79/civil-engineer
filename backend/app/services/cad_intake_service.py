"""Real CAD (DXF) intake and parsing service for Phase 11.

This service registers a real DXF file, parses it with the ezdxf library, and
extracts review-support metadata: layers, entities, blocks, text, reference
candidates, and review-support findings. It compares extracted sheet and detail
references against the seeded Phase 6 plan sheets and raises review-support
findings when a reference has no match, a detail reference is ambiguous, a basin
label may conflict, or a layer cannot be categorized.

Parsing extracts metadata from a real DXF file. It does not verify CAD, validate
geometry or design, certify compliance, or make final engineering decisions. DXF
is the only supported file type in this phase; DWG parsing is out of scope. There
is no action called approve.

Read side effects: get_cad_parse_summary, list_cad_layers, list_cad_text, and
get_cad_file_review_context each write an audit event recording the access. This
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

from app.db import models
from app.services import plan_sheet_service, workflow_service

PARSER_NAME = "ezdxf"
PARSER_VERSION = ezdxf.__version__

SAMPLE_DIR = Path(__file__).resolve().parent.parent / "cad_samples"
# Whitelisted bundled sample DXF fixtures. The client selects a sample by key so
# no arbitrary filesystem path is read. Browser upload is a later enhancement.
SAMPLE_DXF_FILES: dict[str, Path] = {
    "brookside_meadows": SAMPLE_DIR / "brookside_meadows.dxf",
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

# Layer name keyword to review category. Order matters: first match wins.
LAYER_CATEGORY_RULES: list[tuple[str, str]] = [
    ("WTLND", "wetland_buffer"),
    ("WETLAND", "wetland_buffer"),
    ("STORM", "stormwater"),
    ("GRAD", "grading"),
    ("EROS", "erosion_control"),
    ("UTIL", "utilities"),
    ("TITLE", "titleblock"),
    ("NOTE", "notes"),
]

# Default layers that carry no review meaning on their own.
NEUTRAL_LAYERS = {"0", "DEFPOINTS"}

SHEET_RE = re.compile(r"\b([A-Z]-\d\.\d[A-Z0-9]?)\b")
DETAIL_RE = re.compile(r"DETAIL\s+([0-9?]+)\s*/\s*([A-Z]-\d\.[0-9A-Z]+)")
PIPE_RE = re.compile(r"\bP-\d+\b")
OUTFALL_RE = re.compile(r"\bOF-\d+\b")


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
    upper = (layer_name or "").upper()
    for keyword, category in LAYER_CATEGORY_RULES:
        if keyword in upper:
            return category
    return "unknown"


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

    cad_file = models.CadFileUpload(
        cad_file_id=f"cad_{_short()}",
        project_id=project_id,
        file_name=file_name,
        file_type=file_type,
        file_size_bytes=file_size_bytes,
        storage_path=storage_path,
        upload_status="uploaded",
        uploaded_by=uploaded_by,
        limitations_note=LIMITATIONS_NOTE,
    )
    db.add(cad_file)
    _audit(
        db,
        project_id=project_id,
        event_type="cad_file_created",
        related_entity_type="cad_file",
        related_entity_id=cad_file.cad_file_id,
        description=f"CAD file record created for {file_name}.",
        metadata={"cad_file_id": cad_file.cad_file_id, "file_type": file_type},
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
    """Return (x_min, y_min, x_max, y_max) in local drawing coordinates if
    cheaply available, else None. These are not georeferenced coordinates."""

    try:
        dxftype = entity.dxftype()
        if dxftype in {"TEXT", "MTEXT"}:
            point = entity.dxf.insert
            return (float(point[0]), float(point[1]), float(point[0]), float(point[1]))
        if dxftype == "LINE":
            start = entity.dxf.start
            end = entity.dxf.end
            xs = [float(start[0]), float(end[0])]
            ys = [float(start[1]), float(end[1])]
            return (min(xs), min(ys), max(xs), max(ys))
        if dxftype == "LWPOLYLINE":
            pts = [(float(p[0]), float(p[1])) for p in entity.get_points()]
            if pts:
                xs = [p[0] for p in pts]
                ys = [p[1] for p in pts]
                return (min(xs), min(ys), max(xs), max(ys))
    except Exception:
        return None
    return None


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
    if DETAIL_RE.search(normalized):
        return "detail_reference"
    if "SHEET" in normalized and SHEET_RE.search(normalized):
        return "sheet_reference"
    if "OUTFALL" in normalized or OUTFALL_RE.search(normalized):
        return "outfall_label"
    if "BASIN" in normalized and "SHEET" not in normalized and "SEE" not in normalized:
        return "basin_label"
    if PIPE_RE.search(normalized):
        return "pipe_label"
    if SHEET_RE.search(normalized):
        return "sheet_reference"
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

    # Entities and text.
    entity_count = 0
    text_count = 0
    text_extracts: list[models.CadTextExtract] = []
    for entity in msp:
        entity_count += 1
        layer_name = getattr(entity.dxf, "layer", None)
        category = _layer_category(layer_name or "")
        bounds = _entity_bounds(entity)
        text_value = _entity_text(entity)
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

        # Detail references first, so their sheet token is handled as a detail.
        detail_handled = False
        for detail_no, sheet_token in DETAIL_RE.findall(normalized):
            detail_handled = True
            ambiguous = "?" in detail_no or not sheet_token[-1].isdigit()
            matched_id = sheet_map.get(_normalize(sheet_token))
            if ambiguous:
                confidence = "needs_human_review"
                reason = "Detail or sheet token is ambiguous and needs human review."
            elif matched_id:
                confidence = "high"
                reason = f"Detail sheet {sheet_token} matches a seeded plan sheet."
            else:
                confidence = "low"
                reason = f"Detail sheet {sheet_token} has no matching seeded plan sheet."
            candidate = _add_candidate(
                db,
                run=run,
                reference_text=f"DETAIL {detail_no}/{sheet_token}",
                normalized_reference=_normalize(sheet_token),
                reference_type="detail_reference",
                source_text=text,
                matched_plan_sheet_id=matched_id,
                confidence_label=confidence,
                match_reason=reason,
            )
            if ambiguous:
                _create_finding(
                    db,
                    run=run,
                    finding_type="unclear_detail_reference",
                    title=f"Unclear detail reference: DETAIL {detail_no}/{sheet_token}",
                    description=(
                        "The detail reference could not be resolved and needs "
                        "human review."
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
                        f"Sheet {sheet_token} referenced by a detail callout has "
                        "no matching seeded plan sheet."
                    ),
                    severity="medium",
                    source_reference_candidate_id=candidate.candidate_id,
                    source_text_extract_id=text.text_extract_id,
                )

        sheet_scan = normalized
        if detail_handled:
            sheet_scan = DETAIL_RE.sub(" ", normalized)

        if text.reference_type == "sheet_reference" or "SHEET" in sheet_scan:
            for token in SHEET_RE.findall(sheet_scan):
                matched_id = sheet_map.get(_normalize(token))
                if matched_id:
                    confidence = "high"
                    reason = f"Sheet {token} matches seeded plan sheet."
                else:
                    confidence = "needs_human_review"
                    reason = f"Sheet {token} has no matching seeded plan sheet."
                candidate = _add_candidate(
                    db,
                    run=run,
                    reference_text=token,
                    normalized_reference=_normalize(token),
                    reference_type="sheet_reference",
                    source_text=text,
                    matched_plan_sheet_id=matched_id,
                    confidence_label=confidence,
                    match_reason=reason,
                )
                if not matched_id:
                    _create_finding(
                        db,
                        run=run,
                        finding_type="missing_plan_sheet_match",
                        title=f"Referenced sheet {token} has no plan sheet match",
                        description=(
                            f"The DXF references sheet {token}, which has no "
                            "matching seeded plan sheet. Reviewer confirmation "
                            "needed."
                        ),
                        severity="medium",
                        source_reference_candidate_id=candidate.candidate_id,
                        source_text_extract_id=text.text_extract_id,
                    )
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
    by_identifier: dict[str, set[str]] = {}
    sources: dict[str, models.CadTextExtract] = {}
    for normalized, text in basin_labels:
        identifier = normalized.split()[-1] if normalized.split() else normalized
        by_identifier.setdefault(identifier, set()).add(normalized)
        sources[normalized] = text
    for identifier, labels in by_identifier.items():
        if len(labels) > 1:
            joined = ", ".join(sorted(labels))
            sample_text = sources[sorted(labels)[0]]
            _create_finding(
                db,
                run=run,
                finding_type="possible_label_conflict",
                title=f"Possible basin label conflict for '{identifier}'",
                description=(
                    f"Multiple basin labels share identifier '{identifier}': "
                    f"{joined}. Reviewer confirmation needed."
                ),
                severity="medium",
                source_text_extract_id=sample_text.text_extract_id,
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
