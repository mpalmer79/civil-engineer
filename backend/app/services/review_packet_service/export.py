"""Traceability and printable render views for review-support packets.

Both read entry points have an intentional audit side effect recording reviewer
access.
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import models

from ._common import (
    DRAFT_NOTICE,
    PROFESSIONAL_LIMITATIONS,
    TRACEABILITY_REVIEW_NOTE,
    _audit,
)
from .reads import assemble_packet_detail, get_packet


def get_review_packet_traceability(db: Session, packet_id: str) -> dict | None:
    """Return the evidence traceability matrix for a packet.

    Read side effect: writes a review_packet_traceability_requested audit event.
    """

    packet = get_packet(db, packet_id)
    if packet is None:
        return None

    sections = db.scalars(
        select(models.ReviewPacketSection).where(
            models.ReviewPacketSection.packet_id == packet_id
        )
    ).all()
    section_type_by_id = {s.section_id: s.section_type for s in sections}
    items = db.scalars(
        select(models.ReviewPacketItem)
        .where(models.ReviewPacketItem.packet_id == packet_id)
        .order_by(models.ReviewPacketItem.display_order)
    ).all()
    item_by_id = {i.item_id: i for i in items}
    links = db.scalars(
        select(models.ReviewPacketEvidenceLink).where(
            models.ReviewPacketEvidenceLink.packet_id == packet_id
        )
    ).all()

    rows = []
    for link in links:
        item = item_by_id.get(link.item_id)
        if item is None:
            continue
        rows.append(
            {
                "section_type": section_type_by_id.get(item.section_id, ""),
                "item_id": item.item_id,
                "item_title": item.title,
                "item_type": item.item_type,
                "source_type": item.source_type,
                "source_id": item.source_id,
                "evidence_type": link.evidence_type,
                "evidence_id": link.evidence_id,
                "relationship": link.relationship,
                "label": link.label,
            }
        )

    _audit(
        db,
        project_id=packet.project_id,
        event_type="review_packet_traceability_requested",
        related_entity_type="review_packet",
        related_entity_id=packet_id,
        description="Review packet evidence traceability matrix requested.",
        actor_type="reviewer",
        metadata={"packet_id": packet_id, "row_count": len(rows)},
    )
    db.commit()

    return {
        "packet_id": packet_id,
        "project_id": packet.project_id,
        "total_rows": len(rows),
        "rows": rows,
        "note": (
            "Each row traces a packet item back to one source evidence entity. "
            "This is review-support traceability, not a verification or "
            "certification of the evidence."
        ),
    }


def get_review_packet_print_view(db: Session, packet_id: str) -> dict | None:
    """Return a printable review-support view for a packet.

    Read side effect: writes a review_packet_print_view_requested audit event.
    """

    packet = get_packet(db, packet_id)
    if packet is None:
        return None

    detail = assemble_packet_detail(db, packet)
    print_sections = [
        {
            "title": s["title"],
            "section_type": s["section_type"],
            "summary": s["summary"],
            "items": s["items"],
        }
        for s in detail["sections"]
    ]

    traceability_review_rows = _packet_traceability_review_rows(
        db, packet.project_id, packet_id
    )

    _audit(
        db,
        project_id=packet.project_id,
        event_type="review_packet_print_view_requested",
        related_entity_type="review_packet",
        related_entity_id=packet_id,
        description="Review packet printable view requested.",
        actor_type="reviewer",
        metadata={"packet_id": packet_id},
    )
    db.commit()

    return {
        "packet_id": packet.packet_id,
        "project_id": packet.project_id,
        "title": packet.title,
        "packet_type": packet.packet_type,
        "status": packet.status,
        "summary": packet.summary,
        "generated_from_phase": packet.generated_from_phase,
        "created_by": packet.created_by,
        "created_at": packet.created_at,
        "limitations_note": packet.limitations_note,
        "professional_limitations": PROFESSIONAL_LIMITATIONS,
        "draft_notice": DRAFT_NOTICE,
        "sections": print_sections,
        "traceability_review_rows": traceability_review_rows,
        "traceability_note": TRACEABILITY_REVIEW_NOTE,
    }


def _packet_traceability_review_rows(
    db: Session, project_id: str, packet_id: str
) -> list[dict]:
    """Return project traceability rows included in this packet, with review state.

    Read-only. Each row carries its latest reviewer review action, or
    requires_reviewer_confirmation when no action has been recorded. This shows the
    reviewer's traceability review state on the handoff view; it does not approve
    or certify anything.
    """

    from app.services import traceability_service

    result = traceability_service.build_project_traceability(db, project_id)
    if result is None:
        return []
    rows: list[dict] = []
    for r in result["rows"]:
        contexts = r.get("packet_contexts", [])
        if not any(c["review_packet_id"] == packet_id for c in contexts):
            continue
        action = r.get("latest_review_action")
        rows.append(
            {
                "traceability_row_key": r["traceability_row_key"],
                "checklist_title": r.get("checklist_title"),
                "checklist_requirement": r.get("checklist_requirement"),
                "relationship_type": r["relationship_type"],
                "review_action_type": action["action_type"] if action else None,
                "reviewer_note": action.get("reviewer_note") if action else None,
                "created_by": action.get("created_by") if action else None,
                "requires_reviewer_confirmation": action is None,
            }
        )
    return rows
