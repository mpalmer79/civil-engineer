"""SQLAlchemy models for the Civil Engineer AI backend.

The schema includes the Phase 2 core review entities, the Phase 3 source
evidence entities, the Phase 4 AI review entities, the Phase 5 human review and
evaluation entities, the Phase 6 plan sheet and CAD-aware review entities, the
Phase 8 review packet entities, the Phase 9 reviewer workflow board entities,
and the Phase 10 external review response package entities. JSON columns are
used for arrays and nested values during the local prototype phase, with a clean
path to normalization later.
"""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import JSON, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base


def _utcnow() -> datetime:
    """Return a timezone-aware UTC timestamp for column defaults.

    Used instead of datetime.utcnow, which is deprecated on Python 3.12 and
    returns a naive datetime. The stored value and column type are unchanged.
    """

    return datetime.now(timezone.utc)


class Project(Base):
    __tablename__ = "projects"

    project_id: Mapped[str] = mapped_column(String, primary_key=True)
    project_name: Mapped[str] = mapped_column(String, nullable=False)
    project_type: Mapped[str] = mapped_column(String, nullable=False)
    location_context: Mapped[str] = mapped_column(String, nullable=False)
    jurisdiction: Mapped[str] = mapped_column(String, nullable=False)
    review_type: Mapped[str] = mapped_column(String, nullable=False)
    review_domain: Mapped[str] = mapped_column(String, nullable=False)
    acreage: Mapped[float] = mapped_column(Float, nullable=False)
    disturbed_area: Mapped[float] = mapped_column(Float, nullable=False)
    proposed_lots: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(String, nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    site_conditions: Mapped[list] = mapped_column(JSON, default=list)
    proposed_improvements: Mapped[list] = mapped_column(JSON, default=list)
    known_constraints: Mapped[list] = mapped_column(JSON, default=list)

    # Production foundation fields (Sprint 1). All carry safe defaults or are
    # nullable so the seeded Brookside Meadows demo fixture and existing rows
    # keep working without a migration. source_mode distinguishes the seeded
    # demo fixture from a user-created real project record.
    source_mode: Mapped[str] = mapped_column(String, default="demo_fixture")
    created_by_name: Mapped[str | None] = mapped_column(String, nullable=True)
    created_by_actor_id: Mapped[str | None] = mapped_column(String, nullable=True)
    applicant_name: Mapped[str | None] = mapped_column(String, nullable=True)
    applicant_organization: Mapped[str | None] = mapped_column(
        String, nullable=True
    )
    design_engineer_name: Mapped[str | None] = mapped_column(
        String, nullable=True
    )
    design_firm: Mapped[str | None] = mapped_column(String, nullable=True)
    submission_reference: Mapped[str | None] = mapped_column(
        String, nullable=True
    )
    review_round_current: Mapped[int] = mapped_column(Integer, default=1)
    parcel_ids: Mapped[list] = mapped_column(JSON, default=list)
    created_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    updated_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    # Production foundation fields (Sprint 5) for authentication and access
    # control. organization_id and created_by_user_id attribute a real project to
    # an organization and a signed-in user. visibility_mode and demo_public
    # control read access: demo_public projects (the seeded demo) may be read
    # without a login when AUTH_ALLOW_PUBLIC_DEMO is true. All are nullable or
    # defaulted so seeded and Sprint 1 through 4 projects keep working.
    organization_id: Mapped[str | None] = mapped_column(String, nullable=True)
    created_by_user_id: Mapped[str | None] = mapped_column(
        String, nullable=True
    )
    visibility_mode: Mapped[str] = mapped_column(String, default="controlled")
    demo_public: Mapped[bool] = mapped_column(default=False)

    documents: Mapped[list["Document"]] = relationship(back_populates="project")
    checklist_items: Mapped[list["ChecklistItem"]] = relationship(
        back_populates="project"
    )
    findings: Mapped[list["Finding"]] = relationship(back_populates="project")
    audit_events: Mapped[list["AuditEvent"]] = relationship(back_populates="project")
    evaluation_cases: Mapped[list["EvaluationCase"]] = relationship(
        back_populates="project"
    )
    hotspots: Mapped[list["Hotspot"]] = relationship(back_populates="project")
    plan_sheets: Mapped[list["PlanSheet"]] = relationship(back_populates="project")


class Document(Base):
    __tablename__ = "documents"

    document_id: Mapped[str] = mapped_column(String, primary_key=True)
    project_id: Mapped[str] = mapped_column(
        ForeignKey("projects.project_id"), nullable=False
    )
    file_name: Mapped[str] = mapped_column(String, nullable=False)
    document_type: Mapped[str] = mapped_column(String, nullable=False)
    status: Mapped[str] = mapped_column(String, nullable=False)
    purpose: Mapped[str] = mapped_column(Text, nullable=False)
    expected_key_information: Mapped[str] = mapped_column(Text, nullable=False)
    intentionally_missing_or_conflicting_information: Mapped[str | None] = (
        mapped_column(Text, nullable=True)
    )

    # Production foundation fields (Sprint 1). Nullable with safe defaults so the
    # seeded demo documents keep working. source_mode distinguishes seeded demo
    # documents from user-registered or user-uploaded documents. processing_status
    # never implies document approval; it tracks intake handling only.
    source_mode: Mapped[str] = mapped_column(String, default="demo_fixture")
    original_file_name: Mapped[str | None] = mapped_column(String, nullable=True)
    upload_status: Mapped[str | None] = mapped_column(String, nullable=True)
    processing_status: Mapped[str | None] = mapped_column(String, nullable=True)
    storage_path: Mapped[str | None] = mapped_column(String, nullable=True)
    content_type: Mapped[str | None] = mapped_column(String, nullable=True)
    file_size_bytes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    checksum_sha256: Mapped[str | None] = mapped_column(String, nullable=True)
    revision_label: Mapped[str | None] = mapped_column(String, nullable=True)
    revision_date: Mapped[str | None] = mapped_column(String, nullable=True)
    uploaded_by_name: Mapped[str | None] = mapped_column(String, nullable=True)
    uploaded_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    registered_at: Mapped[datetime | None] = mapped_column(
        DateTime, nullable=True
    )
    is_superseded: Mapped[bool] = mapped_column(default=False)
    superseded_by_document_id: Mapped[str | None] = mapped_column(
        String, nullable=True
    )
    page_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    sheet_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    classification_confidence: Mapped[float | None] = mapped_column(
        Float, nullable=True
    )

    # Production foundation fields (Sprint 2) for PDF page indexing. Nullable
    # with safe defaults so seeded and Sprint 1 documents keep working. These
    # track digital PDF text extraction state only; none implies approval.
    indexed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    text_extraction_status: Mapped[str | None] = mapped_column(
        String, nullable=True
    )
    text_extraction_summary: Mapped[str | None] = mapped_column(
        Text, nullable=True
    )
    extraction_warning_count: Mapped[int] = mapped_column(Integer, default=0)

    project: Mapped["Project"] = relationship(back_populates="documents")
    pages: Mapped[list["DocumentPage"]] = relationship(back_populates="document")


class DocumentPage(Base):
    """A page-level review record produced by indexing an uploaded PDF.

    Production Foundations Sprint 2 indexes uploaded digital PDFs into page
    records and extracts text where the PDF carries an embedded text layer.
    Indexing reads a real uploaded file deterministically with pypdf. It does
    not OCR scanned pages, send content to any AI provider, approve plans,
    certify compliance, verify CAD, validate design, or make any final
    engineering decision. A page with no embedded text is recorded as
    no_extractable_text, not an error and not a conclusion.
    """

    __tablename__ = "document_pages"

    document_page_id: Mapped[str] = mapped_column(String, primary_key=True)
    project_id: Mapped[str] = mapped_column(
        ForeignKey("projects.project_id"), nullable=False
    )
    document_id: Mapped[str] = mapped_column(
        ForeignKey("documents.document_id"), nullable=False
    )
    page_number: Mapped[int] = mapped_column(Integer, nullable=False)
    page_label: Mapped[str | None] = mapped_column(String, nullable=True)
    extracted_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    text_extraction_status: Mapped[str] = mapped_column(
        String, default="not_indexed"
    )
    text_extraction_method: Mapped[str | None] = mapped_column(
        String, nullable=True
    )
    char_count: Mapped[int] = mapped_column(Integer, default=0)
    word_count: Mapped[int] = mapped_column(Integer, default=0)
    extraction_warnings: Mapped[list] = mapped_column(JSON, default=list)
    indexed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)

    document: Mapped["Document"] = relationship(back_populates="pages")


class EvidenceCitation(Base):
    """A reviewer-selected, page-level evidence citation for a finding.

    Sprint 2 lets a human reviewer cite an exact page or section of an indexed
    document as evidence for a review-support finding. A citation is a
    reviewer-selected source reference, not proof of correctness. It does not
    approve, certify, verify, or validate anything, and it never changes a
    finding to a final outcome. It complements the Sprint 1 FindingSource
    manual evidence reference with page-level, indexing-aware records.
    """

    __tablename__ = "evidence_citations"

    evidence_citation_id: Mapped[str] = mapped_column(String, primary_key=True)
    project_id: Mapped[str] = mapped_column(
        ForeignKey("projects.project_id"), nullable=False
    )
    finding_id: Mapped[str] = mapped_column(
        ForeignKey("findings.finding_id"), nullable=False
    )
    document_id: Mapped[str] = mapped_column(
        ForeignKey("documents.document_id"), nullable=False
    )
    document_page_id: Mapped[str | None] = mapped_column(
        ForeignKey("document_pages.document_page_id"), nullable=True
    )
    page_number: Mapped[int | None] = mapped_column(Integer, nullable=True)
    page_label: Mapped[str | None] = mapped_column(String, nullable=True)
    section_label: Mapped[str | None] = mapped_column(String, nullable=True)
    quoted_excerpt: Mapped[str | None] = mapped_column(Text, nullable=True)
    reviewer_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    citation_type: Mapped[str] = mapped_column(String, default="reviewer_selected")
    citation_status: Mapped[str] = mapped_column(
        String, default="needs_reviewer_confirmation"
    )
    created_by_actor_id: Mapped[str | None] = mapped_column(String, nullable=True)
    created_by_name: Mapped[str | None] = mapped_column(String, nullable=True)
    source_mode: Mapped[str] = mapped_column(String, default="user_created")
    # Production foundation fields (Sprint 4) for checklist-driven review. These
    # are nullable with safe defaults so Sprint 2 finding citations keep working.
    # citation_context distinguishes a finding citation from a checklist evidence
    # citation. None of these implies a final engineering decision.
    project_checklist_item_id: Mapped[str | None] = mapped_column(
        String, nullable=True
    )
    rule_pack_item_id: Mapped[str | None] = mapped_column(
        String, nullable=True
    )
    citation_context: Mapped[str] = mapped_column(
        String, default="finding_citation"
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)


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


class AuditEvent(Base):
    __tablename__ = "audit_events"

    audit_event_id: Mapped[str] = mapped_column(String, primary_key=True)
    project_id: Mapped[str] = mapped_column(
        ForeignKey("projects.project_id"), nullable=False
    )
    event_type: Mapped[str] = mapped_column(String, nullable=False)
    actor_type: Mapped[str] = mapped_column(String, nullable=False)
    related_entity_type: Mapped[str] = mapped_column(String, nullable=False)
    related_entity_id: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    timestamp: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    # Non-sensitive structured context (provider, prompt version, chunk ids,
    # validation and safety status). Never stores secrets or API keys.
    event_metadata: Mapped[dict] = mapped_column("event_metadata", JSON, default=dict)
    # Production foundation fields (Sprint 1). Actor attribution and request
    # context for real reviewer actions. Raw IP and user agent are never stored;
    # only optional hashes are kept, and only when a caller chooses to provide
    # them. These are nullable so seeded and existing audit events keep working.
    actor_id: Mapped[str | None] = mapped_column(String, nullable=True)
    actor_display_name: Mapped[str | None] = mapped_column(String, nullable=True)
    request_id: Mapped[str | None] = mapped_column(String, nullable=True)
    source_ip_hash: Mapped[str | None] = mapped_column(String, nullable=True)
    user_agent_hash: Mapped[str | None] = mapped_column(String, nullable=True)
    # Production foundation fields (Sprint 5). When an action is taken by a
    # signed-in user, the audit event records the user and organization identity
    # for real attribution. Tokens, passwords, and password hashes are never
    # stored here. Nullable so seeded and demo-attributed events keep working.
    user_id: Mapped[str | None] = mapped_column(String, nullable=True)
    user_email: Mapped[str | None] = mapped_column(String, nullable=True)
    organization_id: Mapped[str | None] = mapped_column(String, nullable=True)
    access_level: Mapped[str | None] = mapped_column(String, nullable=True)

    project: Mapped["Project"] = relationship(back_populates="audit_events")


class Actor(Base):
    """A lightweight reviewer or actor identity for real-action attribution.

    Sprint 1 has no real authentication. This records a demo reviewer identity
    so real actions (project creation, document registration, reviewer findings)
    carry attribution that real authentication can replace later. It is not an
    authentication or authorization record and grants no access.
    """

    __tablename__ = "actors"

    actor_id: Mapped[str] = mapped_column(String, primary_key=True)
    display_name: Mapped[str] = mapped_column(String, nullable=False)
    actor_type: Mapped[str] = mapped_column(String, nullable=False)
    organization_name: Mapped[str | None] = mapped_column(String, nullable=True)
    role_label: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)


class UserAccount(Base):
    """A real local user account for authentication (Sprint 5).

    Civil Engineer AI adds a local authentication foundation so real actions can
    be attributed to a signed-in user instead of a shared demo reviewer. The
    password is never stored in plaintext; only a PBKDF2 hash is kept and it is
    never returned by the API. This is a local auth foundation, not enterprise
    SSO, and it grants no engineering authority.
    """

    __tablename__ = "user_accounts"

    user_id: Mapped[str] = mapped_column(String, primary_key=True)
    email: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    display_name: Mapped[str] = mapped_column(String, nullable=False)
    password_hash: Mapped[str] = mapped_column(String, nullable=False)
    is_active: Mapped[bool] = mapped_column(default=True)
    is_demo_user: Mapped[bool] = mapped_column(default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)
    last_login_at: Mapped[datetime | None] = mapped_column(
        DateTime, nullable=True
    )


class Organization(Base):
    """An organization account that groups users and projects (Sprint 5)."""

    __tablename__ = "organizations"

    organization_id: Mapped[str] = mapped_column(String, primary_key=True)
    organization_name: Mapped[str] = mapped_column(String, nullable=False)
    organization_type: Mapped[str] = mapped_column(
        String, default="municipality"
    )
    source_mode: Mapped[str] = mapped_column(String, default="user_created")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)

    memberships: Mapped[list["OrganizationMembership"]] = relationship(
        back_populates="organization"
    )


class OrganizationMembership(Base):
    """A user's role within an organization (Sprint 5)."""

    __tablename__ = "organization_memberships"

    membership_id: Mapped[str] = mapped_column(String, primary_key=True)
    organization_id: Mapped[str] = mapped_column(
        ForeignKey("organizations.organization_id"), nullable=False
    )
    user_id: Mapped[str] = mapped_column(
        ForeignKey("user_accounts.user_id"), nullable=False
    )
    role: Mapped[str] = mapped_column(String, default="reviewer")
    is_active: Mapped[bool] = mapped_column(default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)

    organization: Mapped["Organization"] = relationship(
        back_populates="memberships"
    )


class ProjectAccess(Base):
    """A user or organization grant of access to a project (Sprint 5).

    Access controls who may view or take reviewer actions on a project's review
    records. It never controls whether a project satisfies engineering
    requirements and never implies approval or compliance.
    """

    __tablename__ = "project_access"

    project_access_id: Mapped[str] = mapped_column(String, primary_key=True)
    project_id: Mapped[str] = mapped_column(
        ForeignKey("projects.project_id"), nullable=False
    )
    organization_id: Mapped[str | None] = mapped_column(
        ForeignKey("organizations.organization_id"), nullable=True
    )
    user_id: Mapped[str | None] = mapped_column(
        ForeignKey("user_accounts.user_id"), nullable=True
    )
    access_level: Mapped[str] = mapped_column(String, default="reviewer")
    granted_by_user_id: Mapped[str | None] = mapped_column(
        String, nullable=True
    )
    is_active: Mapped[bool] = mapped_column(default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)


class EvaluationCase(Base):
    __tablename__ = "evaluation_cases"

    eval_case_id: Mapped[str] = mapped_column(String, primary_key=True)
    project_id: Mapped[str] = mapped_column(
        ForeignKey("projects.project_id"), nullable=False
    )
    name: Mapped[str] = mapped_column(String, nullable=False)
    input_documents: Mapped[list] = mapped_column(JSON, default=list)
    expected_findings: Mapped[list] = mapped_column(JSON, default=list)
    expected_risk_level: Mapped[str] = mapped_column(String, nullable=False)
    evaluation_metric: Mapped[str] = mapped_column(String, nullable=False)
    seeded_result: Mapped[dict] = mapped_column(JSON, default=dict)

    project: Mapped["Project"] = relationship(back_populates="evaluation_cases")


class Hotspot(Base):
    __tablename__ = "hotspots"

    hotspot_id: Mapped[str] = mapped_column(String, primary_key=True)
    project_id: Mapped[str] = mapped_column(
        ForeignKey("projects.project_id"), nullable=False
    )
    name: Mapped[str] = mapped_column(String, nullable=False)
    category: Mapped[str] = mapped_column(String, nullable=False)
    short_description: Mapped[str] = mapped_column(Text, nullable=False)
    civil_purpose: Mapped[str] = mapped_column(Text, nullable=False)
    related_checklist_items: Mapped[list] = mapped_column(JSON, default=list)
    related_planted_issues: Mapped[list] = mapped_column(JSON, default=list)
    future_drilldown: Mapped[str] = mapped_column(Text, nullable=False)
    position_x_percent: Mapped[float] = mapped_column(Float, nullable=False)
    position_y_percent: Mapped[float] = mapped_column(Float, nullable=False)

    project: Mapped["Project"] = relationship(back_populates="hotspots")


class DocumentChunk(Base):
    """A short, retrievable excerpt of source evidence from a document.

    Phase 3 seeds synthetic chunks rather than parsing real documents. Each
    chunk carries enough metadata (page, section, keywords, related checklist
    items and findings) to support keyword and metadata based retrieval.
    """

    __tablename__ = "document_chunks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    chunk_id: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    project_id: Mapped[str] = mapped_column(
        ForeignKey("projects.project_id"), nullable=False
    )
    document_id: Mapped[str] = mapped_column(
        ForeignKey("documents.document_id"), nullable=False
    )
    document_type: Mapped[str] = mapped_column(String, nullable=False)
    file_name: Mapped[str] = mapped_column(String, nullable=False)
    page_number: Mapped[int | None] = mapped_column(Integer, nullable=True)
    section_heading: Mapped[str | None] = mapped_column(String, nullable=True)
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    keywords: Mapped[list] = mapped_column(JSON, default=list)
    related_checklist_items: Mapped[list] = mapped_column(JSON, default=list)
    related_findings: Mapped[list] = mapped_column(JSON, default=list)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=_utcnow
    )


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


class RetrievalQuery(Base):
    """An audit record of a retrieval query run against the seeded chunks.

    This supports future auditing of retrieval behavior. Phase 3 seeds a few
    representative queries; later phases can record live queries here.
    """

    __tablename__ = "retrieval_queries"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    retrieval_query_id: Mapped[str] = mapped_column(
        String, unique=True, nullable=False
    )
    project_id: Mapped[str] = mapped_column(
        ForeignKey("projects.project_id"), nullable=False
    )
    query_text: Mapped[str] = mapped_column(String, nullable=False)
    related_checklist_item_id: Mapped[str | None] = mapped_column(
        String, nullable=True
    )
    result_count: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=_utcnow
    )

    # Production foundation fields (Sprint 3) for deterministic evidence
    # retrieval over indexed PDF page text. Nullable with safe defaults so the
    # seeded Phase 3 retrieval query records keep working without a migration.
    # query_type records which retrieval mode was run; filters holds the
    # non-sensitive document/page filter context. event_metadata never stores
    # full page text, secrets, or raw server file paths.
    query_type: Mapped[str | None] = mapped_column(String, nullable=True)
    filters: Mapped[dict] = mapped_column(JSON, default=dict)
    related_finding_id: Mapped[str | None] = mapped_column(
        String, nullable=True
    )
    created_by_actor_id: Mapped[str | None] = mapped_column(
        String, nullable=True
    )
    created_by_name: Mapped[str | None] = mapped_column(String, nullable=True)
    event_metadata: Mapped[dict] = mapped_column(JSON, default=dict)


class EvidenceCandidate(Base):
    """A reviewer-controlled candidate from deterministic evidence retrieval.

    Production Foundations Sprint 3 lets a reviewer search indexed PDF page text
    and save useful results into a durable queue. A candidate is a retrieval
    result for reviewer evaluation, not a conclusion. It does not approve plans,
    certify compliance, verify CAD, validate design, declare a project safe,
    resolve or close an issue, or make any final engineering decision. A
    reviewer must act to promote a candidate into a draft finding; the system
    never auto-promotes. ranking_score is a transparent local relevance score,
    never proof of correctness.
    """

    __tablename__ = "evidence_candidates"

    evidence_candidate_id: Mapped[str] = mapped_column(String, primary_key=True)
    project_id: Mapped[str] = mapped_column(
        ForeignKey("projects.project_id"), nullable=False
    )
    retrieval_query_id: Mapped[str | None] = mapped_column(
        String, nullable=True
    )
    document_id: Mapped[str] = mapped_column(
        ForeignKey("documents.document_id"), nullable=False
    )
    document_page_id: Mapped[str | None] = mapped_column(
        ForeignKey("document_pages.document_page_id"), nullable=True
    )
    page_number: Mapped[int | None] = mapped_column(Integer, nullable=True)
    finding_id: Mapped[str | None] = mapped_column(
        ForeignKey("findings.finding_id"), nullable=True
    )
    checklist_item_id: Mapped[str | None] = mapped_column(
        String, nullable=True
    )
    candidate_title: Mapped[str] = mapped_column(String, nullable=False)
    candidate_excerpt: Mapped[str | None] = mapped_column(Text, nullable=True)
    match_terms: Mapped[list] = mapped_column(JSON, default=list)
    ranking_score: Mapped[float] = mapped_column(Float, default=0.0)
    ranking_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    candidate_status: Mapped[str] = mapped_column(
        String, default="saved_for_review"
    )
    candidate_origin: Mapped[str] = mapped_column(
        String, default="keyword_search"
    )
    reviewer_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_by_actor_id: Mapped[str | None] = mapped_column(
        String, nullable=True
    )
    created_by_name: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)
    dismissed_at: Mapped[datetime | None] = mapped_column(
        DateTime, nullable=True
    )
    promoted_finding_id: Mapped[str | None] = mapped_column(
        String, nullable=True
    )


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
    """An AI-generated draft review-support finding.

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


class AIEvaluationResult(Base):
    """A scored evaluation of one AI review run against expected findings.

    Evaluation is heuristic and explainable, not a mathematically perfect
    measure. It compares the draft findings from a review run against the
    expected Brookside Meadows findings and records recall, precision, citation
    validity, and quality signals so the workflow stays auditable.
    """

    __tablename__ = "ai_evaluation_results"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    evaluation_result_id: Mapped[str] = mapped_column(
        String, unique=True, nullable=False
    )
    project_id: Mapped[str] = mapped_column(
        ForeignKey("projects.project_id"), nullable=False
    )
    review_run_id: Mapped[str] = mapped_column(
        ForeignKey("ai_review_runs.review_run_id"), nullable=False
    )
    expected_findings_count: Mapped[int] = mapped_column(Integer, default=0)
    draft_findings_count: Mapped[int] = mapped_column(Integer, default=0)
    matched_findings_count: Mapped[int] = mapped_column(Integer, default=0)
    unmatched_expected_count: Mapped[int] = mapped_column(Integer, default=0)
    extra_draft_findings_count: Mapped[int] = mapped_column(Integer, default=0)
    citation_validity_rate: Mapped[float] = mapped_column(Float, default=0.0)
    human_review_required_rate: Mapped[float] = mapped_column(Float, default=0.0)
    prohibited_word_count: Mapped[int] = mapped_column(Integer, default=0)
    validation_failure_count: Mapped[int] = mapped_column(Integer, default=0)
    safety_failure_count: Mapped[int] = mapped_column(Integer, default=0)
    recall: Mapped[float] = mapped_column(Float, default=0.0)
    precision: Mapped[float] = mapped_column(Float, default=0.0)
    overall_score: Mapped[float] = mapped_column(Float, default=0.0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=_utcnow
    )


class AIEvaluationMatch(Base):
    """A single explainable match record produced during evaluation scoring.

    Each record links an expected finding and/or a draft finding and records how
    the match was made (related checklist item, category, or title similarity)
    or that an item was unmatched or extra.
    """

    __tablename__ = "ai_evaluation_matches"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    evaluation_match_id: Mapped[str] = mapped_column(
        String, unique=True, nullable=False
    )
    evaluation_result_id: Mapped[str] = mapped_column(
        ForeignKey("ai_evaluation_results.evaluation_result_id"), nullable=False
    )
    expected_finding_id: Mapped[str | None] = mapped_column(String, nullable=True)
    draft_finding_id: Mapped[str | None] = mapped_column(String, nullable=True)
    match_type: Mapped[str] = mapped_column(String, nullable=False)
    match_confidence: Mapped[float] = mapped_column(Float, default=0.0)
    matched_on: Mapped[str | None] = mapped_column(String, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=_utcnow
    )


class PlanSheet(Base):
    """A civil plan sheet record in the Brookside Meadows plan set.

    Phase 6 models the plan sheet index rather than parsing real CAD or PDF
    files. Each record carries sheet metadata (number, title, discipline,
    revision, status) and connects to related documents, checklist items, and
    findings. A sheet status is never a final engineering decision; values such
    as referenced_not_included and needs_reviewer_confirmation keep the work
    under human review.
    """

    __tablename__ = "plan_sheets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    sheet_id: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    project_id: Mapped[str] = mapped_column(
        ForeignKey("projects.project_id"), nullable=False
    )
    sheet_number: Mapped[str] = mapped_column(String, nullable=False)
    sheet_title: Mapped[str] = mapped_column(String, nullable=False)
    discipline: Mapped[str] = mapped_column(String, nullable=False)
    revision: Mapped[str] = mapped_column(String, nullable=False)
    revision_date: Mapped[str | None] = mapped_column(String, nullable=True)
    status: Mapped[str] = mapped_column(String, nullable=False)
    file_name: Mapped[str | None] = mapped_column(String, nullable=True)
    sheet_purpose: Mapped[str] = mapped_column(Text, nullable=False)
    related_documents: Mapped[list] = mapped_column(JSON, default=list)
    related_checklist_items: Mapped[list] = mapped_column(JSON, default=list)
    related_findings: Mapped[list] = mapped_column(JSON, default=list)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=_utcnow
    )

    project: Mapped["Project"] = relationship(back_populates="plan_sheets")


class CadMetadata(Base):
    """CAD-aware metadata for a civil feature referenced in the plan set.

    Phase 6 seeds synthetic CAD-aware metadata rather than extracting it from
    real DWG or DXF files. Each record describes a civil feature (basin, pipe,
    road, lot, utility, and so on), the sheet and layer it relates to, and the
    documents, checklist items, or findings it connects to. This is a future
    ready abstraction for CAD-derived metadata, not verified CAD geometry.
    """

    __tablename__ = "cad_metadata"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    cad_metadata_id: Mapped[str] = mapped_column(
        String, unique=True, nullable=False
    )
    project_id: Mapped[str] = mapped_column(
        ForeignKey("projects.project_id"), nullable=False
    )
    sheet_id: Mapped[str | None] = mapped_column(String, nullable=True)
    source_type: Mapped[str] = mapped_column(String, nullable=False)
    entity_type: Mapped[str] = mapped_column(String, nullable=False)
    entity_label: Mapped[str] = mapped_column(String, nullable=False)
    layer_name: Mapped[str | None] = mapped_column(String, nullable=True)
    discipline: Mapped[str] = mapped_column(String, nullable=False)
    related_document_id: Mapped[str | None] = mapped_column(String, nullable=True)
    related_checklist_item_id: Mapped[str | None] = mapped_column(
        String, nullable=True
    )
    related_finding_id: Mapped[str | None] = mapped_column(String, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=_utcnow
    )


class PlanReference(Base):
    """A reference linking a document, sheet, or civil feature to another.

    Plan references record where the submitted package points from one place to
    another (for example, a report citing a sheet, or an RFI citing a pipe). The
    consistency_status records whether the reference target was located and
    whether labels agree. It is review-support evidence, never a final decision.
    """

    __tablename__ = "plan_references"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    plan_reference_id: Mapped[str] = mapped_column(
        String, unique=True, nullable=False
    )
    project_id: Mapped[str] = mapped_column(
        ForeignKey("projects.project_id"), nullable=False
    )
    source_type: Mapped[str] = mapped_column(String, nullable=False)
    source_id: Mapped[str] = mapped_column(String, nullable=False)
    target_type: Mapped[str] = mapped_column(String, nullable=False)
    target_id: Mapped[str] = mapped_column(String, nullable=False)
    reference_label: Mapped[str] = mapped_column(String, nullable=False)
    reference_context: Mapped[str] = mapped_column(Text, nullable=False)
    consistency_status: Mapped[str] = mapped_column(String, nullable=False)
    review_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=_utcnow
    )


class PlanConsistencyFinding(Base):
    """A plan-sheet-specific review-support finding.

    These findings are produced by evaluating the seeded plan sheets and plan
    references for missing sheets, missing reference targets, conflicting
    labels, and unclear revisions. Like every finding in the system, each one
    requires human review and never carries final approval or certification
    language.
    """

    __tablename__ = "plan_consistency_findings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    plan_finding_id: Mapped[str] = mapped_column(
        String, unique=True, nullable=False
    )
    project_id: Mapped[str] = mapped_column(
        ForeignKey("projects.project_id"), nullable=False
    )
    finding_type: Mapped[str] = mapped_column(String, nullable=False)
    title: Mapped[str] = mapped_column(String, nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    risk_level: Mapped[str] = mapped_column(String, nullable=False)
    status: Mapped[str] = mapped_column(String, nullable=False)
    related_sheet_ids: Mapped[list] = mapped_column(JSON, default=list)
    related_document_ids: Mapped[list] = mapped_column(JSON, default=list)
    related_checklist_items: Mapped[list] = mapped_column(JSON, default=list)
    related_cad_metadata_ids: Mapped[list] = mapped_column(JSON, default=list)
    recommended_human_action: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=_utcnow
    )


class PlanSheetHotspot(Base):
    """A seeded review-support annotation placed over a plan sheet preview.

    Phase 7 adds a reviewer-facing plan sheet viewer. A hotspot is a seeded
    rectangular annotation (percentage coordinates) over a synthetic plan sheet
    preview that points a reviewer at a civil feature, plan reference, or plan
    consistency finding. Hotspots are seeded review-support metadata, not
    extracted CAD geometry or verified plan locations. They never carry final
    approval, certification, or CAD verification language.
    """

    __tablename__ = "plan_sheet_hotspots"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    hotspot_id: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    project_id: Mapped[str] = mapped_column(
        ForeignKey("projects.project_id"), nullable=False
    )
    sheet_id: Mapped[str] = mapped_column(
        ForeignKey("plan_sheets.sheet_id"), nullable=False
    )
    hotspot_type: Mapped[str] = mapped_column(String, nullable=False)
    label: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    x_percent: Mapped[float] = mapped_column(Float, nullable=False)
    y_percent: Mapped[float] = mapped_column(Float, nullable=False)
    width_percent: Mapped[float] = mapped_column(Float, nullable=False)
    height_percent: Mapped[float] = mapped_column(Float, nullable=False)
    severity: Mapped[str] = mapped_column(String, nullable=False)
    related_plan_reference_ids: Mapped[list] = mapped_column(JSON, default=list)
    related_cad_metadata_ids: Mapped[list] = mapped_column(JSON, default=list)
    related_plan_finding_ids: Mapped[list] = mapped_column(JSON, default=list)
    related_document_ids: Mapped[list] = mapped_column(JSON, default=list)
    related_checklist_item_ids: Mapped[list] = mapped_column(JSON, default=list)
    review_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    requires_human_review: Mapped[bool] = mapped_column(default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=_utcnow
    )


class PlanConsistencyReviewAction(Base):
    """A persisted human review action on a plan consistency finding.

    Phase 7 lets a reviewer record an action on a plan consistency finding:
    needs_follow_up, reviewer_confirmed, not_applicable, or
    needs_more_information. There is intentionally no action called approve, and
    no action approves a plan, certifies compliance, verifies CAD, or validates
    a design. Every action keeps the finding a review-support finding under
    human control.
    """

    __tablename__ = "plan_consistency_review_actions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    review_action_id: Mapped[str] = mapped_column(
        String, unique=True, nullable=False
    )
    plan_finding_id: Mapped[str] = mapped_column(
        ForeignKey("plan_consistency_findings.plan_finding_id"), nullable=False
    )
    project_id: Mapped[str] = mapped_column(
        ForeignKey("projects.project_id"), nullable=False
    )
    reviewer_name: Mapped[str] = mapped_column(String, nullable=False)
    action: Mapped[str] = mapped_column(String, nullable=False)
    reviewer_note: Mapped[str] = mapped_column(Text, nullable=False)
    previous_status: Mapped[str] = mapped_column(String, nullable=False)
    new_status: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=_utcnow
    )


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


class WorkflowItem(Base):
    """An operational workflow board item tracking a review-support item.

    Phase 9 promotes review packet items into a reviewer workflow board so a
    human reviewer can move each item from triage through follow-up to handoff.
    A workflow item tracks where a review-support item sits in the operational
    review workflow. It does not approve plans, certify compliance, stamp
    drawings, verify CAD, validate a design, or make final engineering
    decisions. Every item stays under human control.
    """

    __tablename__ = "workflow_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    workflow_item_id: Mapped[str] = mapped_column(
        String, unique=True, nullable=False
    )
    project_id: Mapped[str] = mapped_column(
        ForeignKey("projects.project_id"), nullable=False
    )
    packet_id: Mapped[str | None] = mapped_column(String, nullable=True)
    packet_item_id: Mapped[str | None] = mapped_column(String, nullable=True)
    title: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    source_type: Mapped[str] = mapped_column(String, nullable=False)
    source_id: Mapped[str | None] = mapped_column(String, nullable=True)
    severity: Mapped[str] = mapped_column(String, nullable=False)
    status: Mapped[str] = mapped_column(String, nullable=False)
    assigned_role: Mapped[str] = mapped_column(String, nullable=False)
    reviewer_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    target_date: Mapped[str | None] = mapped_column(String, nullable=True)
    section_type: Mapped[str] = mapped_column(String, nullable=False)
    evidence_types: Mapped[list] = mapped_column(JSON, default=list)
    requires_human_review: Mapped[bool] = mapped_column(default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=_utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=_utcnow
    )


class WorkflowAction(Base):
    """A persisted reviewer action on a workflow item.

    Each action records a status transition or note a reviewer made while
    working the board. There is no action called approve, and no action
    approves, certifies, verifies, or validates anything.
    """

    __tablename__ = "workflow_actions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    action_id: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    workflow_item_id: Mapped[str] = mapped_column(
        ForeignKey("workflow_items.workflow_item_id"), nullable=False
    )
    project_id: Mapped[str] = mapped_column(
        ForeignKey("projects.project_id"), nullable=False
    )
    action_type: Mapped[str] = mapped_column(String, nullable=False)
    previous_status: Mapped[str] = mapped_column(String, nullable=False)
    new_status: Mapped[str] = mapped_column(String, nullable=False)
    reviewer_note: Mapped[str] = mapped_column(Text, nullable=False)
    reviewer_name: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=_utcnow
    )


class WorkflowFollowUpRequest(Base):
    """A follow-up request tracked against a workflow item.

    A reviewer may request more information or a follow-up from an applicant or
    another reviewer. The request records what was asked and its status. It
    never records a final engineering decision; closing a request without a
    decision is an explicit allowed state.
    """

    __tablename__ = "workflow_follow_up_requests"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    follow_up_id: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    workflow_item_id: Mapped[str] = mapped_column(
        ForeignKey("workflow_items.workflow_item_id"), nullable=False
    )
    project_id: Mapped[str] = mapped_column(
        ForeignKey("projects.project_id"), nullable=False
    )
    requested_from: Mapped[str] = mapped_column(String, nullable=False)
    request_reason: Mapped[str] = mapped_column(Text, nullable=False)
    requested_information: Mapped[str] = mapped_column(Text, nullable=False)
    target_date: Mapped[str | None] = mapped_column(String, nullable=True)
    status: Mapped[str] = mapped_column(String, nullable=False)
    reviewer_name: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=_utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=_utcnow
    )


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


class CadFileUpload(Base):
    """A real CAD file (DXF only) registered for review-support intake.

    Intake parses a real DXF file and extracts review-support metadata. It does
    not verify CAD, validate geometry or design, certify compliance, or make
    final engineering decisions. DWG parsing is out of scope for this phase.

    Phase 12 adds browser upload support. A browser-uploaded file is stored under
    a safe generated stored_file_name (never the raw user file name), and the
    original user file name is kept as original_file_name metadata only.
    validation_status records whether the upload passed intake validation. It
    never records an engineering decision.
    """

    __tablename__ = "cad_file_uploads"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    cad_file_id: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    project_id: Mapped[str] = mapped_column(
        ForeignKey("projects.project_id"), nullable=False
    )
    file_name: Mapped[str] = mapped_column(String, nullable=False)
    file_type: Mapped[str] = mapped_column(String, nullable=False)
    file_size_bytes: Mapped[int] = mapped_column(Integer, default=0)
    storage_path: Mapped[str] = mapped_column(String, nullable=False)
    upload_status: Mapped[str] = mapped_column(String, nullable=False)
    uploaded_by: Mapped[str] = mapped_column(String, nullable=False)
    limitations_note: Mapped[str] = mapped_column(Text, nullable=False)
    # Phase 12 browser upload metadata. Nullable so Phase 11 sample-based intake
    # and existing rows keep working without a migration.
    original_file_name: Mapped[str | None] = mapped_column(String, nullable=True)
    stored_file_name: Mapped[str | None] = mapped_column(String, nullable=True)
    content_type: Mapped[str | None] = mapped_column(String, nullable=True)
    upload_source: Mapped[str] = mapped_column(String, default="sample")
    validation_status: Mapped[str | None] = mapped_column(String, nullable=True)
    validation_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    max_file_size_bytes: Mapped[int] = mapped_column(Integer, default=0)
    parse_requested_at: Mapped[datetime | None] = mapped_column(
        DateTime, nullable=True
    )
    parse_completed_at: Mapped[datetime | None] = mapped_column(
        DateTime, nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=_utcnow
    )


class CadParseRun(Base):
    """A single DXF parse run over a CAD file."""

    __tablename__ = "cad_parse_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    parse_run_id: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    cad_file_id: Mapped[str] = mapped_column(
        ForeignKey("cad_file_uploads.cad_file_id"), nullable=False
    )
    project_id: Mapped[str] = mapped_column(
        ForeignKey("projects.project_id"), nullable=False
    )
    parser_name: Mapped[str] = mapped_column(String, nullable=False)
    parser_version: Mapped[str] = mapped_column(String, nullable=False)
    status: Mapped[str] = mapped_column(String, nullable=False)
    started_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime, nullable=True
    )
    entity_count: Mapped[int] = mapped_column(Integer, default=0)
    layer_count: Mapped[int] = mapped_column(Integer, default=0)
    block_count: Mapped[int] = mapped_column(Integer, default=0)
    text_count: Mapped[int] = mapped_column(Integer, default=0)
    warning_count: Mapped[int] = mapped_column(Integer, default=0)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    limitations_note: Mapped[str] = mapped_column(Text, nullable=False)


class CadLayerExtract(Base):
    """A layer extracted from a DXF parse run."""

    __tablename__ = "cad_layer_extracts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    layer_extract_id: Mapped[str] = mapped_column(
        String, unique=True, nullable=False
    )
    parse_run_id: Mapped[str] = mapped_column(
        ForeignKey("cad_parse_runs.parse_run_id"), nullable=False
    )
    cad_file_id: Mapped[str] = mapped_column(String, nullable=False)
    project_id: Mapped[str] = mapped_column(String, nullable=False)
    layer_name: Mapped[str] = mapped_column(String, nullable=False)
    entity_count: Mapped[int] = mapped_column(Integer, default=0)
    has_text: Mapped[bool] = mapped_column(default=False)
    has_geometry: Mapped[bool] = mapped_column(default=False)
    review_category: Mapped[str] = mapped_column(String, nullable=False)
    requires_human_review: Mapped[bool] = mapped_column(default=True)


class CadEntityExtract(Base):
    """An entity extracted from a DXF parse run.

    Bounding values are stored only when available from the source file. They
    are local drawing coordinates and are not treated as georeferenced.
    """

    __tablename__ = "cad_entity_extracts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    entity_extract_id: Mapped[str] = mapped_column(
        String, unique=True, nullable=False
    )
    parse_run_id: Mapped[str] = mapped_column(
        ForeignKey("cad_parse_runs.parse_run_id"), nullable=False
    )
    cad_file_id: Mapped[str] = mapped_column(String, nullable=False)
    project_id: Mapped[str] = mapped_column(String, nullable=False)
    entity_type: Mapped[str] = mapped_column(String, nullable=False)
    layer_name: Mapped[str | None] = mapped_column(String, nullable=True)
    block_name: Mapped[str | None] = mapped_column(String, nullable=True)
    handle: Mapped[str | None] = mapped_column(String, nullable=True)
    text_value: Mapped[str | None] = mapped_column(Text, nullable=True)
    x_min: Mapped[float | None] = mapped_column(Float, nullable=True)
    y_min: Mapped[float | None] = mapped_column(Float, nullable=True)
    x_max: Mapped[float | None] = mapped_column(Float, nullable=True)
    y_max: Mapped[float | None] = mapped_column(Float, nullable=True)
    review_category: Mapped[str] = mapped_column(String, nullable=False)
    requires_human_review: Mapped[bool] = mapped_column(default=True)


class CadBlockExtract(Base):
    """A block definition extracted from a DXF parse run."""

    __tablename__ = "cad_block_extracts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    block_extract_id: Mapped[str] = mapped_column(
        String, unique=True, nullable=False
    )
    parse_run_id: Mapped[str] = mapped_column(
        ForeignKey("cad_parse_runs.parse_run_id"), nullable=False
    )
    cad_file_id: Mapped[str] = mapped_column(String, nullable=False)
    project_id: Mapped[str] = mapped_column(String, nullable=False)
    block_name: Mapped[str] = mapped_column(String, nullable=False)
    insert_count: Mapped[int] = mapped_column(Integer, default=0)
    layer_names: Mapped[list] = mapped_column(JSON, default=list)
    text_values: Mapped[list] = mapped_column(JSON, default=list)
    review_category: Mapped[str] = mapped_column(String, nullable=False)
    requires_human_review: Mapped[bool] = mapped_column(default=True)


class CadTextExtract(Base):
    """A text or mtext value extracted from a DXF parse run."""

    __tablename__ = "cad_text_extracts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    text_extract_id: Mapped[str] = mapped_column(
        String, unique=True, nullable=False
    )
    parse_run_id: Mapped[str] = mapped_column(
        ForeignKey("cad_parse_runs.parse_run_id"), nullable=False
    )
    cad_file_id: Mapped[str] = mapped_column(String, nullable=False)
    project_id: Mapped[str] = mapped_column(String, nullable=False)
    text_value: Mapped[str] = mapped_column(Text, nullable=False)
    normalized_text: Mapped[str] = mapped_column(Text, nullable=False)
    entity_type: Mapped[str] = mapped_column(String, nullable=False)
    layer_name: Mapped[str | None] = mapped_column(String, nullable=True)
    block_name: Mapped[str | None] = mapped_column(String, nullable=True)
    handle: Mapped[str | None] = mapped_column(String, nullable=True)
    x: Mapped[float | None] = mapped_column(Float, nullable=True)
    y: Mapped[float | None] = mapped_column(Float, nullable=True)
    review_category: Mapped[str] = mapped_column(String, nullable=False)
    reference_type: Mapped[str] = mapped_column(String, nullable=False)
    requires_human_review: Mapped[bool] = mapped_column(default=True)


class CadReferenceCandidate(Base):
    """A reference candidate detected in extracted text.

    A candidate may be matched against a seeded Phase 6 plan sheet or plan
    reference. confidence_label records review-support confidence, never
    verification.
    """

    __tablename__ = "cad_reference_candidates"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    candidate_id: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    parse_run_id: Mapped[str] = mapped_column(
        ForeignKey("cad_parse_runs.parse_run_id"), nullable=False
    )
    cad_file_id: Mapped[str] = mapped_column(String, nullable=False)
    project_id: Mapped[str] = mapped_column(String, nullable=False)
    reference_text: Mapped[str] = mapped_column(Text, nullable=False)
    normalized_reference: Mapped[str] = mapped_column(String, nullable=False)
    reference_type: Mapped[str] = mapped_column(String, nullable=False)
    source_entity_id: Mapped[str | None] = mapped_column(String, nullable=True)
    source_text_id: Mapped[str | None] = mapped_column(String, nullable=True)
    matched_plan_sheet_id: Mapped[str | None] = mapped_column(
        String, nullable=True
    )
    matched_plan_reference_id: Mapped[str | None] = mapped_column(
        String, nullable=True
    )
    confidence_label: Mapped[str] = mapped_column(String, nullable=False)
    match_reason: Mapped[str] = mapped_column(Text, nullable=False)
    requires_human_review: Mapped[bool] = mapped_column(default=True)


class CadReviewFinding(Base):
    """A review-support finding raised from DXF metadata.

    Every finding is a draft that needs human review. There is no action called
    approve, and no finding approves, certifies, verifies, or validates anything.
    """

    __tablename__ = "cad_review_findings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    cad_review_finding_id: Mapped[str] = mapped_column(
        String, unique=True, nullable=False
    )
    parse_run_id: Mapped[str] = mapped_column(
        ForeignKey("cad_parse_runs.parse_run_id"), nullable=False
    )
    cad_file_id: Mapped[str] = mapped_column(String, nullable=False)
    project_id: Mapped[str] = mapped_column(
        ForeignKey("projects.project_id"), nullable=False
    )
    finding_type: Mapped[str] = mapped_column(String, nullable=False)
    title: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    severity: Mapped[str] = mapped_column(String, nullable=False)
    source_reference_candidate_id: Mapped[str | None] = mapped_column(
        String, nullable=True
    )
    source_layer_extract_id: Mapped[str | None] = mapped_column(
        String, nullable=True
    )
    source_text_extract_id: Mapped[str | None] = mapped_column(
        String, nullable=True
    )
    linked_plan_sheet_id: Mapped[str | None] = mapped_column(
        String, nullable=True
    )
    linked_workflow_item_id: Mapped[str | None] = mapped_column(
        String, nullable=True
    )
    # Phase 12 workflow promotion tracking. promoted_to_workflow guards against
    # duplicate workflow items from the same CAD finding. promoted_workflow_item_id
    # mirrors linked_workflow_item_id for the promotion path.
    promoted_to_workflow: Mapped[bool] = mapped_column(default=False)
    promoted_workflow_item_id: Mapped[str | None] = mapped_column(
        String, nullable=True
    )
    status: Mapped[str] = mapped_column(String, nullable=False)
    requires_human_review: Mapped[bool] = mapped_column(default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=_utcnow
    )


# Phase 13: multi-round resubmittal, revision comparison, and applicant response
# cycle. These models track multiple review rounds for a project. They organize
# review-support evidence across rounds and never approve plans, certify
# compliance, verify CAD, validate design, or make final engineering decisions.
# Revision comparison compares extracted DXF metadata only.


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


# Phase 14: reviewer command center and project health dashboard. These models
# persist an aggregated view of the existing review-support data across all
# phases. The dashboard organizes review-support work and never approves plans,
# certifies compliance, verifies CAD, validates design, or closes or resolves
# issues. It links to existing modules rather than replacing them.


class ProjectCommandCenterSnapshot(Base):
    """A point-in-time aggregated view of the project review-support state."""

    __tablename__ = "command_center_snapshots"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    snapshot_id: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    project_id: Mapped[str] = mapped_column(
        ForeignKey("projects.project_id"), nullable=False
    )
    current_review_cycle_id: Mapped[str | None] = mapped_column(
        String, nullable=True
    )
    generated_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)
    overall_status: Mapped[str] = mapped_column(String, nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    attention_count: Mapped[int] = mapped_column(Integer, default=0)
    ready_for_handoff_count: Mapped[int] = mapped_column(Integer, default=0)
    carry_forward_count: Mapped[int] = mapped_column(Integer, default=0)
    needs_more_information_count: Mapped[int] = mapped_column(Integer, default=0)
    cad_findings_count: Mapped[int] = mapped_column(Integer, default=0)
    resubmittal_count: Mapped[int] = mapped_column(Integer, default=0)
    open_follow_up_count: Mapped[int] = mapped_column(Integer, default=0)
    response_mapping_gap_count: Mapped[int] = mapped_column(Integer, default=0)
    revision_change_count: Mapped[int] = mapped_column(Integer, default=0)
    requires_human_review: Mapped[bool] = mapped_column(default=True)


class ProjectHealthMetric(Base):
    """A single review-support health metric in a command center snapshot."""

    __tablename__ = "project_health_metrics"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    metric_id: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    snapshot_id: Mapped[str] = mapped_column(
        ForeignKey("command_center_snapshots.snapshot_id"), nullable=False
    )
    project_id: Mapped[str] = mapped_column(String, nullable=False)
    metric_type: Mapped[str] = mapped_column(String, nullable=False)
    label: Mapped[str] = mapped_column(String, nullable=False)
    value: Mapped[str] = mapped_column(String, nullable=False)
    severity: Mapped[str] = mapped_column(String, nullable=False)
    source_module: Mapped[str] = mapped_column(String, nullable=False)
    source_route: Mapped[str] = mapped_column(String, nullable=False)
    requires_human_review: Mapped[bool] = mapped_column(default=True)


class ReviewerAttentionItem(Base):
    """A review-support item that needs reviewer attention, with a next step."""

    __tablename__ = "reviewer_attention_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    attention_item_id: Mapped[str] = mapped_column(
        String, unique=True, nullable=False
    )
    snapshot_id: Mapped[str] = mapped_column(
        ForeignKey("command_center_snapshots.snapshot_id"), nullable=False
    )
    project_id: Mapped[str] = mapped_column(String, nullable=False)
    title: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    attention_type: Mapped[str] = mapped_column(String, nullable=False)
    severity: Mapped[str] = mapped_column(String, nullable=False)
    source_module: Mapped[str] = mapped_column(String, nullable=False)
    source_type: Mapped[str] = mapped_column(String, nullable=False)
    source_id: Mapped[str | None] = mapped_column(String, nullable=True)
    target_route: Mapped[str] = mapped_column(String, nullable=False)
    recommended_next_step: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)
    requires_human_review: Mapped[bool] = mapped_column(default=True)


class ProjectTimelineEvent(Base):
    """A meaningful review-support event in the project timeline."""

    __tablename__ = "project_timeline_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    timeline_event_id: Mapped[str] = mapped_column(
        String, unique=True, nullable=False
    )
    project_id: Mapped[str] = mapped_column(String, nullable=False)
    event_type: Mapped[str] = mapped_column(String, nullable=False)
    event_title: Mapped[str] = mapped_column(String, nullable=False)
    event_description: Mapped[str] = mapped_column(Text, nullable=False)
    source_module: Mapped[str] = mapped_column(String, nullable=False)
    source_type: Mapped[str] = mapped_column(String, nullable=False)
    source_id: Mapped[str | None] = mapped_column(String, nullable=True)
    event_time: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)
    target_route: Mapped[str] = mapped_column(String, nullable=False)
    requires_human_review: Mapped[bool] = mapped_column(default=False)


class ReviewReadinessCheck(Base):
    """A review-support readiness check in a command center snapshot."""

    __tablename__ = "review_readiness_checks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    readiness_check_id: Mapped[str] = mapped_column(
        String, unique=True, nullable=False
    )
    snapshot_id: Mapped[str] = mapped_column(
        ForeignKey("command_center_snapshots.snapshot_id"), nullable=False
    )
    project_id: Mapped[str] = mapped_column(String, nullable=False)
    check_type: Mapped[str] = mapped_column(String, nullable=False)
    label: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String, nullable=False)
    source_module: Mapped[str] = mapped_column(String, nullable=False)
    source_count: Mapped[int] = mapped_column(Integer, default=0)
    blocker_count: Mapped[int] = mapped_column(Integer, default=0)
    recommended_next_step: Mapped[str] = mapped_column(Text, nullable=False)
    requires_human_review: Mapped[bool] = mapped_column(default=True)


class DashboardReviewerNote(Base):
    """A reviewer note recorded on the project command center dashboard."""

    __tablename__ = "dashboard_reviewer_notes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    note_id: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    project_id: Mapped[str] = mapped_column(String, nullable=False)
    snapshot_id: Mapped[str | None] = mapped_column(String, nullable=True)
    note_text: Mapped[str] = mapped_column(Text, nullable=False)
    reviewer_name: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)
    source_context: Mapped[str | None] = mapped_column(String, nullable=True)
    requires_human_review: Mapped[bool] = mapped_column(default=True)
