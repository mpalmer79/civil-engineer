# Phase 8: Review Packet Builder and Evidence Traceability Report

Phase 8 adds a reviewer-facing Review Packet Builder. It assembles documents,
checklist items, findings, plan sheets, CAD-aware metadata, sheet hotspots, plan
consistency findings, human review actions, and audit evidence into a structured
review-support packet draft, with an evidence traceability matrix and a printable
review-support summary.

Civil Engineer AI remains a review-support and evidence-organization system. The
packet organizes evidence for a human reviewer. It does not approve plans,
certify compliance, stamp drawings, verify CAD, validate the design, or make
final engineering decisions. There is no action called approve.

## What Phase 8 adds

- Five models: ReviewPacket, ReviewPacketSection, ReviewPacketItem,
  ReviewPacketEvidenceLink, and ReviewPacketReviewerAction.
- A packet generation service that builds a packet draft from seeded data from
  prior phases.
- An evidence traceability matrix and a printable review-support view.
- Reviewer actions and item status updates on packet items.
- API endpoints, audit events, and backend tests.
- A Review Packet page and detail page in the frontend, with builder, summary,
  section list, item panel, action panel, traceability matrix, print preview,
  and a professional limitations notice.

## How the packet is generated

`generate_review_packet(project_id)` reads the existing seeded data through the
prior-phase services and assembles it into a packet with eight sections. The
operation is idempotent: existing packets for the project are removed and a fresh
packet is built from the current data. The Brookside Meadows fixture produces a
packet with eight sections and dozens of items, each linked back to its source
evidence.

The packet is built from seeded review-support data. It is not generated from
parsed PDF, DWG, DXF, or Autodesk files, and it does not produce final
engineering decisions, approvals, certifications, stamped reviews, verified CAD
outputs, or validated designs.

## Packet sections

1. Executive review-support summary
2. Document and checklist findings (items from findings and from documents with
   gaps)
3. Plan sheet and CAD-aware references (items from plan sheets needing attention
   and inconsistent plan references)
4. Sheet hotspot observations (items from seeded sheet hotspots)
5. Plan consistency findings (items from plan consistency findings)
6. Human review actions (items from recorded plan consistency review actions, or
   a note when none exist yet)
7. Evidence traceability matrix (overview pointing to the traceability view)
8. Professional limitations and review boundary

## Packet items and evidence links

Each item records its item type, title, description, severity, source type, and
source id, and starts with reviewer status `draft`. Items connect back to
existing entities through evidence links: documents, checklist items, findings,
plan sheets, CAD-aware metadata, plan references, plan consistency findings,
sheet hotspots, plan consistency review actions, and the project. Each evidence
link records an evidence type, evidence id, relationship, and label.

## Statuses and actions

Packet, section, item, and action statuses are limited to: `draft`,
`needs_follow_up`, `reviewer_checked`, `excluded_from_packet`, and
`needs_more_information`. The reviewer actions are `needs_follow_up`,
`reviewer_checked`, `excluded_from_packet`, and `needs_more_information`, each
mapping to a status of the same name. There is no action called approve, and no
status or action uses approval, certification, verification, compliance, safety,
or design-validation language.

## Evidence traceability matrix

`get_review_packet_traceability(packet_id)` returns one row per evidence link.
Each row includes the section type, item id, item title, item type, source type,
source id, evidence type, evidence id, relationship, and label, so a reviewer can
trace every packet item back to the evidence it was built from. This is
review-support traceability, not a verification or certification of the evidence.

## Printable review-support summary

`get_review_packet_print_view(packet_id)` returns the packet, its sections and
items, a professional limitations statement, and a draft notice. The frontend
renders it as a printable summary. It is clearly labeled draft review-support
material.

## Audit events

Phase 8 writes audit events when:

- a review packet is generated (`review_packet_generated`)
- a review packet is viewed (`review_packet_viewed`)
- a traceability matrix is requested (`review_packet_traceability_requested`)
- a print view is requested (`review_packet_print_view_requested`)
- a packet item receives a reviewer action (`review_packet_item_action_recorded`)
- a packet item status changes (`review_packet_item_status_updated`)

Intentional read side effects: the GET endpoints for the packet detail, the
traceability matrix, and the print view each write an audit event recording the
access. This is intentional so the decision history shows reviewer access to the
packet. The list and summary endpoints do not write audit events.

## API endpoints

- `POST /api/v1/projects/{project_id}/review-packets/generate`
- `GET /api/v1/projects/{project_id}/review-packets`
- `GET /api/v1/review-packets/{packet_id}`
- `GET /api/v1/review-packets/{packet_id}/traceability`
- `GET /api/v1/review-packets/{packet_id}/print-view`
- `GET /api/v1/review-packets/{packet_id}/summary`
- `POST /api/v1/review-packets/{packet_id}/items/{item_id}/review-actions`
- `PATCH /api/v1/review-packets/{packet_id}/items/{item_id}/status`

At startup the backend generates one packet for the Brookside Meadows project if
none exists, so the read endpoints and frontend have data without a manual
generate call. The generate endpoint can be called again to rebuild the draft.

## What remains out of scope

Phase 8 does not add real PDF parsing, DWG parsing, DXF parsing, Autodesk
integration, GIS integration, OCR, computer vision, vector search,
authentication, deployment setup, external paid APIs, or final engineering
decision logic. The packet is a draft assembled from seeded review-support data.

## What a later phase could build next

A later phase could let a reviewer compose a packet from a chosen subset of
findings, export the printable summary to a file, and track packet revisions over
time. Real CAD-derived metadata extraction remains a separate, later track
described in `CAD_INTEGRATION_ROADMAP.md`.
