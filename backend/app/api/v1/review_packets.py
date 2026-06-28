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

from app.db import models
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
from app.services.access_control_service import (
    get_optional_user,
    require_project_read,
    require_project_reviewer,
)
from app.services.review_packet_service import ReviewPacketError


def _require_packet_project(db: Session, packet_id: str) -> models.ReviewPacket:
    """Resolve a review packet to its owning project, 404 if missing."""

    packet = review_packet_service.get_packet(db, packet_id)
    if packet is None:
        raise HTTPException(status_code=404, detail="Review packet not found")
    return packet


router = APIRouter(tags=["review-packets"])


@router.post(
    "/projects/{project_id}/review-packets/generate",
    response_model=ReviewPacketDetail,
)
def generate_review_packet(
    project_id: str,
    user: models.UserAccount | None = Depends(get_optional_user),
    db: Session = Depends(get_db),
) -> ReviewPacketDetail:
    if project_service.get_project(db, project_id) is None:
        raise HTTPException(status_code=404, detail="Project not found")
    require_project_reviewer(db, project_id, user)
    try:
        packet = review_packet_service.generate_review_packet(db, project_id)
    except ReviewPacketError as exc:
        raise HTTPException(
            status_code=exc.status_code, detail=exc.message
        ) from exc
    detail = review_packet_service.assemble_packet_detail(db, packet)
    return ReviewPacketDetail.model_validate(detail)


@router.get(
    "/projects/{project_id}/review-packets",
    response_model=list[ReviewPacketRead],
)
def list_review_packets(
    project_id: str,
    user: models.UserAccount | None = Depends(get_optional_user),
    db: Session = Depends(get_db),
) -> list[ReviewPacketRead]:
    if project_service.get_project(db, project_id) is None:
        raise HTTPException(status_code=404, detail="Project not found")
    require_project_read(db, project_id, user)
    return review_packet_service.list_review_packets(db, project_id)


@router.get("/review-packets/{packet_id}", response_model=ReviewPacketDetail)
def get_review_packet(
    packet_id: str,
    user: models.UserAccount | None = Depends(get_optional_user),
    db: Session = Depends(get_db),
) -> ReviewPacketDetail:
    packet = _require_packet_project(db, packet_id)
    require_project_read(db, packet.project_id, user)
    detail = review_packet_service.get_review_packet(db, packet_id)
    if detail is None:
        raise HTTPException(status_code=404, detail="Review packet not found")
    return ReviewPacketDetail.model_validate(detail)


@router.get(
    "/review-packets/{packet_id}/traceability",
    response_model=ReviewPacketTraceability,
)
def get_review_packet_traceability(
    packet_id: str,
    user: models.UserAccount | None = Depends(get_optional_user),
    db: Session = Depends(get_db),
) -> ReviewPacketTraceability:
    packet = _require_packet_project(db, packet_id)
    require_project_read(db, packet.project_id, user)
    result = review_packet_service.get_review_packet_traceability(db, packet_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Review packet not found")
    return ReviewPacketTraceability.model_validate(result)


@router.get(
    "/review-packets/{packet_id}/print-view",
    response_model=ReviewPacketPrintView,
)
def get_review_packet_print_view(
    packet_id: str,
    user: models.UserAccount | None = Depends(get_optional_user),
    db: Session = Depends(get_db),
) -> ReviewPacketPrintView:
    packet = _require_packet_project(db, packet_id)
    require_project_read(db, packet.project_id, user)
    result = review_packet_service.get_review_packet_print_view(db, packet_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Review packet not found")
    return ReviewPacketPrintView.model_validate(result)


@router.get(
    "/review-packets/{packet_id}/summary",
    response_model=ReviewPacketSummary,
)
def get_review_packet_summary(
    packet_id: str,
    user: models.UserAccount | None = Depends(get_optional_user),
    db: Session = Depends(get_db),
) -> ReviewPacketSummary:
    packet = _require_packet_project(db, packet_id)
    require_project_read(db, packet.project_id, user)
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
    user: models.UserAccount | None = Depends(get_optional_user),
    db: Session = Depends(get_db),
) -> ReviewPacketReviewerActionResult:
    packet = _require_packet_project(db, packet_id)
    require_project_reviewer(db, packet.project_id, user)
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
    user: models.UserAccount | None = Depends(get_optional_user),
    db: Session = Depends(get_db),
) -> ReviewPacketItemRead:
    packet = _require_packet_project(db, packet_id)
    require_project_reviewer(db, packet.project_id, user)
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
