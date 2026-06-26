# Applicant Response Matrix

The applicant response matrix is a reviewer-controlled structure for organizing
review-support items, recording applicant responses for reviewer review, and
tracking each item across resubmittal rounds. It is part of Production
Foundations Sprint 7.

An applicant response recorded here is a reviewer-entered record of what the
applicant submitted. It is kept for reviewer review. It is not proof that a
concern is satisfied, not a compliance determination, and not a final outcome.
Carry-forward keeps an item under review across rounds; it does not resolve or
close it.

## Data model

`ResponseMatrix`

- `response_matrix_id`, `project_id`, `name`, `current_round_number`, `status`,
  `source_mode`, `organization_id`, `created_by_user_id`, `created_by_name`.
- `status` is drawn from a review-support set: `matrix_started`,
  `matrix_in_progress`, `awaiting_applicant_response`,
  `applicant_response_received`, `needs_reviewer_follow_up`,
  `ready_for_reviewer_handoff`, `archived_demo`.

`ResponseMatrixItem`

- Identity and linkage: `response_matrix_item_id`, `response_matrix_id`,
  `project_id`, `source_finding_id`, `source_checklist_item_id`,
  `source_citation_id`, `item_number`, `category`.
- Reviewer content: `reviewer_comment_draft`, `requested_evidence`,
  `reviewer_note`.
- Applicant response: `applicant_response_text`, `applicant_response_status`.
- Reviewer workflow: `reviewer_follow_up_status`, `carry_forward_status`,
  `current_round_number`, `carried_from_round_number`,
  `carried_to_round_number`.
- Related references: `related_document_ids`, `related_citation_ids`.
- Attribution: `created_by_user_id`, `created_by_name`, `updated_by_user_id`,
  `updated_by_name`, `sort_order`.

`MatrixItemDocumentLink`

- `matrix_item_document_link_id`, `project_id`, `response_matrix_item_id`,
  `document_id`, `resubmittal_round_id`, `link_type`, `reviewer_note`,
  attribution fields. `link_type` is drawn from a review-support set:
  `applicant_response_document`, `revised_plan_reference`,
  `revised_report_reference`, `supporting_response_evidence`,
  `reviewer_reference`.

## Status vocabularies

These are review-support workflow labels, not engineering determinations.

- Applicant response status: `response_not_requested`,
  `awaiting_applicant_response`, `applicant_response_received`,
  `applicant_response_incomplete`, `response_needs_reviewer_review`,
  `response_recorded_for_review`.
- Reviewer follow-up status: `not_reviewed`, `needs_reviewer_confirmation`,
  `needs_applicant_follow_up`, `evidence_updated`, `reviewer_note_added`,
  `ready_for_reviewer_handoff`.
- Carry-forward status: `not_carried_forward`, `carried_forward_for_review`,
  `carried_forward_with_updated_evidence`,
  `carried_forward_needs_applicant_response`.

## Reviewer workflow

1. Create a response matrix for a project.
2. Add a reviewer finding or a checklist review item to the matrix. A new item
   starts at `awaiting_applicant_response` and `not_reviewed`.
3. When the applicant responds, record the response text. The item moves to
   `applicant_response_received`, and a `not_reviewed` follow-up status is moved
   to `needs_reviewer_confirmation` so the item is queued for reviewer review.
4. Update the reviewer follow-up status as the reviewer checks the response.
5. Carry the item forward when it still needs review in the next round. The
   target round is the current round number plus one.

## What the matrix never does

It never marks an item approved, certified, compliant, verified, validated,
resolved, or closed. It never stores the full applicant response text in audit
metadata; it records only a response length. It never exposes a raw storage path,
a storage key, a signed URL, or any credential.

## Access control

All matrix reads require project read access. All matrix mutations require
project reviewer access. A read-only user receives 403 on any mutation, and a
user without project access receives 403 on reads. The seeded public demo remains
readable when configured.

See [API_RESPONSE_MATRIX_AND_RESUBMITTALS.md](API_RESPONSE_MATRIX_AND_RESUBMITTALS.md)
for the endpoints and
[RESUBMITTAL_COLLABORATION_WORKFLOW.md](RESUBMITTAL_COLLABORATION_WORKFLOW.md) for
how matrix items connect to resubmittal rounds.
