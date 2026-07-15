"""Shared constants and private helpers for the command center service.

Data gathering here is queried directly to avoid other services' read audit
writes.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import models
from app.services import review_cycle_service
from app.services.command_center_service.errors import CommandCenterError

LIMITATIONS_NOTE = (
    "The command center aggregates review-support data and links into existing "
    "modules. It does not approve plans, certify compliance, verify CAD, validate "
    "design, declare a project safe, or close or resolve issues. All statuses are "
    "review-support statuses, not final engineering decisions."
)

# Deep-link routes into existing modules.
ROUTE_WORKFLOW = "/workflow-board"
ROUTE_CAD_INTAKE = "/cad-intake"
ROUTE_CAD_REVIEW = "/cad-review"
ROUTE_REVIEW_CYCLES = "/review-cycles"
ROUTE_RESPONSE = "/response-package"
ROUTE_PACKET = "/review-packet"
ROUTE_SHEETS = "/plan-sheets"
ROUTE_SHEET_VIEWER = "/sheet-viewer"
ROUTE_DOCUMENTS = "/documents"
ROUTE_CHECKLIST = "/checklist"

_SEVERITY_RANK = {
    "needs_human_review": 4,
    "high": 3,
    "medium": 2,
    "low": 1,
    "info": 0,
}


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
    metadata: dict | None = None,
) -> None:
    db.add(
        models.AuditEvent(
            audit_event_id=f"audit_cc_{uuid.uuid4().hex[:12]}",
            project_id=project_id,
            event_type=event_type,
            actor_type="reviewer",
            related_entity_type=related_entity_type,
            related_entity_id=related_entity_id,
            description=description,
            timestamp=_now(),
            event_metadata=metadata or {},
        )
    )


def _require_project(db: Session, project_id: str) -> None:
    if db.get(models.Project, project_id) is None:
        raise CommandCenterError("Project not found.", status_code=404)


# ---------------------------------------------------------------------------
# Data gathering (queried directly to avoid other services' read audit writes)
# ---------------------------------------------------------------------------


def _gather(db: Session, project_id: str) -> dict:
    def q(model, *where):
        stmt = select(model).where(model.project_id == project_id)
        for clause in where:
            stmt = stmt.where(clause)
        return list(db.scalars(stmt).all())

    workflow_items = q(models.WorkflowItem)
    documents = q(models.Document)
    checklist_items = q(models.ChecklistItem)
    cad_files = q(models.CadFileUpload)
    cad_parse_runs = q(models.CadParseRun)
    cad_findings = q(models.CadReviewFinding)
    review_cycles = q(models.ReviewCycle)
    resubmittals = q(models.ResubmittalPackage)
    applicant_responses = q(models.ApplicantResponse)
    mappings = q(models.ApplicantResponseMapping)
    comparison_runs = q(models.RevisionComparisonRun)
    change_records = q(models.RevisionChangeRecord)
    carry_forwards = q(models.IssueCarryForward)
    resolutions = q(models.ResponseResolutionRecord)
    follow_ups = q(models.WorkflowFollowUpRequest)

    latest_package = db.scalars(
        select(models.ResponsePackage)
        .where(models.ResponsePackage.project_id == project_id)
        .order_by(models.ResponsePackage.created_at.desc())
    ).first()
    response_items = []
    if latest_package is not None:
        response_items = list(
            db.scalars(
                select(models.ResponsePackageItem).where(
                    models.ResponsePackageItem.response_package_id
                    == latest_package.response_package_id
                )
            ).all()
        )

    packets = q(models.ReviewPacket)
    plan_sheets = q(models.PlanSheet)
    plan_consistency = q(models.PlanConsistencyFinding)
    sheet_hotspots = q(models.PlanSheetHotspot)

    active_cycle = review_cycle_service._active_cycle(db, project_id)
    next_prep = None
    if active_cycle is not None:
        next_prep = db.scalars(
            select(models.NextCyclePreparation).where(
                models.NextCyclePreparation.review_cycle_id
                == active_cycle.review_cycle_id
            )
        ).first()

    mapped_response_ids = {m.applicant_response_id for m in mappings}
    return {
        "workflow_items": workflow_items,
        "documents": documents,
        "checklist_items": checklist_items,
        "cad_files": cad_files,
        "cad_parse_runs": cad_parse_runs,
        "cad_findings": cad_findings,
        "review_cycles": review_cycles,
        "resubmittals": resubmittals,
        "applicant_responses": applicant_responses,
        "mappings": mappings,
        "mapped_response_ids": mapped_response_ids,
        "comparison_runs": comparison_runs,
        "change_records": change_records,
        "carry_forwards": carry_forwards,
        "resolutions": resolutions,
        "follow_ups": follow_ups,
        "response_items": response_items,
        "packets": packets,
        "plan_sheets": plan_sheets,
        "plan_consistency": plan_consistency,
        "sheet_hotspots": sheet_hotspots,
        "active_cycle": active_cycle,
        "next_prep": next_prep,
    }


# ---------------------------------------------------------------------------
# Read helpers over generated snapshot children
# ---------------------------------------------------------------------------


def get_latest_snapshot_record(
    db: Session, project_id: str
) -> models.ProjectCommandCenterSnapshot | None:
    return db.scalars(
        select(models.ProjectCommandCenterSnapshot)
        .where(models.ProjectCommandCenterSnapshot.project_id == project_id)
        .order_by(models.ProjectCommandCenterSnapshot.generated_at.desc())
    ).first()


def _metrics_for(db: Session, snapshot_id: str) -> list:
    return list(
        db.scalars(
            select(models.ProjectHealthMetric)
            .where(models.ProjectHealthMetric.snapshot_id == snapshot_id)
            .order_by(models.ProjectHealthMetric.id)
        ).all()
    )


def _attention_for(db: Session, snapshot_id: str, **filters) -> list:
    stmt = select(models.ReviewerAttentionItem).where(
        models.ReviewerAttentionItem.snapshot_id == snapshot_id
    )
    if filters.get("status"):
        stmt = stmt.where(models.ReviewerAttentionItem.status == filters["status"])
    if filters.get("severity"):
        stmt = stmt.where(
            models.ReviewerAttentionItem.severity == filters["severity"]
        )
    if filters.get("source_module"):
        stmt = stmt.where(
            models.ReviewerAttentionItem.source_module == filters["source_module"]
        )
    if filters.get("attention_type"):
        stmt = stmt.where(
            models.ReviewerAttentionItem.attention_type
            == filters["attention_type"]
        )
    stmt = stmt.order_by(models.ReviewerAttentionItem.id)
    return list(db.scalars(stmt).all())


def _readiness_for(db: Session, snapshot_id: str) -> list:
    return list(
        db.scalars(
            select(models.ReviewReadinessCheck)
            .where(models.ReviewReadinessCheck.snapshot_id == snapshot_id)
            .order_by(models.ReviewReadinessCheck.id)
        ).all()
    )
