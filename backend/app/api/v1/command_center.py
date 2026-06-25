"""Phase 14 reviewer command center and project health dashboard API.

These endpoints aggregate the existing review-support data into one operational
dashboard for a human reviewer and link into the existing modules. No endpoint
approves plans, certifies compliance, verifies CAD, validates design, closes or
resolves issues, or makes a final engineering decision, and there is no action
called approve.

Read side effects: the command center, latest snapshot, health metrics, attention
items, timeline, readiness checks, reviewer notes, next steps, module links, and
health summary GET endpoints each write an audit event recording reviewer access.
This is intentional so the decision history shows reviewer access. These read
endpoints also generate an initial snapshot once if none exists yet.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.schemas.command_center import (
    AttentionItemStatusUpdate,
    DashboardReviewerNoteCreate,
    DashboardReviewerNoteRead,
    ProjectCommandCenterPayload,
    ProjectCommandCenterSnapshotRead,
    ProjectHealthMetricRead,
    ProjectHealthSummary,
    ProjectModuleLinks,
    ProjectTimelineEventRead,
    ReviewerAttentionItemRead,
    ReviewerNextSteps,
    ReviewReadinessCheckRead,
)
from app.services import command_center_service, project_service
from app.services.command_center_service import CommandCenterError

router = APIRouter(tags=["command-center"])


def _handle(exc: CommandCenterError) -> HTTPException:
    return HTTPException(status_code=exc.status_code, detail=exc.message)


@router.post(
    "/projects/{project_id}/command-center/snapshot",
    response_model=ProjectCommandCenterSnapshotRead,
)
def generate_snapshot(
    project_id: str, db: Session = Depends(get_db)
) -> ProjectCommandCenterSnapshotRead:
    try:
        return command_center_service.generate_command_center_snapshot(
            db, project_id
        )
    except CommandCenterError as exc:
        raise _handle(exc) from exc


@router.get(
    "/projects/{project_id}/command-center",
    response_model=ProjectCommandCenterPayload,
)
def get_command_center(
    project_id: str, db: Session = Depends(get_db)
) -> ProjectCommandCenterPayload:
    try:
        result = command_center_service.get_project_command_center(db, project_id)
    except CommandCenterError as exc:
        raise _handle(exc) from exc
    return ProjectCommandCenterPayload.model_validate(result)


@router.get(
    "/projects/{project_id}/command-center/latest",
    response_model=ProjectCommandCenterSnapshotRead,
)
def get_latest_snapshot(
    project_id: str, db: Session = Depends(get_db)
) -> ProjectCommandCenterSnapshotRead:
    try:
        snapshot = command_center_service.get_latest_command_center_snapshot(
            db, project_id
        )
    except CommandCenterError as exc:
        raise _handle(exc) from exc
    if snapshot is None:
        raise HTTPException(status_code=404, detail="No snapshot found")
    return snapshot


@router.get(
    "/projects/{project_id}/command-center/health-metrics",
    response_model=list[ProjectHealthMetricRead],
)
def get_health_metrics(
    project_id: str, db: Session = Depends(get_db)
) -> list[ProjectHealthMetricRead]:
    try:
        return command_center_service.get_project_health_metrics(db, project_id)
    except CommandCenterError as exc:
        raise _handle(exc) from exc


@router.get(
    "/projects/{project_id}/command-center/attention-items",
    response_model=list[ReviewerAttentionItemRead],
)
def get_attention_items(
    project_id: str,
    status: str | None = None,
    severity: str | None = None,
    source_module: str | None = None,
    attention_type: str | None = None,
    db: Session = Depends(get_db),
) -> list[ReviewerAttentionItemRead]:
    try:
        return command_center_service.get_reviewer_attention_items(
            db,
            project_id,
            status=status,
            severity=severity,
            source_module=source_module,
            attention_type=attention_type,
        )
    except CommandCenterError as exc:
        raise _handle(exc) from exc


@router.patch(
    "/command-center/attention-items/{attention_item_id}/status",
    response_model=ReviewerAttentionItemRead,
)
def update_attention_item_status(
    attention_item_id: str,
    body: AttentionItemStatusUpdate,
    db: Session = Depends(get_db),
) -> ReviewerAttentionItemRead:
    try:
        return command_center_service.update_attention_item_status(
            db,
            attention_item_id,
            status=body.status,
            reviewer_note=body.reviewer_note,
            reviewer_name=body.reviewer_name,
        )
    except CommandCenterError as exc:
        raise _handle(exc) from exc


@router.get(
    "/projects/{project_id}/command-center/timeline",
    response_model=list[ProjectTimelineEventRead],
)
def get_timeline(
    project_id: str, db: Session = Depends(get_db)
) -> list[ProjectTimelineEventRead]:
    try:
        return command_center_service.get_project_timeline(db, project_id)
    except CommandCenterError as exc:
        raise _handle(exc) from exc


@router.get(
    "/projects/{project_id}/command-center/readiness-checks",
    response_model=list[ReviewReadinessCheckRead],
)
def get_readiness_checks(
    project_id: str, db: Session = Depends(get_db)
) -> list[ReviewReadinessCheckRead]:
    try:
        return command_center_service.get_review_readiness_checks(db, project_id)
    except CommandCenterError as exc:
        raise _handle(exc) from exc


@router.post(
    "/projects/{project_id}/command-center/notes",
    response_model=DashboardReviewerNoteRead,
)
def add_note(
    project_id: str,
    body: DashboardReviewerNoteCreate,
    db: Session = Depends(get_db),
) -> DashboardReviewerNoteRead:
    try:
        return command_center_service.add_dashboard_reviewer_note(
            db,
            project_id,
            note_text=body.note_text,
            reviewer_name=body.reviewer_name,
            snapshot_id=body.snapshot_id,
            source_context=body.source_context,
        )
    except CommandCenterError as exc:
        raise _handle(exc) from exc


@router.get(
    "/projects/{project_id}/command-center/notes",
    response_model=list[DashboardReviewerNoteRead],
)
def get_notes(
    project_id: str, db: Session = Depends(get_db)
) -> list[DashboardReviewerNoteRead]:
    try:
        return command_center_service.get_dashboard_reviewer_notes(db, project_id)
    except CommandCenterError as exc:
        raise _handle(exc) from exc


@router.get(
    "/projects/{project_id}/command-center/next-steps",
    response_model=ReviewerNextSteps,
)
def get_next_steps(
    project_id: str, db: Session = Depends(get_db)
) -> ReviewerNextSteps:
    try:
        return ReviewerNextSteps.model_validate(
            command_center_service.get_reviewer_next_steps(db, project_id)
        )
    except CommandCenterError as exc:
        raise _handle(exc) from exc


@router.get(
    "/projects/{project_id}/command-center/module-links",
    response_model=ProjectModuleLinks,
)
def get_module_links(
    project_id: str, db: Session = Depends(get_db)
) -> ProjectModuleLinks:
    try:
        return ProjectModuleLinks.model_validate(
            command_center_service.get_project_module_links(db, project_id)
        )
    except CommandCenterError as exc:
        raise _handle(exc) from exc


@router.get(
    "/projects/{project_id}/command-center/health-summary",
    response_model=ProjectHealthSummary,
)
def get_health_summary(
    project_id: str, db: Session = Depends(get_db)
) -> ProjectHealthSummary:
    try:
        return ProjectHealthSummary.model_validate(
            command_center_service.get_project_health_summary(db, project_id)
        )
    except CommandCenterError as exc:
        raise _handle(exc) from exc
