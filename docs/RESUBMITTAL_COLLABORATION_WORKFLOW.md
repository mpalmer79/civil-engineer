# Resubmittal Collaboration Workflow

The resubmittal collaboration workflow records applicant resubmittals across
review rounds and connects them to the applicant response matrix. It is part of
Production Foundations Sprint 7.

Registering a resubmittal round records an applicant submission for reviewer
review. It does not decide whether the resubmittal satisfies engineering
requirements, and it does not resolve or close anything. Every round needs human
review.

## Data model

`ResubmittalRound`

- Identity: `resubmittal_round_id`, `project_id`, `response_matrix_id`,
  `round_number`, `round_label`.
- Submission metadata: `received_at`, `submitted_by_name`,
  `submitted_by_organization`, `summary`.
- Workflow: `status`, `document_ids`, `carried_forward_item_ids`.
- Provenance and attribution: `source_mode`, `organization_id`,
  `created_by_user_id`, `created_by_name`.

`status` is drawn from a review-support set: `round_registered`,
`documents_received`, `indexing_needed`, `evidence_review_needed`,
`response_review_in_progress`, `ready_for_reviewer_handoff`, `archived_demo`.

## Reviewer workflow

1. Register a resubmittal round when the applicant submits revised material. The
   round number defaults to the next round, and the project review round counter
   advances.
2. Link the documents received with the round. Linking a document moves the round
   to `documents_received`.
3. Carry forward the response matrix items that still need review into the round.
4. Review the round summary, which counts the connected matrix items by applicant
   response status and carry-forward status.

## How rounds connect to the response matrix

A resubmittal round can reference a response matrix. Carrying matrix items into a
round records which review-support items are being tracked in that round. The
round summary reads the connected matrix items and reports review-support status
counts so the reviewer can see what still needs confirmation. None of these
counts is an engineering determination.

## What the workflow never does

It never marks a round or an item approved, certified, compliant, verified,
validated, resolved, or closed. It never exposes a raw storage path, a storage
key, a signed URL, or any credential in a response or in audit metadata. Document
links record only the document id and a review-support link type and note.

## Access control

All resubmittal reads require project read access. All resubmittal mutations
require project reviewer access. A read-only user receives 403 on any mutation.
The seeded public demo remains readable when configured.

See [APPLICANT_RESPONSE_MATRIX.md](APPLICANT_RESPONSE_MATRIX.md) for the matrix
model and [API_RESPONSE_MATRIX_AND_RESUBMITTALS.md](API_RESPONSE_MATRIX_AND_RESUBMITTALS.md)
for the endpoints.
