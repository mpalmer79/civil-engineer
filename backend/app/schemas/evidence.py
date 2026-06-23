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
