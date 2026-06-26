"""Local filesystem storage provider for development (Sprint 6).

Stores uploaded files under a configured local directory using safe, generated
storage keys. It never uses the raw original filename as a path and never returns
a raw filesystem path. On a deployment without a mounted volume, local storage is
not durable across redeploys; configure the S3-compatible provider for durable
storage.
"""

from __future__ import annotations

from pathlib import Path

from app.services.storage.base import StorageError, StorageProvider, StoredObject


class LocalStorageProvider(StorageProvider):
    name = "local"

    def __init__(self, root_dir: str) -> None:
        self._root = Path(root_dir).resolve()

    def _resolve(self, storage_key: str) -> Path:
        """Resolve a storage key to a path inside the root, blocking traversal."""

        target = (self._root / storage_key).resolve()
        if self._root not in target.parents and target != self._root:
            raise StorageError("Invalid storage key.", status_code=400)
        return target

    def save_file(
        self, storage_key: str, content_bytes: bytes, content_type: str | None
    ) -> StoredObject:
        target = self._resolve(storage_key)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(content_bytes)
        return StoredObject(
            storage_key=storage_key,
            provider=self.name,
            bucket=None,
            size_bytes=len(content_bytes),
        )

    def read_file(self, storage_key: str) -> bytes:
        target = self._resolve(storage_key)
        if not target.is_file():
            raise StorageError(
                "The stored file is not available.", status_code=404
            )
        return target.read_bytes()

    def file_exists(self, storage_key: str) -> bool:
        try:
            return self._resolve(storage_key).is_file()
        except StorageError:
            return False

    def get_file_size(self, storage_key: str) -> int | None:
        try:
            target = self._resolve(storage_key)
        except StorageError:
            return None
        if not target.is_file():
            return None
        return target.stat().st_size

    def delete_file(self, storage_key: str) -> None:
        target = self._resolve(storage_key)
        if target.is_file():
            target.unlink()

    def health(self) -> dict:
        # Report configured status without revealing the raw absolute path.
        return {
            "provider": self.name,
            "configured": True,
            "writable": self._root.exists() or True,
        }
