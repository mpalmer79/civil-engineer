"""Phase 8 review packet API routes.

These endpoints generate and read review-support packet drafts and record
reviewer actions on packet items. A packet organizes evidence for a human
reviewer. No endpoint approves a plan, certifies compliance, stamps a drawing,
verifies CAD, or validates a design, and there is no action called approve.

Read side effects: GET /review-packets/{packet_id},
GET /review-packets/{packet_id}/traceability, and
GET /review-packets/{packet_id}/print-view each write an audit event recording
the access. This is intentional so the decision history shows reviewer access.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.schemas.review_packet import (
    ReviewPacketDetail,
    ReviewPacketItemRead,
    ReviewPacketItemStatusUpdate,
    ReviewPacketPrintView,
    ReviewPacketRead,
    ReviewPacketReviewerActionCreate,
    ReviewPacketReviewerActionResult,
    ReviewPacketSummary,
    ReviewPacketTraceability,
)
from app.services import project_service, review_packet_service
from app.services.review_packet_service import ReviewPacketError

router = APIRouter(tags=["review-packets"])


@router.post(
    "/projects/{project_id}/review-packets/generate",
    response_model=ReviewPacketDetail,
)
def generate_review_packet(
    project_id: str, db: Session = Depends(get_db)
) -> ReviewPacketDetail:
    if project_service.get_project(db, project_id) is None:
        raise HTTPException(status_code=404, detail="Project not found")
    try:
        packet = review_packet_service.generate_review_packet(db, project_id)
    except ReviewPacketError as exc:
        raise HTTPException(
            status_code=exc.status_code, detail=exc.message
        ) from exc
    detail = review_packet_service._assemble_detail(db, packet)
    return ReviewPacketDetail.model_validate(detail)


@router.get(
    "/projects/{project_id}/review-packets",
    response_model=list[ReviewPacketRead],
)
def list_review_packets(
    project_id: str, db: Session = Depends(get_db)
) -> list[ReviewPacketRead]:
    if project_service.get_project(db, project_id) is None:
        raise HTTPException(status_code=404, detail="Project not found")
    return review_packet_service.list_review_packets(db, project_id)


@router.get("/review-packets/{packet_id}", response_model=ReviewPacketDetail)
def get_review_packet(
    packet_id: str, db: Session = Depends(get_db)
) -> ReviewPacketDetail:
    detail = review_packet_service.get_review_packet(db, packet_id)
    if detail is None:
        raise HTTPException(status_code=404, detail="Review packet not found")
    return ReviewPacketDetail.model_validate(detail)


@router.get(
    "/review-packets/{packet_id}/traceability",
    response_model=ReviewPacketTraceability,
)
def get_review_packet_traceability(
    packet_id: str, db: Session = Depends(get_db)
) -> ReviewPacketTraceability:
    result = review_packet_service.get_review_packet_traceability(db, packet_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Review packet not found")
    return ReviewPacketTraceability.model_validate(result)


@router.get(
    "/review-packets/{packet_id}/print-view",
    response_model=ReviewPacketPrintView,
)
def get_review_packet_print_view(
    packet_id: str, db: Session = Depends(get_db)
) -> ReviewPacketPrintView:
    result = review_packet_service.get_review_packet_print_view(db, packet_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Review packet not found")
    return ReviewPacketPrintView.model_validate(result)


@router.get(
    "/review-packets/{packet_id}/summary",
    response_model=ReviewPacketSummary,
)
def get_review_packet_summary(
    packet_id: str, db: Session = Depends(get_db)
) -> ReviewPacketSummary:
    result = review_packet_service.summarize_review_packet(db, packet_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Review packet not found")
    return ReviewPacketSummary.model_validate(result)


@router.post(
    "/review-packets/{packet_id}/items/{item_id}/review-actions",
    response_model=ReviewPacketReviewerActionResult,
)
def create_review_packet_reviewer_action(
    packet_id: str,
    item_id: str,
    body: ReviewPacketReviewerActionCreate,
    db: Session = Depends(get_db),
) -> ReviewPacketReviewerActionResult:
    try:
        action, item = (
            review_packet_service.create_review_packet_reviewer_action(
                db,
                packet_id=packet_id,
                item_id=item_id,
                action_type=body.action_type,
                reviewer_note=body.reviewer_note,
                reviewer_name=body.reviewer_name,
            )
        )
    except ReviewPacketError as exc:
        raise HTTPException(
            status_code=exc.status_code, detail=exc.message
        ) from exc
    return ReviewPacketReviewerActionResult(action=action, item=item)


@router.patch(
    "/review-packets/{packet_id}/items/{item_id}/status",
    response_model=ReviewPacketItemRead,
)
def update_review_packet_item_status(
    packet_id: str,
    item_id: str,
    body: ReviewPacketItemStatusUpdate,
    db: Session = Depends(get_db),
) -> ReviewPacketItemRead:
    try:
        item = review_packet_service.update_review_packet_item_status(
            db,
            packet_id=packet_id,
            item_id=item_id,
            new_status=body.new_status,
            reviewer_note=body.reviewer_note,
            reviewer_name=body.reviewer_name,
        )
    except ReviewPacketError as exc:
        raise HTTPException(
            status_code=exc.status_code, detail=exc.message
        ) from exc
    return item
