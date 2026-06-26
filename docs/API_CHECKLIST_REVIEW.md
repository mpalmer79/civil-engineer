# API: Checklist-Driven Review and Rule Packs

Production Foundations Sprint 4 routes for reusable rule packs and
checklist-driven evidence review. All routes are under the `/api/v1` prefix.

These endpoints are review-support only. A rule pack is a review-support
template, not a legal ordinance and not a compliance standard. Checklist status
is review-support only. Nothing here approves plans, certifies compliance,
verifies CAD, validates design, declares a project safe, resolves or closes an
issue, or makes a final engineering decision. Draft findings require reviewer
confirmation. Responses never include full extracted page text or raw server
file paths.

## Rule pack routes

### GET /api/v1/rule-packs

List all rule packs with item counts.

```json
[
  {
    "rule_pack_id": "rulepack_brookside_stormwater_starter",
    "name": "Brookside Stormwater Review Starter Pack",
    "jurisdiction_name": "Starter template (no jurisdiction)",
    "review_domain": "stormwater",
    "version_label": "v1",
    "source_mode": "seeded_demo",
    "is_active": true,
    "item_count": 16
  }
]
```

### GET /api/v1/rule-packs/{rule_pack_id}

Get a rule pack with its items.

```json
{
  "rule_pack_id": "rulepack_brookside_stormwater_starter",
  "name": "Brookside Stormwater Review Starter Pack",
  "item_count": 16,
  "items": [
    {
      "rule_pack_item_id": "rpi_..._do_01",
      "item_code": "DO-01",
      "category": "Detention and outlet control",
      "requirement_text": "Detention storage and outlet control are sized for the design storms.",
      "expected_evidence": "Detention basin stage storage table and outlet control structure computations.",
      "applicability_note": "Applies when detention is proposed.",
      "risk_level": "high",
      "reference_label": "Starter template, not ordinance"
    }
  ]
}
```

## Project checklist routes

### GET /api/v1/projects/{project_id}/checklists

List project checklists with item counts and status summaries.

### POST /api/v1/projects/{project_id}/checklists/from-rule-pack

Apply a rule pack to the project as a checklist.

Request:

```json
{ "rule_pack_id": "rulepack_brookside_stormwater_starter", "name": null }
```

Response: the created `ProjectChecklist` (status `checklist_started`) with item
count and status summaries. Returns 404 if the project or rule pack is missing.

### GET /api/v1/projects/{project_id}/checklists/{project_checklist_id}

Get a checklist with its items.

### GET /api/v1/projects/{project_id}/checklists/{project_checklist_id}/items

List a checklist's items.

## Checklist item review routes

### PATCH /api/v1/projects/{project_id}/checklist-items/{project_checklist_item_id}

Update reviewer-controlled status and/or note.

```json
{
  "applicability_status": "applies",
  "evidence_status": "missing_evidence",
  "review_status": "evidence_review_needed",
  "reviewer_note": "Reviewer should request the drainage report"
}
```

Unsupported statuses and final-decision language are rejected with 422.

### POST /api/v1/projects/{project_id}/checklist-items/{project_checklist_item_id}/evidence-search

Search indexed evidence for the checklist item. The query defaults to the item's
expected evidence text.

```json
{ "query_text": null, "limit": 10 }
```

Response: the deterministic evidence search response (same shape as Sprint 3),
with short excerpts only. If the project has no indexed pages, the response has
`result_count` 0 and a message asking the reviewer to upload and index a digital
PDF first.

### POST /api/v1/projects/{project_id}/checklist-items/{project_checklist_item_id}/evidence-links

Link a document page, citation, or candidate to the checklist item.

```json
{
  "document_id": "doc_user_111",
  "document_page_id": "docpage_222",
  "page_number": 4,
  "evidence_citation_id": null,
  "evidence_candidate_id": null,
  "reviewer_note": "Detention basin shown on this page",
  "link_status": "reviewer_selected"
}
```

Response: the created `ChecklistEvidenceLink`. The document and page are validated
against the project; unknown documents return 404 and bad relationships 422.

### POST /api/v1/projects/{project_id}/checklist-items/{project_checklist_item_id}/draft-finding

Create a reviewer draft finding from the checklist item.

Request (all fields optional; prefilled from the item when omitted):

```json
{
  "title": "Detention basin outlet sizing needs reviewer confirmation",
  "category": "Detention and outlet control",
  "risk_level": "high",
  "evidence_status": "missing_evidence",
  "evidence_to_find": "Detention basin stage storage table",
  "reason_it_matters": "Affects downstream culvert capacity",
  "recommended_human_action": "Reviewer should request the outlet sizing",
  "document_id": "doc_user_111",
  "page_number": 4
}
```

Response:

```json
{
  "finding": {
    "finding_id": "find_checklist_777",
    "title": "Detention basin outlet sizing needs reviewer confirmation",
    "risk_level": "high",
    "evidence_status": "missing_evidence",
    "human_review_status": "draft",
    "finding_origin": "checklist_review",
    "related_checklist_items": ["pcli_..."]
  },
  "citation": {
    "evidence_citation_id": "cite_888",
    "finding_id": "find_checklist_777",
    "document_id": "doc_user_111",
    "page_number": 4,
    "citation_context": "checklist_evidence"
  },
  "checklist_item": { "...": "review_status now draft_finding_created" }
}
```

`citation` is null when no `document_id` is provided. `evidence_status` must be an
allowed evidence status and `human_review_status` an allowed reviewer finding
status; otherwise 422. Final-decision language is rejected with 422.

## Allowed statuses

- Rule pack source modes: `seeded_demo`, `user_created`, `imported_template`.
- Project checklist statuses: `checklist_started`, `checklist_in_progress`,
  `needs_reviewer_review`, `ready_for_reviewer_handoff`, `archived_demo`.
- Applicability statuses: `applies`, `not_applicable_by_reviewer`,
  `applicability_unclear`, `needs_reviewer_confirmation`.
- Checklist evidence statuses: `not_reviewed`, `evidence_found`,
  `missing_evidence`, `conflicting_evidence`, `unclear_evidence`,
  `extraction_unavailable`, `needs_reviewer_confirmation`.
- Checklist review statuses: `not_started`, `evidence_review_needed`,
  `reviewer_note_added`, `citation_added`, `draft_finding_created`,
  `ready_for_reviewer_handoff`.
- Checklist link statuses: `reviewer_selected`, `citation_candidate`,
  `needs_reviewer_confirmation`, `extraction_unavailable`, `page_reference_only`.

## Professional-boundary notes

There is intentionally no `compliant`, `noncompliant`, `approved`, `certified`,
`verified`, `passed`, `failed`, `resolved`, or `closed` status anywhere in this
API. Rule packs are templates, not legal determinations. Checklist status is
review-support only and does not determine project outcome. Evidence search
results are candidates. Draft findings are reviewer drafts under human review.
The reviewer remains responsible for every finding. Audit metadata never includes
full extracted page text, raw server file paths, secrets, or API keys.
