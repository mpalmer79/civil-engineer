"""Pydantic schemas for retrieval results and finding source evidence."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class RetrievalResult(BaseModel):
    """A single retrieval result returned by search and evidence endpoints.

    A retrieval result is source evidence for a human reviewer. It is not a
    conclusion and never carries final-decision language.
    """

    chunk_id: str | None
    document_id: str
    file_name: str
    document_type: str
    page_number: int | None = None
    section_heading: str | None = None
    excerpt: str
    relevance_reason: str
    score: float
    evidence_role: str | None = None
    safety_note: str


class FindingSourceRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    finding_source_id: str
    finding_id: str
    document_id: str
    chunk_id: str | None = None
    page_number: int | None = None
    excerpt: str
    evidence_role: str
    confidence: float
    sheet_number: str | None = None
    section_label: str | None = None
    source_mode: str = "demo_fixture"


class EvidenceReferenceCreate(BaseModel):
    """Request body for a basic manual evidence reference on a finding.

    This is a review-support evidence reference placeholder, not a final
    citation engine. reviewer_note records why the document is relevant.
    """

    document_id: str
    reviewer_note: str
    page_number: int | None = None
    sheet_number: str | None = None
    section_label: str | None = None
    created_by_name: str = "Demo Reviewer"
