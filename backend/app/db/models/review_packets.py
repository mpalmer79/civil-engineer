"""Review packets bounded context: packet drafts, sections, items, evidence links, and reviewer actions."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.database import Base
from app.db.models.shared import _utcnow

class ReviewPacket(Base):
    """A reviewer-facing review-support packet draft for a project.

    Phase 8 assembles documents, checklist items, findings, plan sheets,
    CAD-aware metadata, hotspots, plan consistency findings, human review
    actions, and audit evidence into a structured review-support packet. The
    packet organizes evidence for a human reviewer. It does not approve plans,
    certify compliance, stamp drawings, verify CAD, validate a design, or make
    final engineering decisions.
    """

    __tablename__ = "review_packets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    packet_id: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    project_id: Mapped[str] = mapped_column(
        ForeignKey("projects.project_id"), nullable=False
    )
    title: Mapped[str] = mapped_column(String, nullable=False)
    packet_type: Mapped[str] = mapped_column(String, nullable=False)
    status: Mapped[str] = mapped_column(String, nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    generated_from_phase: Mapped[str] = mapped_column(String, nullable=False)
    created_by: Mapped[str] = mapped_column(String, nullable=False)
    limitations_note: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=_utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=_utcnow
    )


class ReviewPacketSection(Base):
    """A section of a review packet (for example, plan consistency findings)."""

    __tablename__ = "review_packet_sections"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    section_id: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    packet_id: Mapped[str] = mapped_column(
        ForeignKey("review_packets.packet_id"), nullable=False
    )
    title: Mapped[str] = mapped_column(String, nullable=False)
    section_type: Mapped[str] = mapped_column(String, nullable=False)
    display_order: Mapped[int] = mapped_column(Integer, default=0)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String, nullable=False)
    requires_human_review: Mapped[bool] = mapped_column(default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=_utcnow
    )


class ReviewPacketItem(Base):
    """A single item in a review packet section, linked to a source entity."""

    __tablename__ = "review_packet_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    item_id: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    packet_id: Mapped[str] = mapped_column(
        ForeignKey("review_packets.packet_id"), nullable=False
    )
    section_id: Mapped[str] = mapped_column(
        ForeignKey("review_packet_sections.section_id"), nullable=False
    )
    item_type: Mapped[str] = mapped_column(String, nullable=False)
    title: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    severity: Mapped[str] = mapped_column(String, nullable=False)
    source_type: Mapped[str] = mapped_column(String, nullable=False)
    source_id: Mapped[str | None] = mapped_column(String, nullable=True)
    reviewer_status: Mapped[str] = mapped_column(String, nullable=False)
    reviewer_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    requires_human_review: Mapped[bool] = mapped_column(default=True)
    display_order: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=_utcnow
    )


class ReviewPacketEvidenceLink(Base):
    """A link from a packet item to a source evidence entity."""

    __tablename__ = "review_packet_evidence_links"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    evidence_link_id: Mapped[str] = mapped_column(
        String, unique=True, nullable=False
    )
    packet_id: Mapped[str] = mapped_column(
        ForeignKey("review_packets.packet_id"), nullable=False
    )
    item_id: Mapped[str] = mapped_column(
        ForeignKey("review_packet_items.item_id"), nullable=False
    )
    evidence_type: Mapped[str] = mapped_column(String, nullable=False)
    evidence_id: Mapped[str] = mapped_column(String, nullable=False)
    relationship: Mapped[str] = mapped_column(String, nullable=False)
    label: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=_utcnow
    )


class ReviewPacketReviewerAction(Base):
    """A persisted reviewer action on a review packet item.

    A reviewer may mark an item needs_follow_up, reviewer_checked,
    excluded_from_packet, or needs_more_information. There is no action called
    approve, and no action approves, certifies, verifies, or validates anything.
    """

    __tablename__ = "review_packet_reviewer_actions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    action_id: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    packet_id: Mapped[str] = mapped_column(
        ForeignKey("review_packets.packet_id"), nullable=False
    )
    item_id: Mapped[str] = mapped_column(
        ForeignKey("review_packet_items.item_id"), nullable=False
    )
    action_type: Mapped[str] = mapped_column(String, nullable=False)
    reviewer_note: Mapped[str] = mapped_column(Text, nullable=False)
    previous_status: Mapped[str] = mapped_column(String, nullable=False)
    new_status: Mapped[str] = mapped_column(String, nullable=False)
    reviewer_name: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=_utcnow
    )
