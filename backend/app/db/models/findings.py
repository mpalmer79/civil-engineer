"""Findings bounded context: findings, finding sources, AI review runs, draft findings, and review actions."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import JSON, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base
from app.db.models.shared import _utcnow

class Finding(Base):
    __tablename__ = "findings"

    finding_id: Mapped[str] = mapped_column(String, primary_key=True)
    project_id: Mapped[str] = mapped_column(
        ForeignKey("projects.project_id"), nullable=False
    )
    planted_issue: Mapped[str] = mapped_column(String, nullable=False)
    title: Mapped[str] = mapped_column(String, nullable=False)
    category: Mapped[str] = mapped_column(String, nullable=False)
    risk_level: Mapped[str] = mapped_column(String, nullable=False)
    expected_status: Mapped[str] = mapped_column(String, nullable=False)
    evidence_to_find: Mapped[str] = mapped_column(Text, nullable=False)
    reason_it_matters: Mapped[str] = mapped_column(Text, nullable=False)
    recommended_human_action: Mapped[str] = mapped_column(Text, nullable=False)
    human_review_status: Mapped[str] = mapped_column(String, nullable=False)
    related_checklist_items: Mapped[list] = mapped_column(JSON, default=list)
    related_documents: Mapped[list] = mapped_column(JSON, default=list)

    # Production foundation fields (Sprint 1). finding_origin distinguishes a
    # seeded demo finding from a reviewer-created one. Every reviewer-created
    # finding stays under human review and never carries final-decision language.
    source_mode: Mapped[str] = mapped_column(String, default="demo_fixture")
    finding_origin: Mapped[str] = mapped_column(String, default="seeded_demo")
    evidence_status: Mapped[str | None] = mapped_column(String, nullable=True)
    reviewer_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    applicant_response_summary: Mapped[str | None] = mapped_column(
        Text, nullable=True
    )
    carry_forward_status: Mapped[str | None] = mapped_column(
        String, nullable=True
    )
    created_by_name: Mapped[str | None] = mapped_column(String, nullable=True)
    created_by_actor_id: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    updated_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    project: Mapped["Project"] = relationship(back_populates="findings")


class FindingSource(Base):
    """Source evidence linking a review-support finding to a document chunk.

    A finding source is not a conclusion. It records where in the submitted
    documents a reviewer can inspect evidence relevant to a finding, and what
    role that evidence plays (supports, shows missing evidence, shows a
    conflict, context only, or requires reviewer confirmation).
    """

    __tablename__ = "finding_sources"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    finding_source_id: Mapped[str] = mapped_column(
        String, unique=True, nullable=False
    )
    finding_id: Mapped[str] = mapped_column(
        ForeignKey("findings.finding_id"), nullable=False
    )
    document_id: Mapped[str] = mapped_column(
        ForeignKey("documents.document_id"), nullable=False
    )
    chunk_id: Mapped[str | None] = mapped_column(String, nullable=True)
    page_number: Mapped[int | None] = mapped_column(Integer, nullable=True)
    excerpt: Mapped[str] = mapped_column(Text, nullable=False)
    evidence_role: Mapped[str] = mapped_column(String, nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    # Sprint 1 manual evidence reference fields. A reviewer may add a basic
    # review-support reference to a sheet or section on an uploaded document
    # before real document chunks exist. These are nullable so seeded Phase 3
    # finding sources keep working. source_mode distinguishes them.
    sheet_number: Mapped[str | None] = mapped_column(String, nullable=True)
    section_label: Mapped[str | None] = mapped_column(String, nullable=True)
    source_mode: Mapped[str] = mapped_column(String, default="demo_fixture")
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=_utcnow
    )


class AIReviewRun(Base):
    """An execution of the AI Review Assistant over a project's checklist.

    A run records the provider, model, prompt version, and outcome counts so the
    workflow is auditable. The AI does not make final engineering decisions; it
    produces draft review-support findings that require human review.
    """

    __tablename__ = "ai_review_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    review_run_id: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    project_id: Mapped[str] = mapped_column(
        ForeignKey("projects.project_id"), nullable=False
    )
    run_type: Mapped[str] = mapped_column(String, nullable=False)
    provider: Mapped[str] = mapped_column(String, nullable=False)
    model_name: Mapped[str] = mapped_column(String, nullable=False)
    status: Mapped[str] = mapped_column(String, nullable=False)
    prompt_version: Mapped[str] = mapped_column(String, nullable=False)
    checklist_item_count: Mapped[int] = mapped_column(Integer, default=0)
    draft_findings_created: Mapped[int] = mapped_column(Integer, default=0)
    safety_failures: Mapped[int] = mapped_column(Integer, default=0)
    started_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=_utcnow
    )


class AIDraftFinding(Base):
    """An AI-drafted draft review-support finding.

    A draft finding is not a final engineering conclusion. It is generated from
    retrieved source evidence, validated against a strict schema and safety
    checks, and always requires human review before any action.
    """

    __tablename__ = "ai_draft_findings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    draft_finding_id: Mapped[str] = mapped_column(
        String, unique=True, nullable=False
    )
    review_run_id: Mapped[str] = mapped_column(
        ForeignKey("ai_review_runs.review_run_id"), nullable=False
    )
    project_id: Mapped[str] = mapped_column(
        ForeignKey("projects.project_id"), nullable=False
    )
    checklist_item_id: Mapped[str] = mapped_column(String, nullable=False)
    finding_type: Mapped[str] = mapped_column(String, nullable=False)
    title: Mapped[str] = mapped_column(String, nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    risk_level: Mapped[str] = mapped_column(String, nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    status: Mapped[str] = mapped_column(String, nullable=False)
    recommended_human_action: Mapped[str] = mapped_column(Text, nullable=False)
    source_chunk_ids: Mapped[list] = mapped_column(JSON, default=list)
    validation_status: Mapped[str] = mapped_column(String, nullable=False)
    safety_check_status: Mapped[str] = mapped_column(String, nullable=False)
    validation_errors: Mapped[list] = mapped_column(JSON, default=list)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=_utcnow
    )


class HumanReviewAction(Base):
    """A persisted human review decision on an AI draft finding.

    A review action records what a human reviewer did with a draft finding
    (accepted, edited, rejected, escalated, marked unclear, or requested more
    information), the status transition it produced, and any edited text. No
    action approves, certifies, or finalizes an engineering decision. Every
    action keeps the finding under human control.
    """

    __tablename__ = "human_review_actions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    review_action_id: Mapped[str] = mapped_column(
        String, unique=True, nullable=False
    )
    draft_finding_id: Mapped[str] = mapped_column(
        ForeignKey("ai_draft_findings.draft_finding_id"), nullable=False
    )
    project_id: Mapped[str] = mapped_column(
        ForeignKey("projects.project_id"), nullable=False
    )
    review_run_id: Mapped[str] = mapped_column(String, nullable=False)
    reviewer_name: Mapped[str] = mapped_column(String, nullable=False)
    action: Mapped[str] = mapped_column(String, nullable=False)
    reviewer_note: Mapped[str] = mapped_column(Text, nullable=False)
    edited_title: Mapped[str | None] = mapped_column(Text, nullable=True)
    edited_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    edited_recommended_action: Mapped[str | None] = mapped_column(
        Text, nullable=True
    )
    previous_status: Mapped[str] = mapped_column(String, nullable=False)
    new_status: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=_utcnow
    )


class TraceabilityReviewAction(Base):
    """A reviewer-recorded review action on one project traceability row (Phase 4B).

    Project traceability rows are computed read-only from existing links, so they
    have no stable stored primary key. This append-only table stores a reviewer's
    review state for a row, keyed by a stable traceability_row_key derived from the
    row's existing entity IDs (checklist item, evidence citation or candidate,
    finding, and relationship), not by the positional row id.

    A review action records how the reviewer reviewed the link. It never approves a
    plan, certifies compliance, verifies CAD, validates a design, or marks a
    requirement satisfied. reviewer_confirmed_link means the reviewer confirmed the
    link is useful for review only. link_rejected discards the link for review
    without deleting any source record. Recording an action does not mutate the
    checklist item, evidence, finding, workflow item, or packet it references.
    """

    __tablename__ = "traceability_review_actions"

    action_id: Mapped[str] = mapped_column(String, primary_key=True)
    project_id: Mapped[str] = mapped_column(
        ForeignKey("projects.project_id"), nullable=False
    )
    # Stable key derived from the row's existing entity IDs. Used to group a row's
    # action history and to address the row in the review-actions routes.
    traceability_row_key: Mapped[str] = mapped_column(String, nullable=False)
    action_type: Mapped[str] = mapped_column(String, nullable=False)
    reviewer_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_by: Mapped[str] = mapped_column(String, nullable=False)
    # Component IDs kept for transparency and audit, mirroring the row the action
    # was recorded against. All nullable: a no-linked-evidence row carries only a
    # checklist item id.
    checklist_item_id: Mapped[str | None] = mapped_column(String, nullable=True)
    evidence_citation_id: Mapped[str | None] = mapped_column(String, nullable=True)
    evidence_candidate_id: Mapped[str | None] = mapped_column(
        String, nullable=True
    )
    finding_id: Mapped[str | None] = mapped_column(String, nullable=True)
    workflow_item_id: Mapped[str | None] = mapped_column(String, nullable=True)
    review_packet_item_id: Mapped[str | None] = mapped_column(
        String, nullable=True
    )
    relationship_type: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)
