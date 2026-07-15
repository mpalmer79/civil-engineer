"""Evidence bounded context: citations, retrieval queries, and evidence candidates."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import JSON, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.database import Base
from app.db.models.shared import _utcnow

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
