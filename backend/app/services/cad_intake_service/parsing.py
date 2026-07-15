"""DXF parsing and review-support extraction for CAD intake.

Parses a registered DXF file with ezdxf and extracts layers, entities, blocks,
text, reference candidates, and review-support findings. Reference candidates are
matched against seeded plan sheets; findings are raised when a reference has no
match, a detail reference is ambiguous, a facility label may conflict, or a layer
cannot be categorized. Parsing extracts metadata only. It does not verify CAD,
validate geometry or design, certify compliance, or make final engineering
decisions.
"""

from __future__ import annotations

import re

import ezdxf
from sqlalchemy.orm import Session

# The size caps below are read through the package so a test that monkeypatches
# app.services.cad_intake_service.MAX_PERSISTED_ENTITIES (and the other caps)
# changes parsing behavior exactly as it did on the single-file module.
import app.services.cad_intake_service as _pkg
from app.db import models
from app.services.cad import facility_identity, geometry, reference_parser
from app.services.cad_intake_service._common import (
    _audit,
    _create_finding,
    _layer_category,
    _normalize,
    _now,
    _seeded_sheet_map,
    _short,
)
from app.services.cad_intake_service.errors import (
    CadIntakeError,
    LIMITATIONS_NOTE,
    PARSER_NAME,
    PARSER_VERSION,
)
from app.services.cad_intake_service.reads import get_cad_file
from app.services.cad_intake_service.references import (
    _build_layer_findings,
    _build_reference_candidates,
)
from app.services.cad_intake_service.uploads import create_cad_file_from_sample

PIPE_RE = re.compile(r"\bP-\d+\b")
OUTFALL_RE = re.compile(r"\bOF-\d+\b")

# Safety limits for pathological files. Entities beyond the cap are counted
# but not persisted; a parse warning records the truncation. Text values are
# truncated to the maximum length. Partial parsing is allowed and visible.
MAX_PERSISTED_ENTITIES = 100_000
MAX_TEXT_VALUE_LENGTH = 2_000
MAX_LAYER_COUNT = 5_000


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
        if layer_count >= _pkg.MAX_LAYER_COUNT:
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
        if entity_count > _pkg.MAX_PERSISTED_ENTITIES:
            persisted_truncated = True
            continue
        layer_name = getattr(entity.dxf, "layer", None)
        category = _layer_category(layer_name or "")
        bounds = _entity_bounds(entity)
        text_value = _entity_text(entity)
        if text_value and len(text_value) > _pkg.MAX_TEXT_VALUE_LENGTH:
            text_value = text_value[: _pkg.MAX_TEXT_VALUE_LENGTH]
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
                f"above the {_pkg.MAX_PERSISTED_ENTITIES} persistence limit. All "
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
