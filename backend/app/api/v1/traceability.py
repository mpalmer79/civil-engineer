"""Project-wide traceability API routes (Phase 4A/4B).

GET /projects/{project_id}/traceability aggregates existing review-support links
between checklist items, evidence, findings, workflow items, and review packets,
with inline review packet context, handoff readiness signals, and the latest
reviewer review action per row. The GET is read-only: it mutates nothing, runs no
analysis engine, and makes no final engineering decision.

POST and GET /projects/{project_id}/traceability/{traceability_row_key}/
review-actions record and read reviewer-controlled review actions on a single
traceability row. A review action is append-only and never mutates the source
records the row references. reviewer_confirmed_link means the reviewer confirmed
the link is useful for review only; no action approves, certifies, verifies,
validates, or marks a requirement satisfied.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db import models
from app.db.database import get_db
from app.schemas.traceability import (
    ProjectTraceabilityResponse,
    TraceabilityReviewActionCreate,
    TraceabilityReviewActionHistory,
    TraceabilityReviewActionRead,
)
from app.services import traceability_service
from app.services.access_control_service import (
    get_optional_user,
    require_project_read,
    require_project_reviewer,
)
from app.services.traceability_service import TraceabilityError

router = APIRouter(tags=["traceability"])

REVIEW_ACTION_HISTORY_NOTE = (
    "Reviewer review actions on this traceability row. Each action records how a "
    "reviewer reviewed the link for review only. It does not approve, certify, "
    "verify, validate, or mark the requirement satisfied."
)


@router.get(
    "/projects/{project_id}/traceability",
    response_model=ProjectTraceabilityResponse,
)
def get_project_traceability(
    project_id: str,
    user: models.UserAccount | None = Depends(get_optional_user),
    db: Session = Depends(get_db),
) -> ProjectTraceabilityResponse:
    # Enforce project access (public demo stays readable; a non-member of a real
    # project is rejected) before reading any traceability data.
    require_project_read(db, project_id, user)
    result = traceability_service.build_project_traceability(db, project_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Project not found")
    return ProjectTraceabilityResponse.model_validate(result)


@router.post(
    "/projects/{project_id}/traceability/{traceability_row_key}/review-actions",
    response_model=TraceabilityReviewActionRead,
    status_code=201,
)
def create_traceability_review_action(
    project_id: str,
    traceability_row_key: str,
    body: TraceabilityReviewActionCreate,
    user: models.UserAccount | None = Depends(get_optional_user),
    db: Session = Depends(get_db),
) -> TraceabilityReviewActionRead:
    # Recording a review action is a reviewer write, so require reviewer access.
    require_project_reviewer(db, project_id, user)
    try:
        record = traceability_service.record_traceability_review_action(
            db,
            project_id=project_id,
            traceability_row_key=traceability_row_key,
            action_type=body.action_type,
            reviewer_note=body.reviewer_note,
            created_by=body.created_by,
            checklist_item_id=body.checklist_item_id,
            evidence_citation_id=body.evidence_citation_id,
            evidence_candidate_id=body.evidence_candidate_id,
            finding_id=body.finding_id,
            workflow_item_id=body.workflow_item_id,
            review_packet_item_id=body.review_packet_item_id,
            relationship_type=body.relationship_type,
        )
    except TraceabilityError as exc:
        raise HTTPException(
            status_code=exc.status_code, detail=exc.message
        ) from exc
    return TraceabilityReviewActionRead.model_validate(record)


@router.get(
    "/projects/{project_id}/traceability/{traceability_row_key}/review-actions",
    response_model=TraceabilityReviewActionHistory,
)
def list_traceability_review_actions(
    project_id: str,
    traceability_row_key: str,
    user: models.UserAccount | None = Depends(get_optional_user),
    db: Session = Depends(get_db),
) -> TraceabilityReviewActionHistory:
    require_project_read(db, project_id, user)
    if traceability_service.build_project_traceability(db, project_id) is None:
        raise HTTPException(status_code=404, detail="Project not found")
    actions = traceability_service.list_traceability_review_actions(
        db, project_id, traceability_row_key
    )
    return TraceabilityReviewActionHistory(
        project_id=project_id,
        traceability_row_key=traceability_row_key,
        total_actions=len(actions),
        actions=[
            TraceabilityReviewActionRead.model_validate(a) for a in actions
        ],
        note=REVIEW_ACTION_HISTORY_NOTE,
    )
