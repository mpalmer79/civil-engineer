"""Storage provider interface for durable file persistence (Sprint 6).

A storage provider stores uploaded review-support documents and reports whether
they are available. It never approves plans, certifies compliance, validates
design, or makes any final engineering decision. Providers expose only safe,
generated storage keys; they never expose raw local filesystem paths or object
storage credentials in their return values.
"""

from __future__ import annotations

import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path


class StorageError(Exception):
    """Raised when a storage operation fails."""

    def __init__(self, message: str, *, status_code: int = 500) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code


@dataclass
class StoredObject:
    """Safe metadata returned after storing a file. Carries no secrets."""

    storage_key: str
    provider: str
    bucket: str | None
    size_bytes: int
    etag: str | None = None
    version_id: str | None = None


def generate_storage_key(
    project_id: str, document_id: str, original_filename: str
) -> str:
    """Return a safe, generated storage key for an uploaded file.

    The key is namespaced by project and document and uses a generated id plus
    only the validated lowercase extension of the original filename. The raw
    original filename is never used in the key, which prevents path traversal and
    avoids leaking user-provided names into storage paths.
    """

    extension = Path(original_filename or "").suffix.lower()
    safe_project = "".join(c for c in project_id if c.isalnum() or c in "_-")
    safe_document = "".join(c for c in document_id if c.isalnum() or c in "_-")
    token = uuid.uuid4().hex[:16]
    return f"projects/{safe_project}/{safe_document}/{token}{extension}"


class StorageProvider(ABC):
    """Abstract storage provider. Concrete providers store and read file bytes."""

    name: str = "base"

    def get_provider_name(self) -> str:
        return self.name

    def generate_storage_key(
        self, project_id: str, document_id: str, original_filename: str
    ) -> str:
        return generate_storage_key(project_id, document_id, original_filename)

    @abstractmethod
    def save_file(
        self, storage_key: str, content_bytes: bytes, content_type: str | None
    ) -> StoredObject:
        """Store the bytes under the storage key and return safe metadata."""

    @abstractmethod
    def read_file(self, storage_key: str) -> bytes:
        """Return the stored bytes for a storage key, or raise StorageError."""

    @abstractmethod
    def file_exists(self, storage_key: str) -> bool:
        """Return True if a file exists for the storage key."""

    @abstractmethod
    def get_file_size(self, storage_key: str) -> int | None:
        """Return the stored file size in bytes, or None if unavailable."""

    def delete_file(self, storage_key: str) -> None:  # pragma: no cover - optional
        """Delete the stored file. Optional; default is a no-op."""

    def create_download_url(
        self, storage_key: str, expires_seconds: int = 300
    ) -> str | None:
        """Return a short-lived download URL when supported, else None."""

        return None

    @abstractmethod
    def health(self) -> dict:
        """Return safe provider health info. Never includes secrets."""
