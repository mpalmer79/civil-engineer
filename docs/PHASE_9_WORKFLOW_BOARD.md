# Phase 9: Reviewer Workflow Board and Issue Resolution Tracking Report

Phase 9 adds a reviewer-facing workflow board. It promotes the review packet
items that require human review into an operational board where a reviewer can
triage each item, request follow-up or more information, record reviewer notes,
mark items reviewer checked or excluded, and mark items ready for handoff to a
licensed Professional Engineer.

Civil Engineer AI remains a review-support and evidence-organization system. The
board organizes review-support work for a human reviewer. It does not approve
plans, certify compliance, stamp drawings, verify CAD, validate the design, or
make final engineering decisions. There is no action called approve, and ready
for handoff means handing organized evidence to a human reviewer, not issuing a
decision.

## What Phase 9 adds

- Three models: WorkflowItem, WorkflowAction, and WorkflowFollowUpRequest.
- A board generation service that promotes review packet items into workflow
  items.
- Status transitions, reviewer notes, and follow-up requests on workflow items.
- A board summary and a ready-for-handoff summary.
- API endpoints, audit events, and backend tests.
- A Workflow Board page and item detail page in the frontend, with a board
  summary card, status columns, an item detail panel, an action panel, an item
  history panel, a ready-for-handoff panel, and a professional limitations
  notice.

## How the board is generated

`generate_workflow_items_from_review_packet(project_id)` reads the most recent
review packet for the project, assembles its detail through
`assemble_packet_detail`, and promotes each packet item that requires human
review into a workflow item. Informational summary, traceability, and
limitations items do not require human review, so they are not promoted. If no
packet exists yet, a packet is generated first so the board has source items.

The operation is idempotent: existing workflow items, actions, and follow-up
requests for the project are removed and a fresh board is built from the current
packet. The Brookside Meadows fixture produces a board of review-support items
split across reviewer roles.

Each workflow item records its title, description, source type, source id, and
severity from the packet item, plus the packet section type, the distinct
evidence types drawn from the packet item evidence links, and an assigned
reviewer role derived from the section type. Items start at status `draft`.

The board is built from seeded review-support data. It is not generated from
parsed PDF, DWG, DXF, or Autodesk files, and it does not produce final
engineering decisions, approvals, certifications, stamped reviews, verified CAD
outputs, or validated designs.

## Statuses and actions

Workflow board statuses are limited to: `draft`, `needs_triage`,
`needs_follow_up`, `needs_more_information`, `reviewer_checked`,
`excluded_from_packet`, and `ready_for_handoff`. `draft` is the seeded initial
status and is not a manual transition target; requesting it is rejected.

Each manual status transition records a workflow action. The action types are
`triage_started`, `follow_up_requested`, `more_information_requested`,
`reviewer_checked`, `excluded_from_packet`, `ready_for_handoff`, `note_added`,
and `target_date_updated`. Follow-up request statuses are `open`,
`response_needed`, `reviewer_checked`, and `closed_without_decision`.

There is no action called approve, and no status or action uses approval,
certification, verification, compliance, safety, or design-validation language.
Reviewer notes and follow-up text are checked for prohibited final-decision
wording and rejected if it appears.

## Follow-up requests

A reviewer can open a follow-up request against a workflow item, recording who
the request is from, the reason, the information requested, and an optional
target date. Opening a follow-up request moves the item to `needs_follow_up`,
records a `follow_up_requested` action, and starts the request at `open`.
Closing a request without a decision is an explicit allowed state, so the board
never forces a final determination.

## Board and handoff summaries

`get_workflow_board_summary(project_id)` returns counts by status, severity,
section type, and assigned role, plus the open follow-up count and the
ready-for-handoff count. `get_ready_for_handoff_summary(project_id)` returns the
items a reviewer has marked ready for handoff and the count of outstanding
follow-up requests, with a note that handoff is to a human reviewer and is not a
decision.

## Audit events

Phase 9 writes audit events when:

- a workflow board is generated (`workflow_board_generated`)
- a workflow item is viewed (`workflow_item_viewed`)
- a workflow item status changes (`workflow_item_status_updated`)
- a reviewer note is added (`workflow_note_added`)
- a follow-up request is opened (`workflow_follow_up_requested`)
- an item history is requested (`workflow_item_history_requested`)
- a board summary is requested (`workflow_board_summary_requested`)
- a ready-for-handoff summary is requested (`workflow_ready_for_handoff_requested`)

Intentional read side effects: the GET endpoints for the item detail, the item
history, the board summary, and the ready-for-handoff summary each write an
audit event recording the access. This is intentional so the decision history
shows reviewer activity. The list, actions, and follow-ups list endpoints do
not write audit events.

## API endpoints

- `POST /api/v1/projects/{project_id}/workflow-board/generate`
- `GET /api/v1/projects/{project_id}/workflow-board` (optional `?status=`,
  `?severity=`, `?section_type=`, `?assigned_role=`, `?source_type=`)
- `GET /api/v1/projects/{project_id}/workflow-board/summary`
- `GET /api/v1/projects/{project_id}/workflow-board/ready-for-handoff`
- `GET /api/v1/workflow-items/{workflow_item_id}`
- `GET /api/v1/workflow-items/{workflow_item_id}/history`
- `GET /api/v1/workflow-items/{workflow_item_id}/actions`
- `GET /api/v1/workflow-items/{workflow_item_id}/follow-ups`
- `PATCH /api/v1/workflow-items/{workflow_item_id}/status`
- `POST /api/v1/workflow-items/{workflow_item_id}/notes`
- `POST /api/v1/workflow-items/{workflow_item_id}/follow-ups`

At startup the backend generates the workflow board for the Brookside Meadows
project if none exists, so the read endpoints and frontend have data without a
manual generate call. The generate endpoint can be called again to rebuild the
board from the latest packet.

## What remains out of scope

Phase 9 does not add real PDF parsing, DWG parsing, DXF parsing, Autodesk
integration, GIS integration, OCR, computer vision, vector search,
authentication, deployment setup, external paid APIs, or final engineering
decision logic. The board is built from seeded review-support data.

## What a later phase could build next

A later phase could add assignment to named reviewers, due-date reminders, and
board filtering presets, and could begin reading real CAD-derived metadata. Real
CAD-derived metadata extraction remains a separate, later track described in
`CAD_INTEGRATION_ROADMAP.md`.
