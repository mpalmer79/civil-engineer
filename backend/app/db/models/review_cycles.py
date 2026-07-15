"""Review cycles bounded context: review rounds, resubmittals, applicant responses, revision comparisons, and carry-forwards."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import JSON, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.database import Base
from app.db.models.shared import _utcnow

class ReviewCycle(Base):
    """One round of review for a project (initial review, resubmittal, and so on)."""

    __tablename__ = "review_cycles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    review_cycle_id: Mapped[str] = mapped_column(
        String, unique=True, nullable=False
    )
    project_id: Mapped[str] = mapped_column(
        ForeignKey("projects.project_id"), nullable=False
    )
    cycle_number: Mapped[int] = mapped_column(Integer, default=1)
    cycle_name: Mapped[str] = mapped_column(String, nullable=False)
    status: Mapped[str] = mapped_column(String, nullable=False)
    started_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    source_response_package_id: Mapped[str | None] = mapped_column(
        String, nullable=True
    )
    source_workflow_board_id: Mapped[str | None] = mapped_column(
        String, nullable=True
    )
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    requires_human_review: Mapped[bool] = mapped_column(default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)


class ResubmittalPackage(Base):
    """A resubmittal returned by an applicant or design engineer for a round."""

    __tablename__ = "resubmittal_packages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    resubmittal_package_id: Mapped[str] = mapped_column(
        String, unique=True, nullable=False
    )
    project_id: Mapped[str] = mapped_column(
        ForeignKey("projects.project_id"), nullable=False
    )
    review_cycle_id: Mapped[str] = mapped_column(String, nullable=False)
    package_name: Mapped[str] = mapped_column(String, nullable=False)
    submitted_by: Mapped[str] = mapped_column(String, nullable=False)
    submitted_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    received_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)
    status: Mapped[str] = mapped_column(String, nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    reviewer_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    requires_human_review: Mapped[bool] = mapped_column(default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)


class ResubmittalDocument(Base):
    """A document or CAD file linked to a resubmittal package."""

    __tablename__ = "resubmittal_documents"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    resubmittal_document_id: Mapped[str] = mapped_column(
        String, unique=True, nullable=False
    )
    project_id: Mapped[str] = mapped_column(
        ForeignKey("projects.project_id"), nullable=False
    )
    review_cycle_id: Mapped[str] = mapped_column(String, nullable=False)
    resubmittal_package_id: Mapped[str] = mapped_column(
        ForeignKey("resubmittal_packages.resubmittal_package_id"), nullable=False
    )
    document_type: Mapped[str] = mapped_column(String, nullable=False)
    source_type: Mapped[str] = mapped_column(String, nullable=False)
    source_id: Mapped[str | None] = mapped_column(String, nullable=True)
    file_name: Mapped[str | None] = mapped_column(String, nullable=True)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)


class ApplicantResponse(Base):
    """An applicant or design engineer response note tied to a resubmittal."""

    __tablename__ = "applicant_responses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    applicant_response_id: Mapped[str] = mapped_column(
        String, unique=True, nullable=False
    )
    project_id: Mapped[str] = mapped_column(
        ForeignKey("projects.project_id"), nullable=False
    )
    review_cycle_id: Mapped[str] = mapped_column(String, nullable=False)
    resubmittal_package_id: Mapped[str] = mapped_column(String, nullable=False)
    response_text: Mapped[str] = mapped_column(Text, nullable=False)
    response_topic: Mapped[str] = mapped_column(String, nullable=False)
    submitted_by: Mapped[str] = mapped_column(String, nullable=False)
    target_response_item_id: Mapped[str | None] = mapped_column(
        String, nullable=True
    )
    target_workflow_item_id: Mapped[str | None] = mapped_column(
        String, nullable=True
    )
    status: Mapped[str] = mapped_column(String, nullable=False)
    reviewer_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    requires_human_review: Mapped[bool] = mapped_column(default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)


class ApplicantResponseMapping(Base):
    """A review-support mapping between an applicant response and a prior item."""

    __tablename__ = "applicant_response_mappings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    mapping_id: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    project_id: Mapped[str] = mapped_column(
        ForeignKey("projects.project_id"), nullable=False
    )
    review_cycle_id: Mapped[str] = mapped_column(String, nullable=False)
    applicant_response_id: Mapped[str] = mapped_column(String, nullable=False)
    response_package_item_id: Mapped[str | None] = mapped_column(
        String, nullable=True
    )
    workflow_item_id: Mapped[str | None] = mapped_column(String, nullable=True)
    response_resolution_record_id: Mapped[str | None] = mapped_column(
        String, nullable=True
    )
    mapping_confidence: Mapped[str] = mapped_column(String, nullable=False)
    mapping_reason: Mapped[str] = mapped_column(Text, nullable=False)
    requires_human_review: Mapped[bool] = mapped_column(default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)


class RevisionComparisonRun(Base):
    """A comparison of extracted DXF metadata between two parse runs."""

    __tablename__ = "revision_comparison_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    comparison_run_id: Mapped[str] = mapped_column(
        String, unique=True, nullable=False
    )
    project_id: Mapped[str] = mapped_column(
        ForeignKey("projects.project_id"), nullable=False
    )
    review_cycle_id: Mapped[str] = mapped_column(String, nullable=False)
    resubmittal_package_id: Mapped[str | None] = mapped_column(
        String, nullable=True
    )
    previous_parse_run_id: Mapped[str] = mapped_column(String, nullable=False)
    current_parse_run_id: Mapped[str] = mapped_column(String, nullable=False)
    status: Mapped[str] = mapped_column(String, nullable=False)
    started_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    compared_layer_count: Mapped[int] = mapped_column(Integer, default=0)
    compared_text_count: Mapped[int] = mapped_column(Integer, default=0)
    added_count: Mapped[int] = mapped_column(Integer, default=0)
    removed_count: Mapped[int] = mapped_column(Integer, default=0)
    changed_count: Mapped[int] = mapped_column(Integer, default=0)
    unchanged_count: Mapped[int] = mapped_column(Integer, default=0)
    warning_count: Mapped[int] = mapped_column(Integer, default=0)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    limitations_note: Mapped[str] = mapped_column(Text, nullable=False)
    requires_human_review: Mapped[bool] = mapped_column(default=True)


class RevisionChangeRecord(Base):
    """A single review-support difference between two DXF parse rounds."""

    __tablename__ = "revision_change_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    change_record_id: Mapped[str] = mapped_column(
        String, unique=True, nullable=False
    )
    project_id: Mapped[str] = mapped_column(
        ForeignKey("projects.project_id"), nullable=False
    )
    review_cycle_id: Mapped[str] = mapped_column(String, nullable=False)
    comparison_run_id: Mapped[str] = mapped_column(
        ForeignKey("revision_comparison_runs.comparison_run_id"), nullable=False
    )
    change_type: Mapped[str] = mapped_column(String, nullable=False)
    source_category: Mapped[str] = mapped_column(String, nullable=False)
    previous_value: Mapped[str | None] = mapped_column(Text, nullable=True)
    current_value: Mapped[str | None] = mapped_column(Text, nullable=True)
    normalized_key: Mapped[str] = mapped_column(String, nullable=False)
    layer_name: Mapped[str | None] = mapped_column(String, nullable=True)
    reference_type: Mapped[str | None] = mapped_column(String, nullable=True)
    severity: Mapped[str] = mapped_column(String, nullable=False)
    linked_cad_review_finding_id: Mapped[str | None] = mapped_column(
        String, nullable=True
    )
    linked_workflow_item_id: Mapped[str | None] = mapped_column(
        String, nullable=True
    )
    reviewer_status: Mapped[str] = mapped_column(String, nullable=False)
    reviewer_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    requires_human_review: Mapped[bool] = mapped_column(default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)


class IssueCarryForward(Base):
    """An unresolved review-support item carried forward into a review cycle."""

    __tablename__ = "issue_carry_forwards"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    carry_forward_id: Mapped[str] = mapped_column(
        String, unique=True, nullable=False
    )
    project_id: Mapped[str] = mapped_column(
        ForeignKey("projects.project_id"), nullable=False
    )
    review_cycle_id: Mapped[str] = mapped_column(String, nullable=False)
    source_workflow_item_id: Mapped[str | None] = mapped_column(
        String, nullable=True
    )
    source_response_item_id: Mapped[str | None] = mapped_column(
        String, nullable=True
    )
    source_cad_finding_id: Mapped[str | None] = mapped_column(
        String, nullable=True
    )
    source_revision_change_id: Mapped[str | None] = mapped_column(
        String, nullable=True
    )
    title: Mapped[str] = mapped_column(String, nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    carried_forward_status: Mapped[str] = mapped_column(String, nullable=False)
    target_workflow_item_id: Mapped[str | None] = mapped_column(
        String, nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)
    reviewer_name: Mapped[str] = mapped_column(String, nullable=False)
    reviewer_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    requires_human_review: Mapped[bool] = mapped_column(default=True)


class ResponseResolutionRecord(Base):
    """A reviewer's review-support resolution view of an item within a cycle."""

    __tablename__ = "response_resolution_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    resolution_record_id: Mapped[str] = mapped_column(
        String, unique=True, nullable=False
    )
    project_id: Mapped[str] = mapped_column(
        ForeignKey("projects.project_id"), nullable=False
    )
    review_cycle_id: Mapped[str] = mapped_column(String, nullable=False)
    response_package_item_id: Mapped[str | None] = mapped_column(
        String, nullable=True
    )
    workflow_item_id: Mapped[str | None] = mapped_column(String, nullable=True)
    applicant_response_id: Mapped[str | None] = mapped_column(
        String, nullable=True
    )
    revision_change_record_id: Mapped[str | None] = mapped_column(
        String, nullable=True
    )
    status: Mapped[str] = mapped_column(String, nullable=False)
    reviewer_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    reviewer_name: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)
    requires_human_review: Mapped[bool] = mapped_column(default=True)


class NextCyclePreparation(Base):
    """A review-support summary of what should move into the next review round."""

    __tablename__ = "next_cycle_preparations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    next_cycle_preparation_id: Mapped[str] = mapped_column(
        String, unique=True, nullable=False
    )
    project_id: Mapped[str] = mapped_column(
        ForeignKey("projects.project_id"), nullable=False
    )
    review_cycle_id: Mapped[str] = mapped_column(String, nullable=False)
    status: Mapped[str] = mapped_column(String, nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    carried_forward_count: Mapped[int] = mapped_column(Integer, default=0)
    needs_more_information_count: Mapped[int] = mapped_column(Integer, default=0)
    reviewer_checked_count: Mapped[int] = mapped_column(Integer, default=0)
    next_response_package_ready: Mapped[bool] = mapped_column(default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)
    requires_human_review: Mapped[bool] = mapped_column(default=True)


class ResubmittalRound(Base):
    """A registered resubmittal round for a project (Sprint 7).

    A resubmittal round records an applicant submission of revised materials for
    reviewer review. It tracks round handling only; it never decides whether the
    resubmittal satisfies engineering requirements and never resolves or closes
    anything.
    """

    __tablename__ = "resubmittal_rounds"

    resubmittal_round_id: Mapped[str] = mapped_column(String, primary_key=True)
    project_id: Mapped[str] = mapped_column(
        ForeignKey("projects.project_id"), nullable=False
    )
    response_matrix_id: Mapped[str | None] = mapped_column(
        String, nullable=True
    )
    round_number: Mapped[int] = mapped_column(Integer, nullable=False)
    round_label: Mapped[str] = mapped_column(String, default="")
    received_at: Mapped[datetime | None] = mapped_column(
        DateTime, nullable=True
    )
    submitted_by_name: Mapped[str | None] = mapped_column(String, nullable=True)
    submitted_by_organization: Mapped[str | None] = mapped_column(
        String, nullable=True
    )
    status: Mapped[str] = mapped_column(String, default="round_registered")
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    document_ids: Mapped[list] = mapped_column(JSON, default=list)
    carried_forward_item_ids: Mapped[list] = mapped_column(JSON, default=list)
    source_mode: Mapped[str] = mapped_column(String, default="user_created")
    organization_id: Mapped[str | None] = mapped_column(String, nullable=True)
    created_by_user_id: Mapped[str | None] = mapped_column(
        String, nullable=True
    )
    created_by_name: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)
