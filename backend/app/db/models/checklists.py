"""Checklists bounded context: checklist items, rule packs, project checklists, and evidence links."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import JSON, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base
from app.db.models.shared import _utcnow

class ChecklistItem(Base):
    __tablename__ = "checklist_items"

    checklist_item_id: Mapped[str] = mapped_column(String, primary_key=True)
    project_id: Mapped[str] = mapped_column(
        ForeignKey("projects.project_id"), nullable=False
    )
    review_domain: Mapped[str] = mapped_column(String, nullable=False)
    category: Mapped[str] = mapped_column(String, nullable=False)
    requirement: Mapped[str] = mapped_column(Text, nullable=False)
    expected_evidence: Mapped[str] = mapped_column(Text, nullable=False)
    supporting_documents: Mapped[list] = mapped_column(JSON, default=list)
    risk_level: Mapped[str] = mapped_column(String, nullable=False)
    applies_when: Mapped[str] = mapped_column(String, nullable=False)
    expected_status_for_brookside_meadows: Mapped[str] = mapped_column(
        String, nullable=False
    )
    planted_issue: Mapped[str | None] = mapped_column(String, nullable=True)

    project: Mapped["Project"] = relationship(back_populates="checklist_items")


class RulePack(Base):
    """A reusable review-support checklist template (Sprint 4).

    A rule pack is a starter template that organizes stormwater review
    requirements for reviewer use. It is not a legal ordinance, not a compliance
    standard, and not a binding requirement set. Applying a rule pack to a
    project never approves plans, certifies compliance, validates design, or
    makes any final engineering decision.
    """

    __tablename__ = "rule_packs"

    rule_pack_id: Mapped[str] = mapped_column(String, primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    jurisdiction_name: Mapped[str] = mapped_column(String, nullable=False)
    review_domain: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    version_label: Mapped[str] = mapped_column(String, default="v1")
    source_mode: Mapped[str] = mapped_column(String, default="seeded_demo")
    is_active: Mapped[bool] = mapped_column(default=True)
    created_by_actor_id: Mapped[str | None] = mapped_column(
        String, nullable=True
    )
    created_by_name: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)

    items: Mapped[list["RulePackItem"]] = relationship(
        back_populates="rule_pack"
    )


class RulePackItem(Base):
    """A single requirement entry in a rule pack (Sprint 4).

    Each item describes a stormwater review requirement and the evidence a
    reviewer would expect to find. It is a review-support prompt, not a legal
    determination and not a compliance standard.
    """

    __tablename__ = "rule_pack_items"

    rule_pack_item_id: Mapped[str] = mapped_column(String, primary_key=True)
    rule_pack_id: Mapped[str] = mapped_column(
        ForeignKey("rule_packs.rule_pack_id"), nullable=False
    )
    item_code: Mapped[str] = mapped_column(String, nullable=False)
    category: Mapped[str] = mapped_column(String, nullable=False)
    requirement_text: Mapped[str] = mapped_column(Text, nullable=False)
    expected_evidence: Mapped[str] = mapped_column(Text, nullable=False)
    applicability_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    risk_level: Mapped[str] = mapped_column(String, default="medium")
    review_domain: Mapped[str] = mapped_column(String, default="stormwater")
    reference_label: Mapped[str | None] = mapped_column(String, nullable=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    is_active: Mapped[bool] = mapped_column(default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)

    rule_pack: Mapped["RulePack"] = relationship(back_populates="items")


class ProjectChecklist(Base):
    """A rule pack applied to a real project as a review-support checklist.

    A project checklist is the reviewer's working copy of a rule pack for one
    project. Its status tracks review progress only; it never records a final
    engineering decision, approval, or compliance state.
    """

    __tablename__ = "project_checklists"

    project_checklist_id: Mapped[str] = mapped_column(String, primary_key=True)
    project_id: Mapped[str] = mapped_column(
        ForeignKey("projects.project_id"), nullable=False
    )
    rule_pack_id: Mapped[str | None] = mapped_column(
        ForeignKey("rule_packs.rule_pack_id"), nullable=True
    )
    name: Mapped[str] = mapped_column(String, nullable=False)
    status: Mapped[str] = mapped_column(String, default="checklist_started")
    source_mode: Mapped[str] = mapped_column(String, default="user_created")
    created_by_actor_id: Mapped[str | None] = mapped_column(
        String, nullable=True
    )
    created_by_name: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)

    items: Mapped[list["ProjectChecklistItem"]] = relationship(
        back_populates="checklist"
    )


class ProjectChecklistItem(Base):
    """A reviewer-controlled checklist item for one project (Sprint 4).

    Each item carries the requirement and expected evidence copied from a rule
    pack item, plus reviewer-controlled applicability, evidence, and review
    statuses. Every status is review-support only. The system never decides that
    an item is satisfied, compliant, or approved; a reviewer must act.
    """

    __tablename__ = "project_checklist_items"

    project_checklist_item_id: Mapped[str] = mapped_column(
        String, primary_key=True
    )
    project_checklist_id: Mapped[str] = mapped_column(
        ForeignKey("project_checklists.project_checklist_id"), nullable=False
    )
    project_id: Mapped[str] = mapped_column(
        ForeignKey("projects.project_id"), nullable=False
    )
    rule_pack_item_id: Mapped[str | None] = mapped_column(
        String, nullable=True
    )
    checklist_item_id: Mapped[str | None] = mapped_column(
        String, nullable=True
    )
    item_code: Mapped[str] = mapped_column(String, nullable=False)
    category: Mapped[str] = mapped_column(String, nullable=False)
    requirement_text: Mapped[str] = mapped_column(Text, nullable=False)
    expected_evidence: Mapped[str] = mapped_column(Text, nullable=False)
    applicability_status: Mapped[str] = mapped_column(
        String, default="needs_reviewer_confirmation"
    )
    evidence_status: Mapped[str] = mapped_column(String, default="not_reviewed")
    review_status: Mapped[str] = mapped_column(String, default="not_started")
    risk_level: Mapped[str] = mapped_column(String, default="medium")
    reviewer_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    related_finding_id: Mapped[str | None] = mapped_column(
        String, nullable=True
    )
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)
    reviewed_by_actor_id: Mapped[str | None] = mapped_column(
        String, nullable=True
    )
    reviewed_by_name: Mapped[str | None] = mapped_column(String, nullable=True)
    reviewed_at: Mapped[datetime | None] = mapped_column(
        DateTime, nullable=True
    )

    checklist: Mapped["ProjectChecklist"] = relationship(
        back_populates="items"
    )


class ChecklistEvidenceLink(Base):
    """A reviewer link between a checklist item and source evidence (Sprint 4).

    Links a checklist item to a document page, an evidence citation, or an
    evidence candidate. A link is a reviewer-selected source reference, not proof
    of correctness, and it never changes a checklist item to a final outcome.
    """

    __tablename__ = "checklist_evidence_links"

    checklist_evidence_link_id: Mapped[str] = mapped_column(
        String, primary_key=True
    )
    project_id: Mapped[str] = mapped_column(
        ForeignKey("projects.project_id"), nullable=False
    )
    project_checklist_item_id: Mapped[str] = mapped_column(
        ForeignKey("project_checklist_items.project_checklist_item_id"),
        nullable=False,
    )
    document_id: Mapped[str] = mapped_column(
        ForeignKey("documents.document_id"), nullable=False
    )
    document_page_id: Mapped[str | None] = mapped_column(
        String, nullable=True
    )
    evidence_citation_id: Mapped[str | None] = mapped_column(
        String, nullable=True
    )
    evidence_candidate_id: Mapped[str | None] = mapped_column(
        String, nullable=True
    )
    page_number: Mapped[int | None] = mapped_column(Integer, nullable=True)
    quoted_excerpt: Mapped[str | None] = mapped_column(Text, nullable=True)
    reviewer_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    link_status: Mapped[str] = mapped_column(
        String, default="reviewer_selected"
    )
    created_by_actor_id: Mapped[str | None] = mapped_column(
        String, nullable=True
    )
    created_by_name: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)
