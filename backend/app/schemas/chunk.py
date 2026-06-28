"""Pydantic schemas for document chunks."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class ChunkRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    chunk_id: str
    project_id: str
    document_id: str
    document_type: str
    file_name: str
    page_number: int | None = None
    section_heading: str | None = None
    chunk_index: int
    content: str
    keywords: list[str]
    related_checklist_items: list[str]
    related_findings: list[str]
    chunk_origin: str | None = None


class DocumentChunkingSummary(BaseModel):
    """Summary returned when real-derived chunks are rebuilt for a document.

    Reports counts and statuses only. It does not return chunk content here and
    does not imply any final review outcome.
    """

    document_id: str
    project_id: str
    document_type: str
    file_name: str
    pages_chunked: int
    chunk_count: int
    removed_prior_chunk_count: int
