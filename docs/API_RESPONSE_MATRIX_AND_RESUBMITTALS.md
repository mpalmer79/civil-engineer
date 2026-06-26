# API: Applicant Response Matrix and Resubmittals

Production Foundations Sprint 7 routes for the applicant response matrix and the
resubmittal collaboration workflow. All routes are under the `/api/v1` prefix and
the existing project prefix.

Reads require project read access. Mutations require project reviewer access. A
read-only user receives 403 on mutations, and a user without project access
receives 403 on reads. The seeded public demo remains readable when configured.

Responses never include a raw storage path, a storage key, a signed URL, or any
credential. Audit metadata records a response length, never the full applicant
response text. Nothing here approves plans, certifies compliance, verifies CAD,
validates design, or makes any final engineering decision. An applicant response
is recorded for reviewer review, never as proof. Carry-forward means continued
review, not resolution.

## Response matrix

- `GET /projects/{project_id}/response-matrices` lists matrices with status
  summaries.
- `POST /projects/{project_id}/response-matrices` creates a matrix. Writes
  `response_matrix_created`.
- `GET /projects/{project_id}/response-matrices/{response_matrix_id}` returns a
  matrix with its items.
- `POST /projects/{project_id}/response-matrices/{response_matrix_id}/items/from-finding/{finding_id}`
  adds a reviewer finding as a matrix item. Writes `response_matrix_item_added`.
- `POST /projects/{project_id}/response-matrices/{response_matrix_id}/items/from-checklist-item/{checklist_item_id}`
  adds a checklist review item as a matrix item. Writes
  `response_matrix_item_added`.
- `GET /projects/{project_id}/response-matrices/{response_matrix_id}/items` lists
  items, with an optional `applicant_response_status` filter.

## Response matrix items

- `GET /projects/{project_id}/response-matrix-items/{matrix_item_id}` returns one
  item.
- `PATCH /projects/{project_id}/response-matrix-items/{matrix_item_id}` updates
  reviewer fields and review-support statuses. Writes
  `response_matrix_item_updated`.
- `POST /projects/{project_id}/response-matrix-items/{matrix_item_id}/applicant-response`
  records an applicant response. Requires response text. Moves the item to
  `applicant_response_received` by default and a `not_reviewed` follow-up status
  to `needs_reviewer_confirmation`. Writes `applicant_response_recorded` with a
  response length, not the full text.
- `POST /projects/{project_id}/response-matrix-items/{matrix_item_id}/documents/{document_id}`
  links a supporting document to the item with a review-support link type. Writes
  `response_document_linked`. The response never includes a storage path or
  storage key.
- `POST /projects/{project_id}/response-matrix-items/{matrix_item_id}/carry-forward`
  carries the item into the next round. Writes
  `response_matrix_item_carried_forward`.

## Resubmittal rounds

- `GET /projects/{project_id}/resubmittal-rounds` lists rounds.
- `POST /projects/{project_id}/resubmittal-rounds` registers a round. Advances the
  project review round counter. Writes `resubmittal_round_registered`.
- `GET /projects/{project_id}/resubmittal-rounds/{round_id}` returns one round.
- `POST /projects/{project_id}/resubmittal-rounds/{round_id}/documents/{document_id}`
  links a document to the round and moves it to `documents_received`. Writes
  `resubmittal_document_linked`.
- `POST /projects/{project_id}/resubmittal-rounds/{round_id}/carry-forward-items`
  carries response matrix items into the round. Writes
  `resubmittal_items_carried_forward`.
- `GET /projects/{project_id}/resubmittal-rounds/{round_id}/summary` returns
  review-support status counts for the matrix items connected to the round.

## Validation and safety

Free-text fields (matrix name, reviewer comment draft, requested evidence,
reviewer note, applicant response text, round label, summary) are checked against
the prohibited-language guard, which rejects final-outcome wording. Status values
are validated against the Sprint 7 review-support status sets. An invalid status
returns 400 with a safe message.

See [APPLICANT_RESPONSE_MATRIX.md](APPLICANT_RESPONSE_MATRIX.md) and
[RESUBMITTAL_COLLABORATION_WORKFLOW.md](RESUBMITTAL_COLLABORATION_WORKFLOW.md) for
the models and workflow.
