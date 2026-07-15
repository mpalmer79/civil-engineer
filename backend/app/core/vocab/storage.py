"""Durable file storage provider and upload handling vocabulary."""

from __future__ import annotations

# Production Foundations Sprint 6 durable file storage vocabulary. Storage tracks
# where an uploaded review-support record is stored and whether it is available.
# It never implies a final engineering decision, approval, certification, or
# compliance, and it never changes the review-support boundary.

# Storage provider names. local stores files on the service file system for
# development; s3 uses S3-compatible object storage for deployment.
ALLOWED_STORAGE_PROVIDERS: set[str] = {"local", "s3"}

# Document upload handling statuses for stored files. None implies approval; they
# track storage handling only. storage_failed records that a file could not be
# stored, not an engineering determination.
ALLOWED_STORAGE_UPLOAD_STATUSES: set[str] = {
    "not_uploaded",
    "upload_started",
    "stored",
    "storage_failed",
    "file_unavailable",
}
