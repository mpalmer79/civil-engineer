"""Phase 7 sheet hotspot, sheet viewer, and plan review action API routes.

These endpoints serve the seeded plan sheet hotspots, assemble the sheet viewer
context for one sheet, and persist human review actions on plan consistency
findings. All responses use review-support language. No endpoint approves a
plan, certifies compliance, verifies CAD, or validates a design, and there is
no action called approve.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.schemas.plan_sheet_hotspot import (
    PlanConsistencyReviewActionCreate,
    PlanConsistencyReviewActionRead,
    PlanConsistencyReviewActionResult,
    PlanSheetHotspotRead,
    SheetHotspotSummary,
    SheetViewerContext,
)
from app.services import (
    plan_review_service,
    plan_sheet_hotspot_service,
    plan_sheet_service,
    project_service,
)
from app.services.plan_review_service import PlanReviewActionError

router = APIRouter(tags=["plan-sheet-viewer"])


def _require_project(db: Session, project_id: str) -> None:
    if project_service.get_project(db, project_id) is None:
        raise HTTPException(status_code=404, detail="Project not found")


@router.get(
    "/projects/{project_id}/sheet-hotspots",
    response_model=list[PlanSheetHotspotRead],
)
def list_sheet_hotspots(
    project_id: str, db: Session = Depends(get_db)
) -> list[PlanSheetHotspotRead]:
    _require_project(db, project_id)
    return plan_sheet_hotspot_service.list_sheet_hotspots(db, project_id)


@router.get(
    "/projects/{project_id}/sheet-hotspots/summary",
    response_model=SheetHotspotSummary,
)
def sheet_hotspot_summary(
    project_id: str, db: Session = Depends(get_db)
) -> SheetHotspotSummary:
    _require_project(db, project_id)
    return SheetHotspotSummary(
        **plan_sheet_hotspot_service.summarize_sheet_hotspots(db, project_id)
    )


@router.get(
    "/plan-sheets/{sheet_id}/sheet-hotspots",
    response_model=list[PlanSheetHotspotRead],
)
def list_hotspots_for_sheet(
    sheet_id: str, db: Session = Depends(get_db)
) -> list[PlanSheetHotspotRead]:
    if plan_sheet_service.get_plan_sheet(db, sheet_id) is None:
        raise HTTPException(status_code=404, detail="Plan sheet not found")
    return plan_sheet_hotspot_service.list_hotspots_for_sheet(db, sheet_id)


@router.get(
    "/plan-sheets/{sheet_id}/viewer-context",
    response_model=SheetViewerContext,
)
def get_sheet_viewer_context(
    sheet_id: str, db: Session = Depends(get_db)
) -> SheetViewerContext:
    context = plan_sheet_hotspot_service.get_plan_view_context(db, sheet_id)
    if context is None:
        raise HTTPException(status_code=404, detail="Plan sheet not found")
    return SheetViewerContext(**context)


@router.get(
    "/sheet-hotspots/{hotspot_id}",
    response_model=PlanSheetHotspotRead,
)
def get_sheet_hotspot(
    hotspot_id: str, db: Session = Depends(get_db)
) -> PlanSheetHotspotRead:
    hotspot = plan_sheet_hotspot_service.inspect_sheet_hotspot(db, hotspot_id)
    if hotspot is None:
        raise HTTPException(status_code=404, detail="Sheet hotspot not found")
    return hotspot


@router.post(
    "/plan-consistency-findings/{plan_finding_id}/review-actions",
    response_model=PlanConsistencyReviewActionResult,
)
def create_plan_consistency_review_action(
    plan_finding_id: str,
    body: PlanConsistencyReviewActionCreate,
    db: Session = Depends(get_db),
) -> PlanConsistencyReviewActionResult:
    try:
        action, finding = (
            plan_review_service.create_plan_consistency_review_action(
                db,
                plan_finding_id=plan_finding_id,
                action=body.action,
                reviewer_name=body.reviewer_name,
                reviewer_note=body.reviewer_note,
            )
        )
    except PlanReviewActionError as exc:
        raise HTTPException(
            status_code=exc.status_code, detail=exc.message
        ) from exc
    return PlanConsistencyReviewActionResult(action=action, finding=finding)


@router.get(
    "/plan-consistency-findings/{plan_finding_id}/review-actions",
    response_model=list[PlanConsistencyReviewActionRead],
)
def list_finding_review_actions(
    plan_finding_id: str, db: Session = Depends(get_db)
) -> list[PlanConsistencyReviewActionRead]:
    from app.services import plan_consistency_service

    finding = plan_consistency_service.get_plan_consistency_finding(
        db, plan_finding_id
    )
    if finding is None:
        raise HTTPException(
            status_code=404, detail="Plan consistency finding not found"
        )
    return plan_review_service.list_plan_consistency_review_actions(
        db, finding.project_id, plan_finding_id=plan_finding_id
    )


@router.get(
    "/projects/{project_id}/plan-consistency-review-actions",
    response_model=list[PlanConsistencyReviewActionRead],
)
def list_project_review_actions(
    project_id: str,
    plan_finding_id: str | None = Query(default=None),
    db: Session = Depends(get_db),
) -> list[PlanConsistencyReviewActionRead]:
    _require_project(db, project_id)
    return plan_review_service.list_plan_consistency_review_actions(
        db, project_id, plan_finding_id=plan_finding_id
    )
