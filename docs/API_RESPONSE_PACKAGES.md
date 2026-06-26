# API: Reviewer Response Packages and Comment Letters

Production Foundations Sprint 8 routes for reviewer response packages and comment
letter drafts. All routes are under the `/api/v1` prefix and the existing project
prefix. The project-scoped namespace is `reviewer-response-packages`, which is
distinct from the Phase 10 demo `response-packages` routes so the demo is
preserved.

Reads require project read access. Mutations require project reviewer access. A
read-only user receives 403 on mutations, and a user without project access
receives 403 on reads. The public demo remains readable when configured.

Responses never include a raw filesystem path, a storage key, a signed URL, a
token, or any credential. Issuing a package records a reviewer communication only.
Nothing here approves a project, certifies compliance, verifies CAD, validates
design, resolves an issue, or closes an issue.

## Response packages

- `GET /projects/{project_id}/reviewer-response-packages` lists packages.
- `POST /projects/{project_id}/reviewer-response-packages` creates a package.
  Writes `response_package_created`.
- `GET /projects/{project_id}/reviewer-response-packages/{response_package_id}`
  returns a package with its items.
- `POST .../{response_package_id}/items/matrix-items` adds response matrix items.
  Body: `{ "matrix_item_ids": ["..."] }`. Writes `response_package_item_added`.
- `POST .../{response_package_id}/items/findings` adds findings. Body:
  `{ "finding_ids": ["..."] }`.
- `POST .../{response_package_id}/items/checklist-items` adds checklist items.
  Body: `{ "checklist_item_ids": ["..."] }`.
- `POST .../{response_package_id}/items/citations` adds citations. Body:
  `{ "citation_ids": ["..."] }`.
- `POST .../{response_package_id}/items/manual` adds a manual reviewer note. Body:
  `{ "reviewer_comment_text": "...", "category": "...", "requested_evidence": "..." }`.
- `GET .../{response_package_id}/preview` returns safe preview data with the
  boundary statement.
- `POST .../{response_package_id}/ready-for-handoff` marks the package ready for
  reviewer handoff. Writes `response_package_ready_for_handoff`.
- `POST .../{response_package_id}/issue` issues the package. Body:
  `{ "reviewer_note": "..." }` (optional). Writes `response_package_issued`.
- `POST .../{response_package_id}/revisions` starts a revision. Body:
  `{ "revision_reason": "..." }` (optional). Writes
  `response_package_revision_created`.

## Package items

- `PATCH /projects/{project_id}/reviewer-response-package-items/{package_item_id}`
  updates item text, follow-up text, requested evidence, the include-in-letter
  flag, sort order, and the item status. Writes `response_package_item_updated`.

## Comment letter drafts

- `POST /projects/{project_id}/reviewer-response-packages/{response_package_id}/comment-letter-draft`
  generates a deterministic comment letter draft. Body:
  `{ "recipient_name": "...", "recipient_organization": "..." }` (optional). Writes
  `comment_letter_draft_created`.
- `GET /projects/{project_id}/comment-letter-drafts/{draft_id}` returns a draft.
- `PATCH /projects/{project_id}/comment-letter-drafts/{draft_id}` updates draft
  sections and status. Writes `comment_letter_draft_updated` (or
  `comment_letter_ready_for_handoff` when the status becomes ready for handoff).
- `GET /projects/{project_id}/comment-letter-drafts/{draft_id}/preview` returns
  safe preview sections with the boundary statement.

## Example: create a package and add findings

Request:

```
POST /api/v1/projects/proj_abc/reviewer-response-packages
{ "package_title": "Round 1 review comments", "package_type": "initial_review_comment_letter" }
```

Response (201):

```json
{
  "response_package_id": "rpkg_abc",
  "project_id": "proj_abc",
  "package_title": "Round 1 review comments",
  "package_number": 1,
  "revision_number": 0,
  "status": "package_draft",
  "package_type": "initial_review_comment_letter",
  "item_count": 0,
  "items": []
}
```

```
POST /api/v1/projects/proj_abc/reviewer-response-packages/rpkg_abc/items/findings
{ "finding_ids": ["find_1"] }
```

The response is the updated package detail with the new item and
`status` advanced to `package_in_review`.

## Allowed statuses

- Package status: `package_draft`, `package_in_review`,
  `ready_for_reviewer_handoff`, `issued_by_reviewer`, `revision_started`,
  `archived_demo`.
- Package type: `initial_review_comment_letter`,
  `resubmittal_review_comment_letter`, `checklist_review_summary`,
  `response_matrix_summary`, `reviewer_handoff_package`.
- Package item source type: `finding`, `checklist_item`, `response_matrix_item`,
  `citation`, `document_reference`, `resubmittal_summary`, `manual_reviewer_note`.
- Package item status: `item_draft`, `needs_reviewer_confirmation`,
  `ready_for_reviewer_handoff`, `carried_forward_for_review`,
  `reviewer_note_added`.
- Comment letter draft status: `draft_created`, `reviewer_editing`,
  `ready_for_reviewer_handoff`, `issued_by_reviewer`, `superseded_by_revision`.

## Validation and professional boundary

Reviewer-entered free-text fields (package title, manual reviewer comment,
requested evidence, reviewer note, revision reason, recipient fields, and every
editable comment letter section) are checked against the prohibited-language
guard, which rejects final-outcome wording. Status values are validated against
the Sprint 8 review-support status sets. An invalid status returns 422 with a safe
message. Source records must belong to the same project as the package; a
mismatch returns 404.
