"""Packet item accessors, evidence links, and reviewer action recording."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.safety import (
    ALLOWED_REVIEW_PACKET_ACTIONS,
    ALLOWED_REVIEW_PACKET_STATUSES,
    PACKET_ACTION_TO_STATUS,
    find_prohibited_language,
)
from app.db import models

from ._common import _audit, _short
from .errors import ReviewPacketError
from .reads import get_packet


def list_evidence_links_for_item(
    db: Session, item_id: str
) -> list[models.ReviewPacketEvidenceLink]:
    """Return the evidence links for one packet item (public accessor)."""

    return list(
        db.scalars(
            select(models.ReviewPacketEvidenceLink).where(
                models.ReviewPacketEvidenceLink.item_id == item_id
            )
        ).all()
    )


def _get_item(
    db: Session, packet_id: str, item_id: str
) -> models.ReviewPacketItem:
    item = db.scalars(
        select(models.ReviewPacketItem).where(
            models.ReviewPacketItem.item_id == item_id,
            models.ReviewPacketItem.packet_id == packet_id,
        )
    ).first()
    if item is None:
        raise ReviewPacketError(
            "Packet item not found for this packet.", status_code=404
        )
    return item


def _record_action(
    db: Session,
    *,
    item: models.ReviewPacketItem,
    action_type: str,
    new_status: str,
    reviewer_note: str,
    reviewer_name: str,
) -> models.ReviewPacketReviewerAction:
    previous_status = item.reviewer_status
    item.reviewer_status = new_status
    project_id = _packet_project(db, item.packet_id)

    action_id = f"pkt_act_{_short()}"
    record = models.ReviewPacketReviewerAction(
        action_id=action_id,
        packet_id=item.packet_id,
        item_id=item.item_id,
        action_type=action_type,
        reviewer_note=reviewer_note,
        previous_status=previous_status,
        new_status=new_status,
        reviewer_name=reviewer_name,
    )
    db.add(record)
    _audit(
        db,
        project_id=project_id,
        event_type="review_packet_item_action_recorded",
        related_entity_type="review_packet_item",
        related_entity_id=item.item_id,
        description=(
            f"Review packet item action '{action_type}' recorded by "
            f"{reviewer_name}."
        ),
        actor_type="reviewer",
        metadata={
            "packet_id": item.packet_id,
            "item_id": item.item_id,
            "action_id": action_id,
            "action_type": action_type,
            "previous_status": previous_status,
            "new_status": new_status,
            "reviewer_name": reviewer_name,
        },
    )
    _audit(
        db,
        project_id=project_id,
        event_type="review_packet_item_status_updated",
        related_entity_type="review_packet_item",
        related_entity_id=item.item_id,
        description=(
            f"Review packet item status updated from {previous_status} to "
            f"{new_status}."
        ),
        actor_type="reviewer",
        metadata={
            "packet_id": item.packet_id,
            "item_id": item.item_id,
            "previous_status": previous_status,
            "new_status": new_status,
        },
    )
    return record


def _packet_project(db: Session, packet_id: str) -> str:
    packet = get_packet(db, packet_id)
    return packet.project_id if packet else ""


def create_review_packet_reviewer_action(
    db: Session,
    *,
    packet_id: str,
    item_id: str,
    action_type: str,
    reviewer_note: str,
    reviewer_name: str,
) -> tuple[models.ReviewPacketReviewerAction, models.ReviewPacketItem]:
    """Validate and persist a reviewer action on a packet item."""

    item = _get_item(db, packet_id, item_id)
    if action_type not in ALLOWED_REVIEW_PACKET_ACTIONS:
        raise ReviewPacketError(
            f"Unknown packet action '{action_type}'.", status_code=422
        )
    if not reviewer_name or not reviewer_name.strip():
        raise ReviewPacketError("reviewer_name is required.", status_code=422)
    if not reviewer_note or not reviewer_note.strip():
        raise ReviewPacketError("reviewer_note is required.", status_code=422)
    if find_prohibited_language(reviewer_note):
        raise ReviewPacketError(
            "reviewer_note contains prohibited final-decision wording.",
            status_code=422,
        )

    record = _record_action(
        db,
        item=item,
        action_type=action_type,
        new_status=PACKET_ACTION_TO_STATUS[action_type],
        reviewer_note=reviewer_note.strip(),
        reviewer_name=reviewer_name.strip(),
    )
    db.commit()
    db.refresh(record)
    db.refresh(item)
    return record, item


def update_review_packet_item_status(
    db: Session,
    *,
    packet_id: str,
    item_id: str,
    new_status: str,
    reviewer_note: str | None = None,
    reviewer_name: str | None = None,
) -> models.ReviewPacketItem:
    """Validate and apply a status update to a packet item."""

    item = _get_item(db, packet_id, item_id)
    if new_status not in ALLOWED_REVIEW_PACKET_STATUSES:
        raise ReviewPacketError(
            f"Unknown packet status '{new_status}'.", status_code=422
        )
    note = (reviewer_note or "").strip()
    if find_prohibited_language(note):
        raise ReviewPacketError(
            "reviewer_note contains prohibited final-decision wording.",
            status_code=422,
        )

    _record_action(
        db,
        item=item,
        action_type=new_status,
        new_status=new_status,
        reviewer_note=note or "Status updated by reviewer.",
        reviewer_name=(reviewer_name or "reviewer").strip(),
    )
    db.commit()
    db.refresh(item)
    return item
