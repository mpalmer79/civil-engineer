"""Pydantic schemas for durable file storage (Sprint 6).

These represent safe storage metadata for a stored document and the configured
storage provider's health. They never expose raw filesystem paths, storage keys,
object storage credentials, or signed URLs in a way that leaks secrets. Nothing
here implies a final engineering decision, approval, certification, or compliance.
"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class DocumentStorageStatus(BaseModel):
    document_id: str
    project_id: str
    file_available: bool
    storage_provider: str | None = None
    processing_status: str | None = None
    upload_status: str | None = None
    content_type: str | None = None
    file_size_bytes: int | None = None
    checksum_sha256: str | None = None
    original_file_name: str | None = None
    uploaded_at: datetime | None = None
    last_storage_check_at: datetime | None = None
    download_count: int = 0
    last_downloaded_at: datetime | None = None
    message: str | None = None


class StorageHealthResponse(BaseModel):
    provider: str
    configured: bool
    detail: str | None = None
