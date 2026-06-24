"""Phase 9 reviewer workflow board API routes.

These endpoints generate and read the reviewer workflow board and record
reviewer actions, notes, and follow-up requests on workflow items. The board
organizes review-support work for a human reviewer. No endpoint approves a
plan, certifies compliance, stamps a drawing, verifies CAD, or validates a
design, and there is no action called approve.

Read side effects: GET /workflow-items/{workflow_item_id},
GET /workflow-items/{workflow_item_id}/history,
GET /projects/{project_id}/workflow-board/summary, and
GET /projects/{project_id}/workflow-board/ready-for-handoff each write an audit
event recording the access. This is intentional so the decision history shows
reviewer activity.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.schemas.workflow import (
    ReadyForHandoffSummary,
    WorkflowActionRead,
    WorkflowBoardSummary,
    WorkflowFollowUpRequestCreate,
    WorkflowFollowUpRequestRead,
    WorkflowItemDetail,
    WorkflowItemHistory,
    WorkflowItemRead,
    WorkflowItemStatusUpdate,
    WorkflowNoteCreate,
)
from app.services import project_service, workflow_service
from app.services.workflow_service import WorkflowError

router = APIRouter(tags=["workflow-board"])


@router.post(
    "/projects/{project_id}/workflow-board/generate",
    response_model=list[WorkflowItemRead],
)
def generate_workflow_board(
    project_id: str, db: Session = Depends(get_db)
) -> list[WorkflowItemRead]:
    if project_service.get_project(db, project_id) is None:
        raise HTTPException(status_code=404, detail="Project not found")
    try:
        items = workflow_service.generate_workflow_items_from_review_packet(
            db, project_id
        )
    except WorkflowError as exc:
        raise HTTPException(
            status_code=exc.status_code, detail=exc.message
        ) from exc
    return items


@router.get(
    "/projects/{project_id}/workflow-board",
    response_model=list[WorkflowItemRead],
)
def list_workflow_items(
    project_id: str,
    status: str | None = None,
    severity: str | None = None,
    section_type: str | None = None,
    assigned_role: str | None = None,
    source_type: str | None = None,
    db: Session = Depends(get_db),
) -> list[WorkflowItemRead]:
    if project_service.get_project(db, project_id) is None:
        raise HTTPException(status_code=404, detail="Project not found")
    return workflow_service.list_workflow_items(
        db,
        project_id,
        status=status,
        severity=severity,
        section_type=section_type,
        assigned_role=assigned_role,
        source_type=source_type,
    )


@router.get(
    "/projects/{project_id}/workflow-board/summary",
    response_model=WorkflowBoardSummary,
)
def get_workflow_board_summary(
    project_id: str, db: Session = Depends(get_db)
) -> WorkflowBoardSummary:
    result = workflow_service.get_workflow_board_summary(db, project_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Project not found")
    return WorkflowBoardSummary.model_validate(result)


@router.get(
    "/projects/{project_id}/workflow-board/ready-for-handoff",
    response_model=ReadyForHandoffSummary,
)
def get_ready_for_handoff_summary(
    project_id: str, db: Session = Depends(get_db)
) -> ReadyForHandoffSummary:
    result = workflow_service.get_ready_for_handoff_summary(db, project_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Project not found")
    return ReadyForHandoffSummary.model_validate(result)


@router.get(
    "/workflow-items/{workflow_item_id}",
    response_model=WorkflowItemDetail,
)
def get_workflow_item(
    workflow_item_id: str, db: Session = Depends(get_db)
) -> WorkflowItemDetail:
    detail = workflow_service.get_workflow_item(db, workflow_item_id)
    if detail is None:
        raise HTTPException(status_code=404, detail="Workflow item not found")
    return WorkflowItemDetail.model_validate(detail)


@router.get(
    "/workflow-items/{workflow_item_id}/history",
    response_model=WorkflowItemHistory,
)
def get_workflow_item_history(
    workflow_item_id: str, db: Session = Depends(get_db)
) -> WorkflowItemHistory:
    result = workflow_service.get_workflow_item_history(db, workflow_item_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Workflow item not found")
    return WorkflowItemHistory.model_validate(result)


@router.get(
    "/workflow-items/{workflow_item_id}/actions",
    response_model=list[WorkflowActionRead],
)
def list_workflow_actions(
    workflow_item_id: str, db: Session = Depends(get_db)
) -> list[WorkflowActionRead]:
    if workflow_service.get_workflow_item_record(db, workflow_item_id) is None:
        raise HTTPException(status_code=404, detail="Workflow item not found")
    return workflow_service.list_workflow_actions(db, workflow_item_id)


@router.get(
    "/workflow-items/{workflow_item_id}/follow-ups",
    response_model=list[WorkflowFollowUpRequestRead],
)
def list_follow_up_requests(
    workflow_item_id: str, db: Session = Depends(get_db)
) -> list[WorkflowFollowUpRequestRead]:
    if workflow_service.get_workflow_item_record(db, workflow_item_id) is None:
        raise HTTPException(status_code=404, detail="Workflow item not found")
    return workflow_service.list_follow_up_requests(db, workflow_item_id)


@router.patch(
    "/workflow-items/{workflow_item_id}/status",
    response_model=WorkflowItemRead,
)
def update_workflow_item_status(
    workflow_item_id: str,
    body: WorkflowItemStatusUpdate,
    db: Session = Depends(get_db),
) -> WorkflowItemRead:
    try:
        item = workflow_service.update_workflow_item_status(
            db,
            workflow_item_id=workflow_item_id,
            new_status=body.new_status,
            reviewer_note=body.reviewer_note,
            reviewer_name=body.reviewer_name,
            target_date=body.target_date,
        )
    except WorkflowError as exc:
        raise HTTPException(
            status_code=exc.status_code, detail=exc.message
        ) from exc
    return item


@router.post(
    "/workflow-items/{workflow_item_id}/notes",
    response_model=WorkflowItemRead,
)
def add_workflow_note(
    workflow_item_id: str,
    body: WorkflowNoteCreate,
    db: Session = Depends(get_db),
) -> WorkflowItemRead:
    try:
        item = workflow_service.add_workflow_note(
            db,
            workflow_item_id=workflow_item_id,
            reviewer_note=body.reviewer_note,
            reviewer_name=body.reviewer_name,
        )
    except WorkflowError as exc:
        raise HTTPException(
            status_code=exc.status_code, detail=exc.message
        ) from exc
    return item


@router.post(
    "/workflow-items/{workflow_item_id}/follow-ups",
    response_model=WorkflowFollowUpRequestRead,
)
def create_follow_up_request(
    workflow_item_id: str,
    body: WorkflowFollowUpRequestCreate,
    db: Session = Depends(get_db),
) -> WorkflowFollowUpRequestRead:
    try:
        follow_up = workflow_service.create_follow_up_request(
            db,
            workflow_item_id=workflow_item_id,
            requested_from=body.requested_from,
            request_reason=body.request_reason,
            requested_information=body.requested_information,
            reviewer_name=body.reviewer_name,
            target_date=body.target_date,
        )
    except WorkflowError as exc:
        raise HTTPException(
            status_code=exc.status_code, detail=exc.message
        ) from exc
    return follow_up
