# API: Durable File Storage

Production Foundations Sprint 6 routes for durable file storage. All routes are
under the `/api/v1` prefix.

Files are stored and read through the storage provider abstraction (local or
S3-compatible). Access control from Sprint 5 is preserved. Responses never
include raw filesystem paths, storage keys, object storage credentials, or signed
URLs. Nothing here approves plans, certifies compliance, verifies CAD, validates
design, or makes any final engineering decision.

## Document upload

`POST /api/v1/projects/{project_id}/documents/upload` (multipart) is unchanged in
shape but now stores the file through the configured storage provider. It
requires reviewer access for real projects (the public demo behavior is
unchanged). The response is safe document metadata, including
`storage_provider`, `file_available`, `download_count`, and `checksum_sha256`. It
never includes the raw storage path or storage key.

On success, the document records the provider and a generated storage key, sets
`file_available` to true, and the backend writes `document_upload_started` and
`document_stored` audit events. A storage failure writes
`document_storage_failed` and returns a safe error.

## Document download

`GET /api/v1/projects/{project_id}/documents/{document_id}/download`

Requires project read access. Streams the file bytes with a safe
`Content-Disposition` filename. Increments `download_count`, updates
`last_downloaded_at`, and writes a `document_downloaded` audit event. If the file
is not available in storage, it writes `document_file_unavailable` and returns
404 with a safe message. The storage key and any signed URL stay on the backend.

## Document storage status

`GET /api/v1/projects/{project_id}/documents/{document_id}/storage-status`

Requires project read access. Checks provider availability and returns safe
metadata:

```json
{
  "document_id": "doc_user_abc",
  "project_id": "proj_user_xyz",
  "file_available": true,
  "storage_provider": "local",
  "processing_status": "indexed_with_text",
  "upload_status": "stored",
  "content_type": "application/pdf",
  "file_size_bytes": 20480,
  "checksum_sha256": "<64 hex chars>",
  "original_file_name": "Plan Set.pdf",
  "uploaded_at": "2026-06-26T00:00:00Z",
  "last_storage_check_at": "2026-06-26T00:05:00Z",
  "download_count": 2,
  "last_downloaded_at": "2026-06-26T00:04:00Z",
  "message": null
}
```

The response never includes a raw filesystem path, storage key, bucket, or any
credential.

## Storage health

`GET /api/v1/storage/health`

Requires an authenticated user. Returns the configured provider name and whether
it is configured, without revealing secrets:

```json
{
  "provider": "local",
  "configured": true,
  "detail": "Local development storage is configured."
}
```

## Auth and access requirements

- Upload requires reviewer access.
- Download requires project read access.
- Storage status requires project read access.
- Storage health requires an authenticated user.
- The public Brookside Meadows demo remains readable when
  `AUTH_ALLOW_PUBLIC_DEMO` is true. Users without access to a real project
  receive 403 on download and storage status.

## Safety notes

Audit metadata for storage actions may include the document id, project id,
storage provider, file size, checksum, content type, and status. It never
includes object storage access keys or secrets, signed URLs, raw local
filesystem paths, full file content, extracted page text, tokens, or passwords.
There is no `approved`, `certified`, `verified`, `passed`, `failed`, `resolved`,
or `closed` status anywhere in this API.
