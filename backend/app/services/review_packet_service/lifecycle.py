"""Packet lifecycle: generation, deletion, and startup ensure."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import models

from ._common import (
    GENERATED_BY,
    GENERATED_FROM_PHASE,
    LIMITATIONS_NOTE,
    PACKET_TYPE,
    _audit,
    _short,
)
from .errors import ReviewPacketError
from .sections import _Builder, _build_sections


def _delete_existing(db: Session, project_id: str) -> None:
    packet_ids = [
        p.packet_id
        for p in db.scalars(
            select(models.ReviewPacket).where(
                models.ReviewPacket.project_id == project_id
            )
        ).all()
    ]
    if not packet_ids:
        return
    for model in (
        models.ReviewPacketReviewerAction,
        models.ReviewPacketEvidenceLink,
        models.ReviewPacketItem,
        models.ReviewPacketSection,
    ):
        db.query(model).filter(model.packet_id.in_(packet_ids)).delete(
            synchronize_session=False
        )
    db.query(models.ReviewPacket).filter(
        models.ReviewPacket.project_id == project_id
    ).delete(synchronize_session=False)
    db.commit()


def generate_review_packet(db: Session, project_id: str) -> models.ReviewPacket:
    """Generate a fresh review-support packet draft for a project.

    Idempotent: existing packets for the project are removed and a new packet is
    built from the current seeded data. Writes a review_packet_generated audit
    event.
    """

    project = db.get(models.Project, project_id)
    if project is None:
        raise ReviewPacketError("Project not found.", status_code=404)

    # Enforce the per-organization review packet limit before any mutation, when
    # enforcement is enabled. A no-op for the demo org and in advisory mode, so
    # the public Brookside demo and startup seeding are never blocked.
    from app.services import usage_service

    usage_service.check_limit(
        db,
        category="review_packet_generated",
        organization_id=project.organization_id,
    )

    _delete_existing(db, project_id)

    packet_id = f"packet_{_short()}"
    packet = models.ReviewPacket(
        packet_id=packet_id,
        project_id=project_id,
        title="Brookside Meadows review-support packet (draft)",
        packet_type=PACKET_TYPE,
        status="draft",
        summary=(
            "Draft review-support packet assembling documents, checklist items, "
            "findings, plan sheets, CAD-aware metadata, hotspots, plan "
            "consistency findings, and reviewer actions for human review."
        ),
        generated_from_phase=GENERATED_FROM_PHASE,
        created_by=GENERATED_BY,
        limitations_note=LIMITATIONS_NOTE,
    )
    db.add(packet)

    builder = _Builder(packet_id, project_id)
    _build_sections(db, project_id, builder)
    for section in builder.sections:
        db.add(section)
    for item in builder.items:
        db.add(item)
    for link in builder.links:
        db.add(link)

    _audit(
        db,
        project_id=project_id,
        event_type="review_packet_generated",
        related_entity_type="review_packet",
        related_entity_id=packet_id,
        description=(
            f"Review-support packet draft generated with "
            f"{len(builder.sections)} sections and {len(builder.items)} items."
        ),
        metadata={
            "packet_id": packet_id,
            "section_count": len(builder.sections),
            "item_count": len(builder.items),
            "evidence_link_count": len(builder.links),
        },
    )
    # Record advisory usage for the generated packet (best-effort, skips the demo
    # organization). Used by usage summaries and enforcement counting.
    usage_service.record_usage_safe(
        db,
        category="review_packet_generated",
        organization_id=project.organization_id,
        project_id=project_id,
    )
    db.commit()
    db.refresh(packet)
    return packet


def ensure_packet(db: Session, project_id: str) -> None:
    """Generate a packet once if none exists for the project.

    Used at startup so the read endpoints and frontend have a packet without a
    manual generate call. Gated on no packet existing, so it does not regenerate
    on every restart.
    """

    if db.get(models.Project, project_id) is None:
        return
    existing = (
        db.query(models.ReviewPacket)
        .filter(models.ReviewPacket.project_id == project_id)
        .first()
    )
    if existing is None:
        generate_review_packet(db, project_id)
