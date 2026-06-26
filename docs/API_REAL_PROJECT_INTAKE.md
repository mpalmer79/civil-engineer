# API: Real Project Intake

Routes added or extended in Production Foundations Sprint 1. All paths are under
the `/api/v1` prefix. The frontend reads the backend origin from
`NEXT_PUBLIC_API_BASE_URL` (backend origin only, no `/api/v1` path) and appends
the `/api/v1` paths itself.

Professional boundary: every route is review-support only. No route approves
plans, certifies compliance, verifies CAD, validates design, declares a project
safe, resolves or closes an issue, or makes a final engineering decision. There
is no action named approve. User-provided text is rejected if it contains
final-decision wording.

## Project routes

### GET /api/v1/projects

Lists demo and user-created projects with aggregate counts. Optional query
parameter `source_mode` is one of `all`, `demo_fixture`, or `user_created`.

### POST /api/v1/projects

Creates a real, user-created project record (status `intake_started`,
source_mode `user_created`) and writes a `project_created` audit event.

Request:

```json
{
  "project_name": "Maple Commons Stormwater Review",
  "project_type": "Commercial site plan",
  "jurisdiction": "Town of Riverton",
  "review_type": "Site plan stormwater review",
  "review_domain": "stormwater",
  "location_context": "Infill commercial parcel",
  "acreage": 4.2,
  "disturbed_area": 3.1,
  "proposed_lots": 1,
  "summary": "A small commercial redevelopment with a new detention basin.",
  "applicant_name": "Jane Applicant",
  "design_engineer_name": "Sam Engineer",
  "parcel_ids": ["12-34-567"]
}
```

Response (201): a project detail object including `source_mode`,
`review_round_current`, `created_at`, `document_count`, `finding_count`, and
`audit_event_count`.

### GET /api/v1/projects/{project_id}

Returns expanded project metadata plus document, finding, and audit event
counts. 404 if the project does not exist.

## Document routes

### GET /api/v1/projects/{project_id}/documents

Lists seeded demo documents and real registered or uploaded documents.

### POST /api/v1/projects/{project_id}/documents/register

Registers document metadata (no file bytes). source_mode `user_registered`,
processing_status `metadata_recorded`. Writes a `document_registered` audit
event.

Request:

```json
{
  "original_file_name": "Stormwater Report.pdf",
  "document_type": "stormwater_report",
  "purpose": "Post-construction stormwater narrative",
  "expected_key_information": "Detention basin sizing",
  "revision_label": "Rev A"
}
```

### POST /api/v1/projects/{project_id}/documents/upload

Multipart upload of a document file. source_mode `user_uploaded`,
processing_status `parsing_not_available`. The file is stored under a safe
generated name (never the raw user file name), a sha256 checksum is computed,
and a `document_uploaded` audit event is written. Rejected uploads write a
`document_upload_rejected` event and return 422.

Form fields: `file` (required), `document_type`, `purpose`, `revision_label`,
`uploaded_by_name`. Allowed extensions and the size limit are configured by
`ALLOWED_PROJECT_UPLOAD_EXTENSIONS` and `MAX_PROJECT_UPLOAD_BYTES`.

## Finding routes

### GET /api/v1/projects/{project_id}/findings

Lists seeded demo findings and reviewer-created findings.

### POST /api/v1/projects/{project_id}/findings

Creates a reviewer-owned review-support finding (finding_origin
`reviewer_created`, source_mode `user_created`). Writes a `finding_created`
audit event.

Request:

```json
{
  "title": "Detention basin outlet detail missing",
  "category": "stormwater",
  "risk_level": "high",
  "evidence_status": "missing_evidence",
  "evidence_to_find": "Outlet control structure detail and sizing",
  "reason_it_matters": "Outlet sizing controls the release rate",
  "recommended_human_action": "Reviewer should request the outlet detail",
  "related_documents": ["doc_user_abc123"],
  "reviewer_notes": "Noticed during intake triage"
}
```

`evidence_status` and `human_review_status` are validated; invalid or
final-decision values return 422.

## Evidence reference routes

### GET /api/v1/findings/{finding_id}/evidence-references

Lists basic manual evidence references for a finding.

### POST /api/v1/findings/{finding_id}/evidence-references

Creates a review-support evidence reference linking a finding to a document.
This is a placeholder, not a citation engine. Writes an
`evidence_reference_created` audit event.

```json
{
  "document_id": "doc_user_abc123",
  "reviewer_note": "Sheet C-3 shows the basin outlet area",
  "page_number": 3,
  "sheet_number": "C-3.0",
  "section_label": "Outlet detail"
}
```

## Audit routes

### GET /api/v1/projects/{project_id}/audit-events

Lists chronological audit events for a project. Each event carries actor
attribution (`actor_type`, `actor_display_name`) and non-sensitive
`event_metadata`. Raw IP addresses, raw user agents, and secrets are never
stored.

## Allowed status values

Project status: `intake_started`, `documents_registered`, `reviewer_triage`,
`under_review_support`, `response_draft_ready`, `awaiting_applicant_response`,
`resubmittal_received`, `archived_demo`.

Document processing status: `registered`, `uploaded`, `intake_pending`,
`metadata_recorded`, `parsing_pending`, `parsed_with_warnings`,
`parsing_not_available`, `needs_reviewer_review`.

Finding human review status: `draft`, `needs_reviewer_confirmation`,
`evidence_missing`, `evidence_conflicting`, `evidence_unclear`,
`reviewer_action_needed`, `ready_for_handoff`, `applicant_response_received`,
`carried_forward_for_review`.

Finding evidence status: `potential_issue`, `missing_evidence`,
`conflicting_evidence`, `unclear_evidence`, `needs_reviewer_confirmation`.

Actor type: `demo_seed`, `reviewer`, `system`, `applicant_placeholder`,
`admin_placeholder`.

## Professional-boundary notes

There is intentionally no resolved, closed, approved, failed, passed, verified,
certified, compliant, or safe status. Statuses describe review-support state
only. Document processing statuses never imply document approval.
