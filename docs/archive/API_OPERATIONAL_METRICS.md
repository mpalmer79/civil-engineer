# API: Operational Metrics and Reviewer Dashboard

Sprint 9 operational metrics routes. All routes are under the `/api/v1` prefix.
Every route enforces Sprint 5 access control. Responses contain operational
review-support indicators only. No response represents approval, certification,
compliance, verification, or issue resolution, and no response includes storage
keys, raw server paths, signed URLs, tokens, secrets, or full record text.

## Reviewer dashboard routes

### GET /api/v1/dashboard/reviewer

Returns the reviewer dashboard for the signed-in user.

- Access: authenticated user. Unauthenticated requests receive 401.
- Scope: only projects the user can read are included.

Example response (abbreviated):

```json
{
  "scope": "reviewer",
  "generated_at": "2026-06-26T12:00:00Z",
  "user_id": "user_abc",
  "display_name": "Reviewer One",
  "accessible_project_count": 2,
  "projects_with_pending_action_count": 1,
  "totals": {
    "documents_needing_indexing": 3,
    "evidence_candidates_needing_triage": 2,
    "checklist_items_missing_evidence": 1,
    "applicant_responses_needing_review": 2,
    "response_packages_ready_for_handoff": 1,
    "pending_reviewer_action_count": 9
  },
  "projects": [
    {
      "project_id": "proj_1",
      "project_name": "Brookside Meadows",
      "status": "under_review_support",
      "age_bucket": "waiting_1_to_3_days",
      "due_date_indicators": [],
      "pending_reviewer_action_count": 9,
      "has_pending_reviewer_action": true,
      "metrics": { "documents_needing_indexing": 3 }
    }
  ],
  "queue": [
    {
      "queue_item_id": "proj_1:documents_needing_indexing",
      "project_id": "proj_1",
      "project_name": "Brookside Meadows",
      "item_type": "document_indexing",
      "label": "Documents needing indexing",
      "count": 3,
      "status": "pending_reviewer_action",
      "age_bucket": "waiting_1_to_3_days",
      "target_path": "/projects/proj_1/documents"
    }
  ],
  "access_note": "Dashboard data is limited to projects you can access. Counts are operational review-support indicators only."
}
```

### GET /api/v1/dashboard/reviewer/queue

Returns the reviewer queue across accessible projects.

- Query: `item_type` (optional) filters by queue item type.
- Access: authenticated user.

### GET /api/v1/dashboard/reviewer/projects

Returns the list of accessible project summaries (the `projects` array shape
above).

- Access: authenticated user.

## Organization dashboard routes

### GET /api/v1/organizations/{organization_id}/dashboard

Returns the organization workload dashboard.

- Access: organization membership required. Non-members receive 403.
- Scope: only organization projects the member can read.

Response includes `project_count`, `projects_with_pending_action_count`,
`status_counts`, `priority_counts`, `totals`, and per-project `projects`.

### GET /api/v1/organizations/{organization_id}/workload

Returns the organization workload aggregate summary (the same totals and status
counts without the per-project list).

- Access: organization membership required.

### GET /api/v1/organizations/{organization_id}/reviewers/workload

Returns per-reviewer workload summaries grouped by assigned reviewer.

- Access: org_admin or senior_reviewer membership required. Other members
  receive 403.

Example response (abbreviated):

```json
{
  "scope": "organization",
  "organization_id": "org_1",
  "viewer_role": "org_admin",
  "reviewers": [
    {
      "assigned_reviewer_user_id": "user_abc",
      "assigned_reviewer_name": "Reviewer One",
      "project_count": 3,
      "pending_reviewer_action_count": 12,
      "projects_with_pending_action_count": 2
    }
  ],
  "access_note": "Reviewer workload is grouped by assigned reviewer across accessible projects."
}
```

## Project workload routes

### GET /api/v1/projects/{project_id}/workload-summary

Returns a single project's workload summary, including metrics, a pending-action
queue, and the assigned reviewer and review priority.

- Access: project read access. Unauthorized users receive 403; unauthenticated
  users on a non-public project receive 401.

### GET /api/v1/projects/{project_id}/pending-actions

Returns the pending reviewer action queue for one project.

- Access: project read access.

## Project assignment and priority routes

### PATCH /api/v1/projects/{project_id}/assignment

Assigns a reviewer to a project. Body:

```json
{ "assigned_reviewer_user_id": "user_abc", "assigned_reviewer_name": "Reviewer One", "note": null }
```

- Access: project admin (or organization admin) access required.
- Writes a `project_assignment_updated` audit event.
- Reviewer-entered names and notes are rejected if they contain final-decision
  wording.

### PATCH /api/v1/projects/{project_id}/priority

Updates a project's review priority and optional due date. Body:

```json
{ "review_priority": "elevated", "review_due_date": "2026-07-15T00:00:00Z", "note": null }
```

- Allowed priorities: `low`, `standard`, `elevated`, `time_sensitive`.
  Unsupported values are rejected with 422.
- Access: project admin (or organization admin) access required.
- Writes a `project_priority_updated` audit event.

## Metric response payloads

Per-project metrics use these safe keys, all integer counts:

- `documents_uploaded`, `documents_needing_indexing`,
  `documents_indexed_with_text`, `documents_extraction_unavailable`
- `findings_needing_reviewer_confirmation`
- `evidence_candidates_needing_triage`
- `checklist_items_missing_evidence`, `checklist_items_unclear_evidence`
- `applicant_responses_needing_review`
- `resubmittal_rounds_registered`
- `matrix_items_carried_forward`
- `response_packages_draft`, `response_packages_ready_for_handoff`,
  `packages_issued_by_reviewer`
- `pending_reviewer_action_count`, `has_pending_reviewer_action`

## Professional-boundary notes

These routes provide workload visibility only. They do not approve plans, certify
compliance, verify CAD, validate design, declare a project safe, resolve an issue,
or close an issue. There is intentionally no count or status labeled approved,
closed, resolved, passed, failed, compliant, verified, certified, safe, or unsafe.
Every pending item requires human review.
