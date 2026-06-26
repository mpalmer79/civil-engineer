"""Pydantic schemas for PDF page indexing and evidence citations (Sprint 2).

These represent page-level review records and reviewer-selected evidence
citations. A page record tracks digital PDF text extraction state only; a
citation is a reviewer-selected source reference. Neither implies a final
engineering decision, approval, certification, or that a design is safe.
"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class DocumentPageResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    document_page_id: str
    project_id: str
    document_id: str
    page_number: int
    page_label: str | None = None
    extracted_text: str | None = None
    text_extraction_status: str
    text_extraction_method: str | None = None
    char_count: int = 0
    word_count: int = 0
    extraction_warnings: list[str] = []
    indexed_at: datetime | None = None


class DocumentIndexingSummary(BaseModel):
    document_id: str
    page_count: int
    pages_with_text: int
    pages_without_text: int
    warning_count: int
    processing_status: str
    text_extraction_status: str
    indexed_at: datetime | None = None
    summary: str


class EvidenceCitationCreate(BaseModel):
    """Request body for a reviewer-selected evidence citation.

    document_id is required. Provide a document_page_id or page_number to cite a
    specific page; omit both to cite a document generally. quoted_excerpt is
    optional and reviewer-selected. citation_type and citation_status, when set,
    are validated against the review-support vocabulary.
    """

    document_id: str
    document_page_id: str | None = None
    page_number: int | None = None
    section_label: str | None = None
    quoted_excerpt: str | None = None
    reviewer_note: str | None = None
    citation_type: str = "reviewer_selected"
    citation_status: str | None = None
    created_by_name: str = "Demo Reviewer"


class EvidenceCitationUpdate(BaseModel):
    section_label: str | None = None
    quoted_excerpt: str | None = None
    reviewer_note: str | None = None
    citation_status: str | None = None
    citation_type: str | None = None


class EvidenceCitationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    evidence_citation_id: str
    project_id: str
    finding_id: str
    document_id: str
    document_page_id: str | None = None
    page_number: int | None = None
    page_label: str | None = None
    section_label: str | None = None
    quoted_excerpt: str | None = None
    reviewer_note: str | None = None
    citation_type: str
    citation_status: str
    created_by_name: str | None = None
    source_mode: str = "user_created"
    created_at: datetime | None = None
    updated_at: datetime | None = None
