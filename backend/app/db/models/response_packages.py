"""Response packages bounded context: draft external response packages with sections, items, evidence links, attachments, and actions."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.database import Base
from app.db.models.shared import _utcnow

class ResponsePackage(Base):
    """A draft external review response package for a project.

    Phase 10 turns ready-for-handoff workflow items into a structured draft
    response package a human reviewer can prepare for an applicant, design
    engineer, municipal reviewer, or internal review team. The package supports
    drafting external communication. It does not send email, approve plans,
    certify compliance, stamp drawings, verify CAD, validate the design, or make
    final engineering decisions. Every item stays under human review.
    """

    __tablename__ = "response_packages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    response_package_id: Mapped[str] = mapped_column(
        String, unique=True, nullable=False
    )
    project_id: Mapped[str] = mapped_column(
        ForeignKey("projects.project_id"), nullable=False
    )
    source_packet_id: Mapped[str | None] = mapped_column(String, nullable=True)
    title: Mapped[str] = mapped_column(String, nullable=False)
    audience_type: Mapped[str] = mapped_column(String, nullable=False)
    status: Mapped[str] = mapped_column(String, nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    draft_intro: Mapped[str] = mapped_column(Text, nullable=False)
    draft_closing: Mapped[str] = mapped_column(Text, nullable=False)
    limitations_note: Mapped[str] = mapped_column(Text, nullable=False)
    created_by: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=_utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=_utcnow
    )


class ResponsePackageSection(Base):
    """A section of a response package, grouping items by topic."""

    __tablename__ = "response_package_sections"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    section_id: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    response_package_id: Mapped[str] = mapped_column(
        ForeignKey("response_packages.response_package_id"), nullable=False
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


class ResponsePackageItem(Base):
    """A single draft response item, traceable to its workflow and packet item."""

    __tablename__ = "response_package_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    item_id: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    response_package_id: Mapped[str] = mapped_column(
        ForeignKey("response_packages.response_package_id"), nullable=False
    )
    section_id: Mapped[str] = mapped_column(
        ForeignKey("response_package_sections.section_id"), nullable=False
    )
    workflow_item_id: Mapped[str | None] = mapped_column(String, nullable=True)
    packet_item_id: Mapped[str | None] = mapped_column(String, nullable=True)
    title: Mapped[str] = mapped_column(String, nullable=False)
    draft_text: Mapped[str] = mapped_column(Text, nullable=False)
    reviewer_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    severity: Mapped[str] = mapped_column(String, nullable=False)
    status: Mapped[str] = mapped_column(String, nullable=False)
    source_type: Mapped[str] = mapped_column(String, nullable=False)
    source_id: Mapped[str | None] = mapped_column(String, nullable=True)
    assigned_role: Mapped[str] = mapped_column(String, nullable=False)
    requires_human_review: Mapped[bool] = mapped_column(default=True)
    display_order: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=_utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=_utcnow
    )


class ResponsePackageEvidenceLink(Base):
    """A link from a response item to a source evidence entity."""

    __tablename__ = "response_package_evidence_links"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    evidence_link_id: Mapped[str] = mapped_column(
        String, unique=True, nullable=False
    )
    response_package_id: Mapped[str] = mapped_column(
        ForeignKey("response_packages.response_package_id"), nullable=False
    )
    response_item_id: Mapped[str] = mapped_column(
        ForeignKey("response_package_items.item_id"), nullable=False
    )
    evidence_type: Mapped[str] = mapped_column(String, nullable=False)
    evidence_id: Mapped[str] = mapped_column(String, nullable=False)
    relationship: Mapped[str] = mapped_column(String, nullable=False)
    label: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=_utcnow
    )


class ResponsePackageAttachment(Base):
    """A suggested attachment in the response package attachment checklist."""

    __tablename__ = "response_package_attachments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    attachment_id: Mapped[str] = mapped_column(
        String, unique=True, nullable=False
    )
    response_package_id: Mapped[str] = mapped_column(
        ForeignKey("response_packages.response_package_id"), nullable=False
    )
    label: Mapped[str] = mapped_column(String, nullable=False)
    attachment_type: Mapped[str] = mapped_column(String, nullable=False)
    source_type: Mapped[str] = mapped_column(String, nullable=False)
    source_id: Mapped[str | None] = mapped_column(String, nullable=True)
    included: Mapped[bool] = mapped_column(default=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    display_order: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=_utcnow
    )


class ResponsePackageAction(Base):
    """A persisted reviewer action on a response package or response item.

    There is no action called approve, and no action approves, certifies,
    verifies, or validates anything.
    """

    __tablename__ = "response_package_actions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    action_id: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    response_package_id: Mapped[str] = mapped_column(
        ForeignKey("response_packages.response_package_id"), nullable=False
    )
    response_item_id: Mapped[str | None] = mapped_column(String, nullable=True)
    action_type: Mapped[str] = mapped_column(String, nullable=False)
    previous_status: Mapped[str] = mapped_column(String, nullable=False)
    new_status: Mapped[str] = mapped_column(String, nullable=False)
    reviewer_note: Mapped[str] = mapped_column(Text, nullable=False)
    reviewer_name: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=_utcnow
    )
