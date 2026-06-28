# Project Traceability and Reviewer Handoff (Phase 4A / 4B)

This document describes the project-wide traceability surface, inline review
packet context, reviewer confirmation of links, handoff readiness signals, and
the known limitations of each. It is review-support only. Nothing here approves a
plan, certifies compliance, verifies CAD, validates a design, or determines that
a requirement is satisfied.

## Project-wide traceability

`GET /projects/{project_id}/traceability` aggregates relationships that already
exist between project checklist items, evidence links, citations, candidates,
documents and pages, findings, workflow items, and review packets. It is
read-only: it organizes existing links, runs no analysis engine, calls no AI
provider, and mutates nothing.

The aggregation centers on project checklist items. It emits one row per linked
evidence record (checklist evidence link, then citation, then candidate), or a
single `no_linked_evidence_yet` row when an item has no linked evidence. Four
states are kept distinct so an unlinked item is never conflated with an unreviewed
item or with a project that has no indexed pages:

- `no_linked_evidence_yet`: the item has no linked evidence, citation, or
  candidate. This is not a statement that the requirement is unsupported.
- `not_enough_indexed_information`: no linked evidence and the project has no
  indexed, searchable document pages yet.
- `not_reviewed`: linked evidence exists but the reviewer has not confirmed it.
- `linked_evidence_exists`: evidence is linked, still review-support only.

### Distinction between linked evidence and requirement satisfaction

A linked evidence row means a reviewer (or an earlier workflow step) associated a
document page, citation, or candidate with a checklist requirement. It does not
mean the requirement is satisfied, approved, certified, verified, validated, or
compliant. Every row requires reviewer confirmation. The `limitations_note` on
the response states this in plain language.

## Inline packet context

Each traceability row carries inline review packet context when the row's
checklist item or finding is included in a review packet. Packet context is read
from existing review packet items and their evidence links only. Each context
records `review_packet_id`, `review_packet_title`, `review_packet_item_id`,
section id and title, `packet_item_status`, `packet_item_source`,
`packet_traceability_relationship`, and a `packet_source_link`.

The list is bounded (at most three contexts per row) and `packet_context_count`
always reports the full count. A row that is not in any packet shows
`packet_context_count` of zero, surfaced in the UI as "not included in a packet
yet". The packet's own requirement-to-evidence traceability tab remains available
from the review packets page.

## Reviewer confirmation of links

Traceability rows are computed and have no stable stored primary key, so a
reviewer review action is keyed by a stable `traceability_row_key`: a
deterministic hash of the row's existing entity IDs (checklist item, evidence
citation or candidate, finding, relationship type, and relationship source). The
key deliberately excludes the positional row id and the regenerated workflow and
packet item ids, so a recorded action stays attached to the same checklist
requirement plus evidence linkage even after a review packet is regenerated.

- `POST /projects/{project_id}/traceability/{traceability_row_key}/review-actions`
  records one review action.
- `GET /projects/{project_id}/traceability/{traceability_row_key}/review-actions`
  returns the row's review action history.

Allowed action types are review-support only and avoid final-decision language:

- `needs_review`
- `reviewer_confirmed_link` (the reviewer confirmed the link is useful for review
  only; it does not mean the requirement is satisfied)
- `needs_more_information`
- `not_applicable`
- `link_rejected` (discards the link for review without deleting any source data)
- `follow_up_needed`

A reviewer note is optional and is rejected if it contains prohibited
final-decision wording.

### Data model and migration note

Review actions are stored in a small, append-only `traceability_review_actions`
table. Recording an action writes one action row and one `AuditEvent`; it never
mutates the checklist item, evidence, finding, workflow item, or packet the row
references. A `link_rejected` action therefore discards the link for review
without deleting source records.

The backend creates tables with `Base.metadata.create_all` and has no migration
framework. The new table is created automatically on startup in this local
prototype. A production deployment would need a managed migration to add the
table to an existing database.

## Handoff readiness signals

The traceability response includes a read-only `handoff_readiness` block. It is a
readiness checklist, not a final decision, and no count means a requirement is
satisfied, approved, or compliant:

- `total_traceability_rows`
- `rows_with_linked_evidence`
- `rows_without_linked_evidence`
- `rows_with_reviewer_action`
- `rows_needing_more_information`
- `rows_follow_up_needed`
- `rows_not_in_packet`
- `packet_context_count`
- `ready_for_reviewer_handoff_count` (rows whose latest action is
  `reviewer_confirmed_link` or `not_applicable`)

The traceability page shows these as a handoff readiness panel with links to
review packets, the workflow board for follow-up items, and evidence search for
rows without linked evidence.

## Review packet handoff view

The review packet print view (`GET /review-packets/{packet_id}/print-view`)
includes `traceability_review_rows` for the rows included in that packet, each
with its latest reviewer review action or `requires_reviewer_confirmation` when no
action exists. The draft notice and professional limitations remain visible, and
a missing traceability action never blocks the print view. The print preview is a
draft reviewer handoff package, not a final or certified output.

## Known limitations

- Traceability reflects only links that already exist. A missing link is a
  workflow state, not a final finding about the project.
- Packet context and the packet handoff view depend on review packets having been
  generated; a project with no packet shows every row as not in a packet yet.
- The stable row key is derived from entity IDs; deleting and recreating a
  checklist item or citation produces a new key, so a prior review action would
  not carry forward to the recreated record.
- There is no production migration tooling. The append-only review action table is
  created with `create_all` in this prototype.
