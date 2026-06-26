"""Storage service: selects and exposes the configured storage provider (Sprint 6).

Chooses the local or S3-compatible provider based on STORAGE_PROVIDER and offers
high-level helpers for saving and reading a document's bytes. Object storage
credentials are read only when STORAGE_PROVIDER is "s3" and are never returned in
any response. Reading falls back to a document's legacy local storage_path when a
storage_key is not yet set, so Sprint 1 uploads keep working.
"""

from __future__ import annotations

from pathlib import Path

from app.core.config import get_settings
from app.core.safety import ALLOWED_STORAGE_PROVIDERS
from app.services.storage.base import StorageError, StorageProvider, StoredObject
from app.services.storage.local_storage import LocalStorageProvider
from app.services.storage.s3_storage import S3CompatibleStorageProvider


def get_storage_provider() -> StorageProvider:
    """Return the storage provider configured by STORAGE_PROVIDER."""

    settings = get_settings()
    provider = (settings.STORAGE_PROVIDER or "local").strip().lower()
    if provider not in ALLOWED_STORAGE_PROVIDERS:
        raise StorageError(
            f"Unsupported storage provider '{provider}'. Allowed: "
            f"{', '.join(sorted(ALLOWED_STORAGE_PROVIDERS))}.",
            status_code=500,
        )
    if provider == "s3":
        return S3CompatibleStorageProvider(settings)
    return LocalStorageProvider(settings.local_storage_dir)


def save_document_file(
    *,
    project_id: str,
    document_id: str,
    original_filename: str,
    content_bytes: bytes,
    content_type: str | None,
) -> StoredObject:
    """Store an uploaded document's bytes through the configured provider."""

    provider = get_storage_provider()
    storage_key = provider.generate_storage_key(
        project_id, document_id, original_filename
    )
    return provider.save_file(storage_key, content_bytes, content_type)


def read_document_bytes(document) -> bytes:
    """Return the stored bytes for a document, by storage key or legacy path."""

    if getattr(document, "storage_key", None):
        provider = _provider_for_document(document)
        return provider.read_file(document.storage_key)
    # Backward compatibility: Sprint 1 documents stored a local path only.
    storage_path = getattr(document, "storage_path", None)
    if storage_path and Path(storage_path).is_file():
        return Path(storage_path).read_bytes()
    raise StorageError("The stored file is not available.", status_code=404)


def document_file_exists(document) -> bool:
    """Return True if a document's stored file is available."""

    if getattr(document, "storage_key", None):
        provider = _provider_for_document(document)
        return provider.file_exists(document.storage_key)
    storage_path = getattr(document, "storage_path", None)
    return bool(storage_path and Path(storage_path).is_file())


def document_file_size(document) -> int | None:
    if getattr(document, "storage_key", None):
        provider = _provider_for_document(document)
        return provider.get_file_size(document.storage_key)
    storage_path = getattr(document, "storage_path", None)
    if storage_path and Path(storage_path).is_file():
        return Path(storage_path).stat().st_size
    return None


def _provider_for_document(document) -> StorageProvider:
    """Return the provider matching a document's recorded storage provider.

    Falls back to the configured provider when the document predates Sprint 6.
    """

    recorded = getattr(document, "storage_provider", None)
    settings = get_settings()
    if recorded == "local":
        return LocalStorageProvider(settings.local_storage_dir)
    if recorded == "s3":
        return S3CompatibleStorageProvider(settings)
    return get_storage_provider()


def storage_health() -> dict:
    """Return safe storage health info for the configured provider."""

    try:
        provider = get_storage_provider()
        info = provider.health()
        info.setdefault("provider", provider.get_provider_name())
        return info
    except StorageError as exc:
        return {"provider": "unknown", "configured": False, "error": exc.message}
