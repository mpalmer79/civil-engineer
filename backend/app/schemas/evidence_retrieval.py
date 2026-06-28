"""Pydantic schemas for evidence retrieval and the reviewer draft queue (Sprint 3).

These represent deterministic, local retrieval over indexed PDF page text and a
reviewer-controlled queue of evidence candidates. A search result and a saved
candidate are review-support evidence for a human reviewer, not a conclusion.
Nothing here approves plans, certifies compliance, verifies CAD, validates
design, declares a project safe, or finalizes a review outcome.
"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class EvidenceSearchFilters(BaseModel):
    document_id: str | None = None
    document_type: str | None = None
    text_extraction_status: str | None = None
    page_min: int | None = None
    page_max: int | None = None
    checklist_item_id: str | None = None
    finding_id: str | None = None


class EvidenceSearchRequest(BaseModel):
    """Request body for a deterministic indexed-evidence search.

    query_text is required (at least two characters). query_type selects the
    retrieval mode. filters are optional and metadata-only. limit is bounded to
    a safe maximum by the service.
    """

    query_text: str = Field(..., min_length=1)
    query_type: str = "keyword"
    filters: EvidenceSearchFilters = Field(default_factory=EvidenceSearchFilters)
    limit: int = 10


class EvidenceSearchResult(BaseModel):
    """A single ranked retrieval candidate. excerpt is short, never full text.

    chunk_id is populated only for results that come from the real-derived
    DocumentChunk search path. Page-text search results leave it unset.
    """

    document_id: str
    document_name: str
    document_type: str | None = None
    chunk_id: str | None = None
    document_page_id: str | None = None
    page_number: int | None = None
    page_label: str | None = None
    text_extraction_status: str | None = None
    excerpt: str | None = None
    match_terms: list[str] = []
    ranking_score: float = 0.0
    ranking_reason: str | None = None
    candidate_origin: str | None = None
    retrieval_query_id: str | None = None


class ChunkEvidenceSearchRequest(BaseModel):
    """Request body for retrieval over real-derived document chunks.

    query_text is required (at least two characters). mode selects keyword,
    semantic, or hybrid retrieval. filters are optional and metadata-only. limit
    is bounded to a safe maximum by the service. The search only covers
    real-derived chunks (those built from indexed PDF page text); seeded demo
    chunks are never included.
    """

    query_text: str = Field(..., min_length=1)
    mode: str = "keyword"
    filters: EvidenceSearchFilters = Field(default_factory=EvidenceSearchFilters)
    limit: int = 10


class EvidenceSearchResponse(BaseModel):
    project_id: str
    query_text: str
    query_type: str
    retrieval_query_id: str | None = None
    result_count: int
    results: list[EvidenceSearchResult] = []
    message: str | None = None


class EvidenceCandidateCreate(BaseModel):
    """Request body to save a retrieval result into the reviewer draft queue."""

    document_id: str
    document_page_id: str | None = None
    page_number: int | None = None
    finding_id: str | None = None
    checklist_item_id: str | None = None
    retrieval_query_id: str | None = None
    candidate_title: str
    candidate_excerpt: str | None = None
    match_terms: list[str] = []
    ranking_score: float = 0.0
    ranking_reason: str | None = None
    candidate_status: str = "saved_for_review"
    candidate_origin: str = "manual_save"
    reviewer_note: str | None = None


class EvidenceCandidateUpdate(BaseModel):
    candidate_status: str | None = None
    reviewer_note: str | None = None


class CandidateDismissRequest(BaseModel):
    reviewer_note: str | None = None


class EvidenceCandidateResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    evidence_candidate_id: str
    project_id: str
    retrieval_query_id: str | None = None
    document_id: str
    document_page_id: str | None = None
    page_number: int | None = None
    finding_id: str | None = None
    checklist_item_id: str | None = None
    candidate_title: str
    candidate_excerpt: str | None = None
    match_terms: list[str] = []
    ranking_score: float = 0.0
    ranking_reason: str | None = None
    candidate_status: str
    candidate_origin: str
    reviewer_note: str | None = None
    created_by_name: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
    dismissed_at: datetime | None = None
    promoted_finding_id: str | None = None


class PromoteCandidateToDraftFindingRequest(BaseModel):
    """Reviewer-confirmed content for a draft finding promoted from a candidate.

    Values may be prefilled from the candidate, but the reviewer can edit them.
    The risk level is reviewer-entered, never a system conclusion.
    """

    title: str | None = None
    category: str | None = None
    risk_level: str | None = None
    evidence_status: str | None = None
    evidence_to_find: str | None = None
    reason_it_matters: str | None = None
    recommended_human_action: str | None = None
    reviewer_note: str | None = None
    citation_excerpt: str | None = None
    human_review_status: str | None = None


class FindingSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    finding_id: str
    project_id: str
    title: str
    category: str
    risk_level: str
    evidence_status: str | None = None
    human_review_status: str
    finding_origin: str
    source_mode: str
    created_by_name: str | None = None


class CitationSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    evidence_citation_id: str
    project_id: str
    finding_id: str
    document_id: str
    document_page_id: str | None = None
    page_number: int | None = None
    citation_type: str
    citation_status: str


class PromoteCandidateToDraftFindingResponse(BaseModel):
    finding: FindingSummary
    citation: CitationSummary
    candidate: EvidenceCandidateResponse


class ChunkEmbeddingBackfillResponse(BaseModel):
    """Summary of a chunk embedding backfill. Counts and model identity only."""

    model_config = ConfigDict(protected_namespaces=())

    project_id: str
    provider: str
    model_name: str
    model_version: str
    dimension: int
    chunk_count: int
    embedded: int
    refreshed: int
    skipped_current: int
    skipped_empty: int
    failed: int


class RetrievalQueryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    retrieval_query_id: str
    project_id: str
    query_text: str
    query_type: str | None = None
    filters: dict = {}
    result_count: int = 0
    related_checklist_item_id: str | None = None
    related_finding_id: str | None = None
    created_by_name: str | None = None
    created_at: datetime | None = None
