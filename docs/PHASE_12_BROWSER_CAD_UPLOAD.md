# Phase 12: Browser CAD Upload and Parse Review Queue Report

> Historical record. This document describes a completed build phase and is
> not current implementation guidance. See docs/README.md for the current
> documentation index.

Phase 12 makes the Phase 11 DXF parsing feature usable from the browser. A
reviewer can upload a real DXF file, see validation results, request a parse,
inspect parse status and parse failures, view a CAD intake dashboard and parse
queue, review unpromoted CAD findings, and promote selected CAD findings into
the Workflow Board.

Civil Engineer AI remains a review-support and evidence-organization system.
Uploading and parsing a DXF file extracts metadata and references only. It does
not verify CAD, validate geometry, hydraulic calculations, grading, stormwater
design, or legal boundaries, certify compliance, approve plans, or replace a
licensed Professional Engineer. There is no action called approve.

## Supported file type

- Supported: DXF only.
- Rejected or out of scope: DWG parsing, Autodesk and Civil 3D integration, PDF
  plan parsing, OCR, GIS, computer vision, design validation, quantity
  certification, automated engineering decisions, email sending, authentication,
  and deployment. DWG support remains future work because it usually requires
  proprietary or heavier tooling.

## Upload size limit

The documented upload size limit is configured by `CAD_MAX_UPLOAD_BYTES` and
defaults to 5,000,000 bytes (5 MB). The limit is returned by the
`GET /api/v1/cad-upload-limits` endpoint and shown in the browser before upload.

## Intake validation

`validate_cad_upload_file(...)` runs these review-support intake checks and
returns one of the allowed validation statuses (`accepted`, `rejected`, or
`needs_human_review`) with a clear message:

- The file extension is `.dxf`. Any other extension is rejected.
- The file size is greater than zero. An empty file is rejected.
- The file size is under the configured maximum. An oversized file is rejected.
- The content type, when the browser provides one, is a known DXF or generic
  binary or text type. A clearly wrong type (for example `application/pdf`) is
  rejected. DXF files are sent with a wide range of content types, so the
  extension and the DXF readability check are authoritative.
- The file content looks like a readable DXF text file (it contains the expected
  DXF section markers). A file that does not is stored but marked
  `needs_human_review` for a reviewer to confirm.

These statuses describe intake validation only. They never record an engineering
decision about the plan.

## Storage safety and path traversal protection

`save_uploaded_dxf_file(...)` writes uploaded bytes to disk under a safe
generated file name (`cad_<random>.dxf`) inside a per-project directory under the
configured `CAD_UPLOAD_DIR` (default `./cad_uploads`, ignored by git). The stored
file name is never derived from the user file name, and the original user file
name is reduced to its base name and kept as `original_file_name` metadata only.
Any directory components in the user file name (for example a `../../etc/passwd`
path traversal attempt) are dropped before anything touches the storage path, so
a malicious file name cannot influence where the file is written.

## Rejected file behavior

A rejected upload is not stored and no CAD file record is created. The endpoint
returns HTTP 422 with the validation message, and a `cad_upload_rejected` audit
event records the attempt. An accepted or `needs_human_review` upload is stored,
registered as a CAD file with `upload_source` `browser_upload`, and returns the
file metadata plus the next action (`request_parse`).

## Parse queue and parse status

Parsing is triggered manually with
`POST /api/v1/cad-files/{cad_file_id}/request-parse`. There is no background
worker, no Redis, and no Celery. The request records `parse_requested_at`, runs
the Phase 11 parser inline, and records `parse_completed_at`.

`get_cad_parse_queue(project_id)` returns one row per uploaded CAD file with a
derived queue status from the allowed set: `queued`, `parsing`, `completed`,
`completed_with_warnings`, `failed`, or `needs_human_review`. A file with no
parse run is `queued` (or `needs_human_review` if validation flagged it); a file
whose latest run is in progress is `parsing`; otherwise the row reflects the
parse run status.

`get_cad_intake_dashboard(project_id)` summarizes file counts, files needing
parse, files with parse failures, parse runs needing human review, total CAD
findings, and unpromoted versus promoted findings, with queue, validation, and
parse status breakdowns.

## Parse failure means a technical parse failure

A parse queue or parse run status of `failed` means the parser could not read the
DXF file (for example a malformed or truncated file). It is a technical parse
failure, not an engineering failure and not a final decision about whether the
design is sound. The CAD intake dashboard, parse queue, and the parse failure
panel all use this technical wording.

## Promoting CAD findings to the workflow

`promote_cad_finding_to_workflow(...)` promotes a single CAD review finding into
a Workflow Board item, and `promote_selected_cad_findings_to_workflow(...)`
promotes a selected batch. Both are idempotent per finding: a finding already
linked to a workflow item (`promoted_to_workflow` is true) is skipped, so the
same CAD finding never creates a duplicate workflow item. The browser also hides
already promoted findings from the unpromoted list. Promotion creates
review-support workflow items under human review; it does not approve, certify,
verify, or validate anything.

## Models

Phase 12 reuses the Phase 11 models and adds fields rather than new tables:

- `CadFileUpload`: `original_file_name`, `stored_file_name`, `content_type`,
  `upload_source`, `validation_status`, `validation_message`,
  `max_file_size_bytes`, `parse_requested_at`, `parse_completed_at`.
- `CadReviewFinding`: `promoted_to_workflow`, `promoted_workflow_item_id`.

All new fields are nullable or defaulted so Phase 11 sample-based intake and
existing rows keep working without a migration.

## Allowed statuses

- Validation statuses: `accepted`, `rejected`, `needs_human_review`.
- Queue statuses: `queued`, `parsing`, `completed`, `completed_with_warnings`,
  `failed`, `needs_human_review`. `failed` is allowed only for a technical parse
  failure, not an engineering failure.

No final-decision vocabulary (`approved`, `certified`, `verified`, `passed`,
`compliant`, `noncompliant`, `safe`, `unsafe`, `design validated`) appears in any
validation status, queue status, generated finding, dashboard label, or workflow
promotion output. A backend test asserts this.

## Audit events

Phase 12 writes audit events when a DXF upload is accepted
(`cad_upload_accepted`), a DXF upload is rejected (`cad_upload_rejected`), a parse
is requested (`cad_parse_requested`), the parse queue is viewed
(`cad_parse_queue_viewed`), the CAD intake dashboard is viewed
(`cad_intake_dashboard_viewed`), unpromoted CAD findings are viewed
(`cad_unpromoted_findings_viewed`), a CAD finding is promoted
(`cad_finding_promoted`), and selected CAD findings are promoted
(`cad_findings_promoted_selected`).

Intentional read side effects: the GET endpoints for the parse queue, the CAD
intake dashboard, and the unpromoted findings list each write an audit event
recording the access, in addition to the Phase 11 read side effects on the parse
summary, layers, text, and review context endpoints. This is intentional so the
decision history shows reviewer access.

## API endpoints

- `GET /api/v1/cad-upload-limits`
- `POST /api/v1/projects/{project_id}/cad-files/upload`
- `GET /api/v1/projects/{project_id}/cad-intake/dashboard`
- `GET /api/v1/projects/{project_id}/cad-parse-queue`
- `POST /api/v1/cad-files/{cad_file_id}/request-parse`
- `GET /api/v1/projects/{project_id}/cad-review-findings/unpromoted`
- `POST /api/v1/cad-review-findings/{cad_review_finding_id}/promote-to-workflow`
- `POST /api/v1/projects/{project_id}/cad-review-findings/promote-selected`

All Phase 11 CAD intake endpoints remain available and unchanged.

## Frontend

The CAD Intake page adds an upload limits notice, an upload panel with an upload
validation notice, the CAD intake dashboard, a parse failure panel, the parse
queue, an unpromoted CAD findings panel with per-finding and batch promotion, and
a promotion panel for reviewer name and note. The Phase 11 per-file detail (parse
summary, layers, text, blocks, reference candidates, plan sheet comparison, and
findings) remains below. All data is backend-canonical; the browser does not
simulate uploaded CAD files or parsed results.

## Dependency

Phase 12 adds `python-multipart` to `backend/requirements.txt` so FastAPI can
accept the multipart file upload. No paid SDK, Autodesk API, or proprietary
integration is used.

## What remains out of scope

Phase 12 does not add DWG parsing, Autodesk or Civil 3D integration, PDF plan
parsing, OCR, GIS, computer vision, vector search, authentication, deployment
setup, email sending, external paid APIs, design validation, or automated
engineering decisions. DWG support and broader CAD extraction remain a separate,
later track described in `CAD_INTEGRATION_ROADMAP.md`.
