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
