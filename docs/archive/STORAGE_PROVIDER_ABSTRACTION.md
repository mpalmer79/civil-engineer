# Storage Provider Abstraction

This document describes the durable file storage abstraction added in Production
Foundations Sprint 6.

Storage tracks where an uploaded review-support document is stored and whether it
is available. It never approves plans, certifies compliance, validates design, or
makes any final engineering decision, and it never changes the review-support
boundary.

## Storage provider interface

`app/services/storage/base.py` defines `StorageProvider`, the interface every
provider implements:

- `generate_storage_key(project_id, document_id, original_filename)`
- `save_file(storage_key, content_bytes, content_type) -> StoredObject`
- `read_file(storage_key) -> bytes`
- `file_exists(storage_key) -> bool`
- `get_file_size(storage_key) -> int | None`
- `delete_file(storage_key)` (optional)
- `create_download_url(storage_key, expires_seconds) -> str | None`
- `get_provider_name() -> str`
- `health() -> dict`

`StoredObject` carries only safe metadata: the storage key, provider name,
optional bucket, size, and optional ETag and version id. It never carries a raw
filesystem path or any credential.

## Local storage provider

`LocalStorageProvider` stores files under a configured local directory using the
generated storage key. It resolves every key inside the configured root and
rejects keys that would escape it, which blocks path traversal. It never returns
a raw absolute path. Local storage is intended for development and the
self-contained demo; it is not durable across redeploys without a mounted volume.

## S3-compatible provider

`S3CompatibleStorageProvider` stores files in an S3-compatible bucket using
boto3. boto3 is imported lazily so the local provider and the test suite do not
require it, and a client may be injected for testing without real credentials.
Credentials come from backend environment variables only and are never exposed to
the frontend or returned in any response. The provider supports object put, get,
head (existence and size), delete, and optional presigned download URLs.

## Generated storage keys

`generate_storage_key` returns `projects/<project_id>/<document_id>/<token><ext>`,
where the token is a generated id and the extension is the validated lowercase
extension of the original filename. The raw original filename is never used in
the key, which prevents path traversal and avoids leaking user-provided names
into storage paths.

## Metadata-only database records

The `Document` row stores only safe storage metadata: `storage_provider`,
`storage_key`, `storage_bucket`, `storage_etag`, `storage_version_id`,
`file_available`, `last_storage_check_at`, `download_count`, and
`last_downloaded_at`. API responses expose only a safe subset (provider,
availability, download counts). The raw `storage_path`, `storage_key`, bucket,
and any credential are never returned to the frontend.

## Checksum behavior

A sha256 checksum is computed from the uploaded bytes before storage and recorded
on the document. It lets a reviewer confirm a stored file matches what was
uploaded. The checksum is review-support metadata, not an engineering
determination.

## File availability checks

`storage_service.document_file_exists` asks the provider whether the stored
object exists. The download and storage-status routes use it to set
`file_available` and `last_storage_check_at`, and to return a safe message when a
file is missing.

## Signed URL strategy

The S3 provider can generate a short-lived presigned GET URL
(`create_download_url`), bounded by `OBJECT_STORAGE_SIGNED_URL_EXPIRE_SECONDS`.
The current download route streams bytes through the access-controlled backend
rather than returning a signed URL, so signed URLs never appear in responses or
audit metadata. Returning signed URLs directly is a possible future optimization
and would remain access-controlled.

## Fallback behavior

`storage_service.read_document_bytes` reads through the recorded provider and
storage key. For Sprint 1 documents that have only a legacy local
`storage_path`, it falls back to reading that path, so older uploads keep
working. When neither a storage key nor an existing path is present, it raises a
safe storage error and the caller returns a clear message.

## Known limitations

- Object storage must be configured in deployment for durable persistence; the
  default local provider is for development only.
- No malware scanning.
- No OCR and no live AI calls.
- No enterprise records-retention system.
- Files are loaded into memory for storage and indexing within the configured
  maximum upload size; very large files are out of scope.
