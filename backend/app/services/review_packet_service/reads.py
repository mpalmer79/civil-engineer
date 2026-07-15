"""Read accessors and projections for review-support packets.

Some read entry points have an intentional audit side effect so the decision
history reflects reviewer access.
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import models

from ._common import _audit


def get_packet(db: Session, packet_id: str) -> models.ReviewPacket | None:
    return db.scalars(
        select(models.ReviewPacket).where(
            models.ReviewPacket.packet_id == packet_id
        )
    ).first()


def list_review_packets(db: Session, project_id: str) -> list[models.ReviewPacket]:
    stmt = (
        select(models.ReviewPacket)
        .where(models.ReviewPacket.project_id == project_id)
        .order_by(models.ReviewPacket.created_at.desc())
    )
    return list(db.scalars(stmt).all())


def _links_by_item(db: Session, packet_id: str) -> dict[str, list]:
    links = db.scalars(
        select(models.ReviewPacketEvidenceLink).where(
            models.ReviewPacketEvidenceLink.packet_id == packet_id
        )
    ).all()
    grouped: dict[str, list] = {}
    for link in links:
        grouped.setdefault(link.item_id, []).append(link)
    return grouped


def _items_by_section(db: Session, packet_id: str) -> dict[str, list]:
    items = db.scalars(
        select(models.ReviewPacketItem)
        .where(models.ReviewPacketItem.packet_id == packet_id)
        .order_by(models.ReviewPacketItem.display_order)
    ).all()
    grouped: dict[str, list] = {}
    for item in items:
        grouped.setdefault(item.section_id, []).append(item)
    return grouped


def assemble_packet_detail(db: Session, packet: models.ReviewPacket) -> dict:
    sections = db.scalars(
        select(models.ReviewPacketSection)
        .where(models.ReviewPacketSection.packet_id == packet.packet_id)
        .order_by(models.ReviewPacketSection.display_order)
    ).all()
    links_by_item = _links_by_item(db, packet.packet_id)
    items_by_section = _items_by_section(db, packet.packet_id)

    def _item_dict(item: models.ReviewPacketItem) -> dict:
        return {
            "item_id": item.item_id,
            "packet_id": item.packet_id,
            "section_id": item.section_id,
            "item_type": item.item_type,
            "title": item.title,
            "description": item.description,
            "severity": item.severity,
            "source_type": item.source_type,
            "source_id": item.source_id,
            "reviewer_status": item.reviewer_status,
            "reviewer_note": item.reviewer_note,
            "requires_human_review": item.requires_human_review,
            "display_order": item.display_order,
            "evidence_links": links_by_item.get(item.item_id, []),
        }

    section_dicts = []
    for section in sections:
        section_dicts.append(
            {
                "section_id": section.section_id,
                "packet_id": section.packet_id,
                "title": section.title,
                "section_type": section.section_type,
                "display_order": section.display_order,
                "summary": section.summary,
                "status": section.status,
                "requires_human_review": section.requires_human_review,
                "items": [
                    _item_dict(i)
                    for i in items_by_section.get(section.section_id, [])
                ],
            }
        )

    return {
        "packet_id": packet.packet_id,
        "project_id": packet.project_id,
        "title": packet.title,
        "packet_type": packet.packet_type,
        "status": packet.status,
        "summary": packet.summary,
        "generated_from_phase": packet.generated_from_phase,
        "created_by": packet.created_by,
        "limitations_note": packet.limitations_note,
        "created_at": packet.created_at,
        "updated_at": packet.updated_at,
        "sections": section_dicts,
    }


def get_review_packet(db: Session, packet_id: str) -> dict | None:
    """Return the full packet detail and record that it was viewed.

    Read side effect: writes a review_packet_viewed audit event.
    """

    packet = get_packet(db, packet_id)
    if packet is None:
        return None
    _audit(
        db,
        project_id=packet.project_id,
        event_type="review_packet_viewed",
        related_entity_type="review_packet",
        related_entity_id=packet_id,
        description="Review packet draft viewed.",
        actor_type="reviewer",
        metadata={"packet_id": packet_id},
    )
    db.commit()
    return assemble_packet_detail(db, packet)


def summarize_review_packet(db: Session, packet_id: str) -> dict | None:
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
        select(models.ReviewPacketItem).where(
            models.ReviewPacketItem.packet_id == packet_id
        )
    ).all()
    link_count = (
        db.query(models.ReviewPacketEvidenceLink)
        .filter(models.ReviewPacketEvidenceLink.packet_id == packet_id)
        .count()
    )

    by_section: dict[str, int] = {}
    by_status: dict[str, int] = {}
    by_severity: dict[str, int] = {}
    for item in items:
        stype = section_type_by_id.get(item.section_id, "unknown")
        by_section[stype] = by_section.get(stype, 0) + 1
        by_status[item.reviewer_status] = by_status.get(item.reviewer_status, 0) + 1
        by_severity[item.severity] = by_severity.get(item.severity, 0) + 1

    return {
        "packet_id": packet_id,
        "project_id": packet.project_id,
        "status": packet.status,
        "total_sections": len(sections),
        "total_items": len(items),
        "total_evidence_links": link_count,
        "items_by_section_type": by_section,
        "items_by_status": by_status,
        "items_by_severity": by_severity,
        "items_requiring_human_review": len(
            [i for i in items if i.requires_human_review]
        ),
    }
