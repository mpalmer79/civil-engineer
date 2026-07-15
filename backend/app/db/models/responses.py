"""Responses bounded context: response matrices, reviewer response packages, and comment letter drafts."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import JSON, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base
from app.db.models.shared import _utcnow

class ResponseMatrix(Base):
    """A reviewer-controlled applicant response matrix for a project (Sprint 7).

    A response matrix organizes review-support findings and checklist items into
    rows that track applicant responses across resubmittal rounds. It helps a
    reviewer organize the review loop. It never decides whether a response
    satisfies engineering requirements, never resolves or closes an issue, and
    never approves, certifies, or validates anything. Every status is
    review-support only.
    """

    __tablename__ = "response_matrices"

    response_matrix_id: Mapped[str] = mapped_column(String, primary_key=True)
    project_id: Mapped[str] = mapped_column(
        ForeignKey("projects.project_id"), nullable=False
    )
    name: Mapped[str] = mapped_column(String, nullable=False)
    current_round_number: Mapped[int] = mapped_column(Integer, default=1)
    status: Mapped[str] = mapped_column(String, default="matrix_started")
    source_mode: Mapped[str] = mapped_column(String, default="user_created")
    organization_id: Mapped[str | None] = mapped_column(String, nullable=True)
    created_by_user_id: Mapped[str | None] = mapped_column(
        String, nullable=True
    )
    created_by_name: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)

    items: Mapped[list["ResponseMatrixItem"]] = relationship(
        back_populates="matrix"
    )


class ResponseMatrixItem(Base):
    """A row in an applicant response matrix (Sprint 7).

    Each item carries the reviewer comment draft, the requested evidence, the
    recorded applicant response text, and reviewer-controlled applicant response,
    reviewer follow-up, and carry-forward statuses. An applicant response is
    recorded as submitted content for reviewer review, never as proof and never
    as a final outcome.
    """

    __tablename__ = "response_matrix_items"

    response_matrix_item_id: Mapped[str] = mapped_column(
        String, primary_key=True
    )
    response_matrix_id: Mapped[str] = mapped_column(
        ForeignKey("response_matrices.response_matrix_id"), nullable=False
    )
    project_id: Mapped[str] = mapped_column(
        ForeignKey("projects.project_id"), nullable=False
    )
    source_finding_id: Mapped[str | None] = mapped_column(
        ForeignKey("findings.finding_id"), nullable=True
    )
    source_checklist_item_id: Mapped[str | None] = mapped_column(
        String, nullable=True
    )
    source_citation_id: Mapped[str | None] = mapped_column(
        String, nullable=True
    )
    item_number: Mapped[str | None] = mapped_column(String, nullable=True)
    category: Mapped[str] = mapped_column(String, default="general")
    reviewer_comment_draft: Mapped[str] = mapped_column(Text, default="")
    requested_evidence: Mapped[str | None] = mapped_column(Text, nullable=True)
    applicant_response_text: Mapped[str | None] = mapped_column(
        Text, nullable=True
    )
    applicant_response_status: Mapped[str] = mapped_column(
        String, default="response_not_requested"
    )
    reviewer_follow_up_status: Mapped[str] = mapped_column(
        String, default="not_reviewed"
    )
    carry_forward_status: Mapped[str] = mapped_column(
        String, default="not_carried_forward"
    )
    current_round_number: Mapped[int] = mapped_column(Integer, default=1)
    carried_from_round_number: Mapped[int | None] = mapped_column(
        Integer, nullable=True
    )
    carried_to_round_number: Mapped[int | None] = mapped_column(
        Integer, nullable=True
    )
    related_document_ids: Mapped[list] = mapped_column(JSON, default=list)
    related_citation_ids: Mapped[list] = mapped_column(JSON, default=list)
    reviewer_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    applicant_placeholder_user_id: Mapped[str | None] = mapped_column(
        String, nullable=True
    )
    created_by_user_id: Mapped[str | None] = mapped_column(
        String, nullable=True
    )
    created_by_name: Mapped[str | None] = mapped_column(String, nullable=True)
    updated_by_user_id: Mapped[str | None] = mapped_column(
        String, nullable=True
    )
    updated_by_name: Mapped[str | None] = mapped_column(String, nullable=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)

    matrix: Mapped["ResponseMatrix"] = relationship(back_populates="items")


class MatrixItemDocumentLink(Base):
    """A reviewer link between a matrix item and a document (Sprint 7).

    Links an applicant response document, a revised plan or report reference, or
    supporting evidence to a response matrix item, optionally within a
    resubmittal round. A link is a reviewer-selected source reference, not proof
    of correctness, and it never changes an item to a final outcome.
    """

    __tablename__ = "matrix_item_document_links"

    matrix_item_document_link_id: Mapped[str] = mapped_column(
        String, primary_key=True
    )
    project_id: Mapped[str] = mapped_column(
        ForeignKey("projects.project_id"), nullable=False
    )
    response_matrix_item_id: Mapped[str] = mapped_column(
        ForeignKey("response_matrix_items.response_matrix_item_id"),
        nullable=False,
    )
    document_id: Mapped[str] = mapped_column(
        ForeignKey("documents.document_id"), nullable=False
    )
    resubmittal_round_id: Mapped[str | None] = mapped_column(
        String, nullable=True
    )
    link_type: Mapped[str] = mapped_column(
        String, default="applicant_response_document"
    )
    reviewer_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_by_user_id: Mapped[str | None] = mapped_column(
        String, nullable=True
    )
    created_by_name: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)


class ReviewerResponsePackage(Base):
    """A reviewer-controlled response package for a real project (Sprint 8).

    A response package assembles reviewer-selected records (findings, checklist
    items, response matrix items, citations, document references, resubmittal
    summaries, and manual reviewer notes) into a controlled communication
    artifact and a deterministic comment letter draft. Issuance records that a
    reviewer issued a communication. It never approves a project, certifies
    compliance, verifies CAD, validates design, declares safety, resolves an
    issue, or closes an issue. Every status is review-support only.
    """

    __tablename__ = "reviewer_response_packages"

    response_package_id: Mapped[str] = mapped_column(String, primary_key=True)
    project_id: Mapped[str] = mapped_column(
        ForeignKey("projects.project_id"), nullable=False
    )
    response_matrix_id: Mapped[str | None] = mapped_column(String, nullable=True)
    resubmittal_round_id: Mapped[str | None] = mapped_column(
        String, nullable=True
    )
    package_title: Mapped[str] = mapped_column(String, nullable=False)
    package_number: Mapped[int] = mapped_column(Integer, default=1)
    revision_number: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[str] = mapped_column(String, default="package_draft")
    package_type: Mapped[str] = mapped_column(
        String, default="initial_review_comment_letter"
    )
    source_mode: Mapped[str] = mapped_column(String, default="user_created")
    prepared_by_user_id: Mapped[str | None] = mapped_column(
        String, nullable=True
    )
    prepared_by_name: Mapped[str | None] = mapped_column(String, nullable=True)
    issued_by_user_id: Mapped[str | None] = mapped_column(String, nullable=True)
    issued_by_name: Mapped[str | None] = mapped_column(String, nullable=True)
    organization_id: Mapped[str | None] = mapped_column(String, nullable=True)
    issued_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)

    items: Mapped[list["ReviewerResponsePackageItem"]] = relationship(
        back_populates="package"
    )


class ReviewerResponsePackageItem(Base):
    """A single reviewer-selected record included in a response package."""

    __tablename__ = "reviewer_response_package_items"

    response_package_item_id: Mapped[str] = mapped_column(
        String, primary_key=True
    )
    response_package_id: Mapped[str] = mapped_column(
        ForeignKey("reviewer_response_packages.response_package_id"),
        nullable=False,
    )
    project_id: Mapped[str] = mapped_column(
        ForeignKey("projects.project_id"), nullable=False
    )
    source_type: Mapped[str] = mapped_column(String, nullable=False)
    source_finding_id: Mapped[str | None] = mapped_column(String, nullable=True)
    source_checklist_item_id: Mapped[str | None] = mapped_column(
        String, nullable=True
    )
    source_matrix_item_id: Mapped[str | None] = mapped_column(
        String, nullable=True
    )
    source_citation_id: Mapped[str | None] = mapped_column(
        String, nullable=True
    )
    source_document_id: Mapped[str | None] = mapped_column(
        String, nullable=True
    )
    item_number: Mapped[str | None] = mapped_column(String, nullable=True)
    category: Mapped[str | None] = mapped_column(String, nullable=True)
    reviewer_comment_text: Mapped[str] = mapped_column(Text, default="")
    applicant_response_summary: Mapped[str | None] = mapped_column(
        Text, nullable=True
    )
    reviewer_follow_up_text: Mapped[str | None] = mapped_column(
        Text, nullable=True
    )
    requested_evidence: Mapped[str | None] = mapped_column(Text, nullable=True)
    citation_reference: Mapped[str | None] = mapped_column(Text, nullable=True)
    include_in_letter: Mapped[bool] = mapped_column(default=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    item_status: Mapped[str] = mapped_column(String, default="item_draft")
    created_by_user_id: Mapped[str | None] = mapped_column(
        String, nullable=True
    )
    created_by_name: Mapped[str | None] = mapped_column(String, nullable=True)
    updated_by_name: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)

    package: Mapped["ReviewerResponsePackage"] = relationship(
        back_populates="items"
    )


class CommentLetterDraft(Base):
    """A deterministic, reviewer-editable comment letter draft for a package.

    The draft is generated from package items using fixed templates only. There
    are no live AI calls. It carries a fixed review-support boundary statement
    that is rendered at preview time and is never an editable section. The draft
    is a reviewer communication artifact, not an approval, certification, or issue
    closure.
    """

    __tablename__ = "comment_letter_drafts"

    comment_letter_draft_id: Mapped[str] = mapped_column(
        String, primary_key=True
    )
    response_package_id: Mapped[str] = mapped_column(
        ForeignKey("reviewer_response_packages.response_package_id"),
        nullable=False,
    )
    project_id: Mapped[str] = mapped_column(
        ForeignKey("projects.project_id"), nullable=False
    )
    title: Mapped[str] = mapped_column(String, nullable=False)
    recipient_name: Mapped[str | None] = mapped_column(String, nullable=True)
    recipient_organization: Mapped[str | None] = mapped_column(
        String, nullable=True
    )
    subject_line: Mapped[str] = mapped_column(String, default="")
    introduction_text: Mapped[str] = mapped_column(Text, default="")
    project_summary_text: Mapped[str | None] = mapped_column(
        Text, nullable=True
    )
    review_scope_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    comment_items_text: Mapped[str] = mapped_column(Text, default="")
    resubmittal_summary_text: Mapped[str | None] = mapped_column(
        Text, nullable=True
    )
    closing_text: Mapped[str] = mapped_column(Text, default="")
    status: Mapped[str] = mapped_column(String, default="draft_created")
    revision_number: Mapped[int] = mapped_column(Integer, default=0)
    created_by_user_id: Mapped[str | None] = mapped_column(
        String, nullable=True
    )
    created_by_name: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)


class ReviewerResponsePackageRevision(Base):
    """A preserved record of a response package revision (Sprint 8).

    Creating a revision never overwrites a prior issued package record. It records
    the prior status and the revision number so the issued history is preserved.
    """

    __tablename__ = "reviewer_response_package_revisions"

    response_package_revision_id: Mapped[str] = mapped_column(
        String, primary_key=True
    )
    response_package_id: Mapped[str] = mapped_column(
        ForeignKey("reviewer_response_packages.response_package_id"),
        nullable=False,
    )
    project_id: Mapped[str] = mapped_column(
        ForeignKey("projects.project_id"), nullable=False
    )
    revision_number: Mapped[int] = mapped_column(Integer, nullable=False)
    revision_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    prior_status: Mapped[str | None] = mapped_column(String, nullable=True)
    created_by_user_id: Mapped[str | None] = mapped_column(
        String, nullable=True
    )
    created_by_name: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)
