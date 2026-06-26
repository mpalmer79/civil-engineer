"""Pydantic schemas for documents.

A document processing status tracks intake handling only. It never implies that
a document was approved, certified, verified, or validated.
"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class DocumentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    document_id: str
    project_id: str
    file_name: str
    document_type: str
    status: str
    purpose: str
    expected_key_information: str
    intentionally_missing_or_conflicting_information: str | None = None
    # Production foundation metadata. Optional so seeded demo documents validate.
    source_mode: str = "demo_fixture"
    original_file_name: str | None = None
    upload_status: str | None = None
    processing_status: str | None = None
    content_type: str | None = None
    file_size_bytes: int | None = None
    checksum_sha256: str | None = None
    revision_label: str | None = None
    revision_date: str | None = None
    uploaded_by_name: str | None = None
    uploaded_at: datetime | None = None
    registered_at: datetime | None = None
    is_superseded: bool = False
    page_count: int | None = None
    sheet_count: int | None = None
    classification_confidence: float | None = None


class DocumentRegister(BaseModel):
    """Request body for registering document metadata (no file bytes)."""

    original_file_name: str
    document_type: str = "other"
    purpose: str | None = None
    expected_key_information: str | None = None
    content_type: str | None = None
    file_size_bytes: int | None = None
    revision_label: str | None = None
    revision_date: str | None = None
    uploaded_by_name: str = "Demo Reviewer"
