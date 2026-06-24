# Phase 10: External Review Response Package Report

Phase 10 adds an external review response package. It turns the Phase 9
ready-for-handoff workflow items into a structured draft external response a
human reviewer can prepare for an applicant, design engineer, municipal
reviewer, or internal review team.

Civil Engineer AI remains a review-support and evidence-organization system. The
response package supports drafting external communication. It does not send
email or official correspondence, approve plans, certify compliance, stamp
drawings, verify CAD, validate the design, or make final engineering decisions.
There is no action called approve, and every item stays under human review.

## Real-world workflow

Phase 10 completes a practical review desk loop:

1. Review packet: assemble the evidence into a structured packet draft.
2. Workflow board: triage items, request follow-up, and mark items ready for
   handoff.
3. Response package: turn the ready-for-handoff items into a draft external
   response, grouped by topic, with draft wording and an attachment checklist.
4. Human review: a licensed Professional Engineer or authorized reviewer reviews
   and issues any response outside the system.

The system never issues the response itself.

## What Phase 10 adds

- Six models: ResponsePackage, ResponsePackageSection, ResponsePackageItem,
  ResponsePackageEvidenceLink, ResponsePackageAttachment, and
  ResponsePackageAction.
- A generation service that promotes workflow items, groups them by topic, and
  drafts plain external-review wording.
- Response item draft text editing, item status management, and package status
  management.
- An attachment checklist, a printable draft response, a package history, and a
  human review sign-off checklist.
- API endpoints, audit events, and backend tests.
- A Response Package page and detail page in the frontend with a builder,
  summary card, section list, item panel, draft editor, evidence panel,
  attachment checklist, printable preview, history timeline, sign-off checklist,
  and an external communication boundary notice.

## How the package is generated

`generate_response_package(project_id)` reads the workflow board and selects the
source items using these tiers:

1. Items with status `ready_for_handoff` (the primary source).
2. If none are ready, items with status `needs_follow_up` or
   `needs_more_information`, and the package summary is labeled draft.
3. If none of those exist either, any item that still requires human review and
   is not excluded, a defensive fallback so the draft is not empty.

Informational limitations items are never promoted as response demands. Items
are grouped into topical sections using source type, section type, severity, and
keywords. Each response item keeps traceability to its workflow item, packet
item, and source evidence links.

Generation is idempotent for the current project unless the existing package
status is `archived`, in which case generation is paused until the package is
reset. At startup the backend generates one package for Brookside Meadows if
none exists, so the read endpoints and frontend have data without a manual
generate call.

The package is built from seeded review-support data. It is not generated from
parsed PDF, DWG, DXF, or Autodesk files, and it does not produce final
engineering decisions, approvals, certifications, stamped reviews, verified CAD
outputs, or validated designs.

## Sections

`opening_summary`, `attachments`, and `limitations_and_review_boundary` are
always present and informational. The topical demand sections appear when at
least one item maps to them: `requested_revisions`, `missing_information`,
`plan_sheet_items`, `stormwater_items`, `erosion_control_items`, and
`wetland_buffer_items`.

## Draft response language

Draft text uses practical external-review wording, for example "Please provide
additional information regarding...", "Please clarify the plan reference
for...", and "The following item should be reviewed by the design
professional...". It avoids final-decision language. The service and the draft
text edit endpoint reject prohibited wording such as approved, certified,
verified, compliant, or safe.

## Statuses and actions

Response package statuses: `draft`, `needs_revision`, `reviewer_checked`,
`ready_for_handoff`, `archived`. Response item statuses: `draft`, `included`,
`excluded`, `needs_revision`, `reviewer_checked`. `draft` is the seeded initial
status for packages and items and is not a manual transition target.

Response action types: `package_generated`, `item_included`, `item_excluded`,
`item_revised`, `reviewer_checked`, `note_added`,
`package_marked_ready_for_handoff`, and `package_archived`. There is no action
called approve, and no status or action uses approval, certification,
verification, compliance, safety, or design-validation language.

## Attachment checklist and sign-off checklist

The attachment checklist suggests enclosures for the reviewer to confirm: a
printable draft review-support summary plus the source documents referenced by
the selected items. The human review sign-off checklist confirms that human
review is still required, that the draft wording was reviewed, that evidence
traceability was checked, that no final-decision language is present, and that
the system did not send the response.

## Printable draft response

`get_response_package_print_view(response_package_id)` returns the package, its
sections and items, the draft intro and closing, the attachment checklist, the
sign-off checklist, an external communication boundary statement, and a draft
notice. The frontend renders it as a printable draft letter or memo, clearly
labeled draft external communication support.

## Audit events

Phase 10 writes audit events when:

- a response package is generated (`response_package_generated`)
- a response package is viewed (`response_package_viewed`)
- a print view is requested (`response_package_print_view_requested`)
- attachments are viewed (`response_package_attachments_viewed`)
- history is viewed (`response_package_history_requested`)
- a package status changes (`response_package_status_updated`)
- an item status changes (`response_item_status_updated`)
- item draft text changes (`response_item_draft_text_updated`)
- a note is added (`response_package_note_added`)

Intentional read side effects: the GET endpoints for the package detail, the
print view, the attachment checklist, and the history each write an audit event
recording the access. This is intentional so the decision history shows reviewer
access. The list and summary endpoints do not write audit events.

## API endpoints

- `POST /api/v1/projects/{project_id}/response-packages/generate`
- `GET /api/v1/projects/{project_id}/response-packages`
- `GET /api/v1/response-packages/{response_package_id}`
- `GET /api/v1/response-packages/{response_package_id}/print-view`
- `GET /api/v1/response-packages/{response_package_id}/attachments`
- `GET /api/v1/response-packages/{response_package_id}/history`
- `GET /api/v1/response-packages/{response_package_id}/summary`
- `PATCH /api/v1/response-packages/{response_package_id}/status`
- `PATCH /api/v1/response-packages/{response_package_id}/items/{response_item_id}/status`
- `PATCH /api/v1/response-packages/{response_package_id}/items/{response_item_id}/draft-text`
- `POST /api/v1/response-packages/{response_package_id}/items/{response_item_id}/notes`

## What remains out of scope

Phase 10 does not add real PDF parsing, DWG parsing, DXF parsing, Autodesk
integration, GIS integration, OCR, computer vision, vector search,
authentication, deployment setup, email sending, external paid APIs, or final
engineering decision logic. The package is built from seeded review-support data
and is never sent by the system.

## What a later phase could build next

A later phase could let a reviewer choose the audience and a subset of items,
export the printable draft to a file, and track response revisions over time.
Real CAD-derived metadata extraction remains a separate, later track described
in `CAD_INTEGRATION_ROADMAP.md`.
