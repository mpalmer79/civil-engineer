"""Command center health metrics, module links, and health summary projections."""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.services.command_center.metrics import _severity_for_count
from app.services.command_center_service._common import (
    LIMITATIONS_NOTE,
    ROUTE_CAD_INTAKE,
    ROUTE_CAD_REVIEW,
    ROUTE_PACKET,
    ROUTE_RESPONSE,
    ROUTE_REVIEW_CYCLES,
    ROUTE_SHEET_VIEWER,
    ROUTE_SHEETS,
    ROUTE_WORKFLOW,
    _audit,
    _gather,
    _metrics_for,
    _readiness_for,
    _require_project,
)
from app.services.command_center_service.queues import _ensure_snapshot


def get_project_health_metrics(db: Session, project_id: str) -> list:
    _require_project(db, project_id)
    snapshot = _ensure_snapshot(db, project_id)
    metrics = _metrics_for(db, snapshot.snapshot_id)
    _audit(
        db,
        project_id=project_id,
        event_type="command_center_metrics_viewed",
        related_entity_type="command_center_snapshot",
        related_entity_id=snapshot.snapshot_id,
        description="Command center health metrics viewed.",
        metadata={"snapshot_id": snapshot.snapshot_id},
    )
    db.commit()
    return metrics


def get_project_module_links(db: Session, project_id: str) -> dict:
    _require_project(db, project_id)
    data = _gather(db, project_id)

    def link(module, label, route, description, count):
        return {
            "module": module,
            "label": label,
            "route": route,
            "description": description,
            "count": count,
            "severity": _severity_for_count(count) if count else "info",
        }

    workflow_attention = len(
        [
            i
            for i in data["workflow_items"]
            if i.status in {"needs_follow_up", "needs_more_information"}
        ]
    )
    links = [
        link(
            "project_dashboard",
            "Project Dashboard",
            "/project-dashboard",
            "Unified command center for the project review state.",
            0,
        ),
        link(
            "cad_intake",
            "CAD Intake",
            ROUTE_CAD_INTAKE,
            "Upload, parse, and review DXF files and CAD findings.",
            len(data["cad_files"]),
        ),
        link(
            "review_cycles",
            "Review Cycles",
            ROUTE_REVIEW_CYCLES,
            "Resubmittals, revision comparison, and the response cycle.",
            len(data["resubmittals"]),
        ),
        link(
            "workflow_board",
            "Workflow Board",
            ROUTE_WORKFLOW,
            "Track review-support items through triage to handoff.",
            workflow_attention,
        ),
        link(
            "response_package",
            "Response Package",
            ROUTE_RESPONSE,
            "Draft external review response package.",
            len(
                [i for i in data["response_items"] if i.status == "needs_revision"]
            ),
        ),
        link(
            "review_packet",
            "Review Packet",
            ROUTE_PACKET,
            "Assembled review-support packet with evidence traceability.",
            len(data["packets"]),
        ),
        link(
            "plan_sheets",
            "Plan Sheets",
            ROUTE_SHEETS,
            "Plan sheet index with revisions and missing sheet detection.",
            len(data["plan_sheets"]),
        ),
        link(
            "cad_review",
            "CAD Review",
            ROUTE_CAD_REVIEW,
            "CAD-aware metadata, plan references, and consistency findings.",
            len(data["plan_consistency"]),
        ),
        link(
            "sheet_viewer",
            "Sheet Viewer",
            ROUTE_SHEET_VIEWER,
            "Plan sheet viewer with seeded sheet hotspots.",
            len(data["sheet_hotspots"]),
        ),
    ]
    _audit(
        db,
        project_id=project_id,
        event_type="command_center_module_links_viewed",
        related_entity_type="project",
        related_entity_id=project_id,
        description="Command center module links viewed.",
        metadata={"link_count": len(links)},
    )
    db.commit()
    return {
        "project_id": project_id,
        "links": links,
        "note": (
            "The dashboard links into existing modules rather than replacing them."
        ),
    }


def get_project_health_summary(db: Session, project_id: str) -> dict:
    _require_project(db, project_id)
    snapshot = _ensure_snapshot(db, project_id)
    readiness = _readiness_for(db, snapshot.snapshot_id)
    readiness_ready = len(
        [c for c in readiness if c.status == "ready_for_human_review"]
    )
    _audit(
        db,
        project_id=project_id,
        event_type="command_center_health_summary_viewed",
        related_entity_type="command_center_snapshot",
        related_entity_id=snapshot.snapshot_id,
        description="Command center health summary viewed.",
        metadata={"snapshot_id": snapshot.snapshot_id},
    )
    db.commit()
    return {
        "project_id": project_id,
        "snapshot_id": snapshot.snapshot_id,
        "overall_status": snapshot.overall_status,
        "current_review_cycle_id": snapshot.current_review_cycle_id,
        "attention_count": snapshot.attention_count,
        "ready_for_handoff_count": snapshot.ready_for_handoff_count,
        "carry_forward_count": snapshot.carry_forward_count,
        "needs_more_information_count": snapshot.needs_more_information_count,
        "cad_findings_count": snapshot.cad_findings_count,
        "resubmittal_count": snapshot.resubmittal_count,
        "open_follow_up_count": snapshot.open_follow_up_count,
        "response_mapping_gap_count": snapshot.response_mapping_gap_count,
        "revision_change_count": snapshot.revision_change_count,
        "readiness_ready_count": readiness_ready,
        "summary": snapshot.summary,
        "limitations_note": LIMITATIONS_NOTE,
    }


def _module_links_payload(db: Session, project_id: str) -> dict:
    data = _gather(db, project_id)
    workflow_attention = len(
        [
            i
            for i in data["workflow_items"]
            if i.status in {"needs_follow_up", "needs_more_information"}
        ]
    )

    def link(module, label, route, description, count):
        return {
            "module": module,
            "label": label,
            "route": route,
            "description": description,
            "count": count,
            "severity": _severity_for_count(count) if count else "info",
        }

    links = [
        link("cad_intake", "CAD Intake", ROUTE_CAD_INTAKE, "Upload, parse, and review DXF files and CAD findings.", len(data["cad_files"])),
        link("review_cycles", "Review Cycles", ROUTE_REVIEW_CYCLES, "Resubmittals, revision comparison, and the response cycle.", len(data["resubmittals"])),
        link("workflow_board", "Workflow Board", ROUTE_WORKFLOW, "Track review-support items through triage to handoff.", workflow_attention),
        link("response_package", "Response Package", ROUTE_RESPONSE, "Draft external review response package.", len([i for i in data["response_items"] if i.status == "needs_revision"])),
        link("review_packet", "Review Packet", ROUTE_PACKET, "Assembled review-support packet with evidence traceability.", len(data["packets"])),
        link("plan_sheets", "Plan Sheets", ROUTE_SHEETS, "Plan sheet index with revisions and missing sheet detection.", len(data["plan_sheets"])),
        link("cad_review", "CAD Review", ROUTE_CAD_REVIEW, "CAD-aware metadata, plan references, and consistency findings.", len(data["plan_consistency"])),
        link("sheet_viewer", "Sheet Viewer", ROUTE_SHEET_VIEWER, "Plan sheet viewer with seeded sheet hotspots.", len(data["sheet_hotspots"])),
    ]
    return {
        "project_id": project_id,
        "links": links,
        "note": "The dashboard links into existing modules rather than replacing them.",
    }
