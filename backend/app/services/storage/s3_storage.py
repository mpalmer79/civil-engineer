"""S3-compatible object storage provider for deployment (Sprint 6).

Stores uploaded files in an S3-compatible bucket so uploads survive redeploys.
Credentials are read from backend environment variables only and are never
exposed to the frontend or returned in API responses. boto3 is imported lazily so
the local provider and the test suite do not require it. A client may be injected
for testing without real credentials.
"""

from __future__ import annotations

from app.core.config import Settings
from app.services.storage.base import StorageError, StorageProvider, StoredObject


class S3CompatibleStorageProvider(StorageProvider):
    name = "s3"

    def __init__(self, settings: Settings, *, client=None) -> None:
        self._bucket = settings.OBJECT_STORAGE_BUCKET
        self._region = settings.OBJECT_STORAGE_REGION
        self._endpoint_url = settings.OBJECT_STORAGE_ENDPOINT_URL or None
        self._force_path_style = settings.OBJECT_STORAGE_FORCE_PATH_STYLE
        self._signed_url_expire = settings.OBJECT_STORAGE_SIGNED_URL_EXPIRE_SECONDS
        self._access_key = settings.OBJECT_STORAGE_ACCESS_KEY_ID
        self._secret_key = settings.OBJECT_STORAGE_SECRET_ACCESS_KEY
        self._client = client

    @property
    def bucket(self) -> str:
        if not self._bucket:
            raise StorageError(
                "Object storage is not configured (missing bucket).",
                status_code=500,
            )
        return self._bucket

    def _get_client(self):
        if self._client is not None:
            return self._client
        try:
            import boto3  # noqa: PLC0415 - lazy import so local provider needs no boto3
            from botocore.config import Config
        except ImportError as exc:  # pragma: no cover - boto3 is a pinned dependency
            raise StorageError(
                "Object storage support requires the boto3 dependency.",
                status_code=500,
            ) from exc
        config = Config(
            s3={"addressing_style": "path" if self._force_path_style else "auto"}
        )
        self._client = boto3.client(
            "s3",
            region_name=self._region,
            endpoint_url=self._endpoint_url,
            aws_access_key_id=self._access_key or None,
            aws_secret_access_key=self._secret_key or None,
            config=config,
        )
        return self._client

    def save_file(
        self, storage_key: str, content_bytes: bytes, content_type: str | None
    ) -> StoredObject:
        client = self._get_client()
        kwargs = {
            "Bucket": self.bucket,
            "Key": storage_key,
            "Body": content_bytes,
        }
        if content_type:
            kwargs["ContentType"] = content_type
        try:
            response = client.put_object(**kwargs)
        except Exception as exc:  # noqa: BLE001 - any client failure is a storage failure
            raise StorageError(
                "The file could not be stored in object storage.",
                status_code=502,
            ) from exc
        return StoredObject(
            storage_key=storage_key,
            provider=self.name,
            bucket=self._bucket or None,
            size_bytes=len(content_bytes),
            etag=(response or {}).get("ETag"),
            version_id=(response or {}).get("VersionId"),
        )

    def read_file(self, storage_key: str) -> bytes:
        client = self._get_client()
        try:
            response = client.get_object(Bucket=self.bucket, Key=storage_key)
            body = response["Body"]
            return body.read()
        except Exception as exc:  # noqa: BLE001 - missing object is a safe failure
            raise StorageError(
                "The stored file is not available.", status_code=404
            ) from exc

    def file_exists(self, storage_key: str) -> bool:
        client = self._get_client()
        try:
            client.head_object(Bucket=self.bucket, Key=storage_key)
            return True
        except Exception:  # noqa: BLE001 - any error means not available
            return False

    def get_file_size(self, storage_key: str) -> int | None:
        client = self._get_client()
        try:
            response = client.head_object(Bucket=self.bucket, Key=storage_key)
            return int(response.get("ContentLength")) if response else None
        except Exception:  # noqa: BLE001
            return None

    def delete_file(self, storage_key: str) -> None:
        client = self._get_client()
        try:
            client.delete_object(Bucket=self.bucket, Key=storage_key)
        except Exception:  # noqa: BLE001 - best-effort delete
            pass

    def create_download_url(
        self, storage_key: str, expires_seconds: int | None = None
    ) -> str | None:
        client = self._get_client()
        expires = expires_seconds or self._signed_url_expire
        try:
            return client.generate_presigned_url(
                "get_object",
                Params={"Bucket": self.bucket, "Key": storage_key},
                ExpiresIn=expires,
            )
        except Exception:  # noqa: BLE001 - signed URLs are optional
            return None

    def health(self) -> dict:
        # Report configuration status only; never include keys or the endpoint
        # secret material.
        return {
            "provider": self.name,
            "configured": bool(self._bucket),
            "bucket_set": bool(self._bucket),
            "region": self._region,
        }
