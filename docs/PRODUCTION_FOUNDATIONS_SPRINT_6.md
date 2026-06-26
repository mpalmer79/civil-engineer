# Production Foundations Sprint 6: Durable Object Storage and Deployment-Ready File Persistence

This sprint replaces local-only uploaded file persistence with a storage
provider abstraction that supports both local development storage and
deployment-ready durable object storage.

The product moves from "uploaded files remain local unless deployment storage is
configured" to "uploaded project files are managed through a storage provider
abstraction, with local storage for development and S3-compatible object storage
support for deployment."

This sprint is about persistence and operational readiness. It does not change
the engineering-review boundary. Durable storage preserves records; it does not
decide whether the records satisfy engineering requirements. Civil Engineer AI
still does not approve plans, certify compliance, verify CAD, validate design,
declare a project safe, or replace a licensed Professional Engineer.

Live demo: https://civil-engineer.up.railway.app/

## What Sprint 6 adds

Backend:

- A storage provider abstraction (`app/services/storage`): a `StorageProvider`
  interface, a `LocalStorageProvider` for development, an
  `S3CompatibleStorageProvider` for deployment, and a `storage_service` that
  selects the provider from `STORAGE_PROVIDER`.
- Sprint 6 `Document` fields: `storage_provider`, `storage_key`,
  `storage_bucket`, `storage_etag`, `storage_version_id`, `file_available`,
  `last_storage_check_at`, `download_count`, `last_downloaded_at`. The legacy
  `storage_path` is retained for backward compatibility.
- Upload routed through the storage service, storing only safe metadata and a
  generated storage key. The raw filesystem path and object storage credentials
  are never stored on the document or in audit metadata.
- An access-controlled download route, a storage-status route, and a storage
  health route.
- PDF indexing reads the file through the storage layer (local or object
  storage) instead of a local path.
- Storage audit events: `document_upload_started`, `document_stored`,
  `document_storage_failed`, `document_downloaded`, `document_file_unavailable`,
  `pdf_indexing_file_loaded_from_storage`.

Frontend:

- A file storage API client (`lib/api/fileStorage.ts`) and a
  `DocumentDownloadButton`.
- Document list and detail pages showing storage provider, file availability,
  download count, and a download action; indexing is gated on file availability.
- A homepage update describing Sprint 6.

## How this builds on Sprints 1 through 5

Sprint 1 added document upload to a local path. Sprints 2 through 4 indexed and
reviewed those files. Sprint 5 protected the routes with authentication and
access control. Sprint 6 keeps all of that and changes only where the bytes live:
uploads now flow through the storage provider abstraction, downloads are
access-controlled, and PDF indexing reads through the storage layer. Access
control, audit attribution, and the review-support boundary are unchanged.

## Why durable file storage matters before applicant workflows, OCR, or enterprise integrations

An applicant workflow, OCR, or an enterprise integration all assume uploaded
files survive and are retrievable by authorized users. Local-only storage on a
service file system is lost on redeploy, so any feature built on it would be
fragile. Establishing a storage abstraction with object storage support first
means later features read and write through a durable, access-controlled layer.

## What remains demo-only

Brookside Meadows is a seeded public demo. Its seeded documents have no uploaded
file, so they show no storage provider and cannot be downloaded or indexed, which
is the same behavior as before. The default provider is `local`, which is fine
for development and the self-contained demo but is not durable across redeploys
without a mounted volume.

## What remains out of scope

Malware scanning, OCR, live AI calls, DWG parsing, GIS, Bluebeam, applicant
portal workflows, automated engineering calculations, geometry or design
validation, final approval workflows, and enterprise records-retention systems
are out of scope. This sprint is a file-persistence foundation only.

## How local storage and object storage differ

- Local (`STORAGE_PROVIDER=local`): files are written under `LOCAL_STORAGE_DIR`
  using a generated storage key. Simple for development; not durable across
  redeploys without a mounted volume.
- S3-compatible (`STORAGE_PROVIDER=s3`): files are stored in an object storage
  bucket using backend-only credentials. Durable across redeploys. Credentials
  are read only when `STORAGE_PROVIDER=s3` and are never exposed to the frontend.

## How access-controlled file download works

`GET /api/v1/projects/{project_id}/documents/{document_id}/download` requires
project read access (the public demo remains readable when configured). The
backend checks the storage provider for availability, streams the bytes,
increments the download count, updates the last-downloaded timestamp, and writes
a `document_downloaded` audit event. The storage key and any signed URL stay on
the backend; the response never exposes a raw filesystem path.

## How PDF indexing reads files through the storage layer

PDF indexing loads the document's bytes with `storage_service.read_document_bytes`,
which uses the recorded provider and storage key (falling back to a legacy local
path for Sprint 1 documents). It indexes from an in-memory buffer, writes a
`pdf_indexing_file_loaded_from_storage` audit event, and preserves all Sprint 2
behavior: digital text extraction only, no OCR, page records, extraction
statuses, no full text in audit metadata, and a safe failure when the file is
unavailable.

## How to test locally

Backend:

```
cd backend
pip install -r requirements.txt pytest-cov
pytest --cov=app --cov-report=term-missing --cov-fail-under=90
```

The storage tests live in `tests/test_file_storage.py`. The S3 provider is tested
with a mock client and requires no real credentials.

Frontend:

```
npm install
npm run typecheck
npm run lint
npm test
npm run build
```

Manual end-to-end: sign in, create a project, upload a PDF, confirm the document
detail page shows the storage provider and a download action, download the file,
and index the PDF. Confirm another user without access receives 403 on download
and storage status.

See [STORAGE_PROVIDER_ABSTRACTION.md](STORAGE_PROVIDER_ABSTRACTION.md) for the
design, [API_FILE_STORAGE.md](API_FILE_STORAGE.md) for the API contract, and
[RAILWAY_DEPLOYMENT_GUIDE.md](RAILWAY_DEPLOYMENT_GUIDE.md) for deployment
configuration. The recommended next sprint is Production Foundations Sprint 7:
Applicant Response Matrix and Resubmittal Collaboration Workflow.
