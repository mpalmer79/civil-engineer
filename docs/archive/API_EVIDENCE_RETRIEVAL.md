# API: Evidence Retrieval and Reviewer Draft Queue

Production Foundations Sprint 3 routes for deterministic, local evidence
retrieval and the reviewer-controlled draft finding queue. All routes are under
the `/api/v1` prefix.

These endpoints are review-support only. Retrieval is deterministic and local.
Search results are candidates for reviewer evaluation, not conclusions.
Promotion creates a reviewer draft finding under human review; it does not
approve plans, certify compliance, verify CAD, validate design, declare a project
safe, resolve or close an issue, or finalize a review outcome. Responses never
include full extracted page text or raw server file paths.

## Retrieval routes

### POST /api/v1/projects/{project_id}/evidence-retrieval/search

Search a project's indexed page text.

Request:

```json
{
  "query_text": "detention basin outlet",
  "query_type": "keyword",
  "filters": {
    "document_id": null,
    "document_type": "stormwater_report",
    "text_extraction_status": null,
    "page_min": 1,
    "page_max": 20,
    "checklist_item_id": null,
    "finding_id": null
  },
  "limit": 10
}
```

Response:

```json
{
  "project_id": "proj_user_abc123",
  "query_text": "detention basin outlet",
  "query_type": "keyword",
  "retrieval_query_id": "rq_user_def456",
  "result_count": 1,
  "results": [
    {
      "document_id": "doc_user_111",
      "document_name": "Stormwater Report.pdf",
      "document_type": "stormwater_report",
      "document_page_id": "docpage_222",
      "page_number": 4,
      "page_label": "Page 4",
      "text_extraction_status": "text_extracted",
      "excerpt": "...detention basin outlet structure limits discharge to the downstream culvert...",
      "match_terms": ["detention", "basin", "outlet"],
      "ranking_score": 0.82,
      "ranking_reason": "Ranked by keyword match: detention, basin, outlet; 5 keyword hit(s) on the page.",
      "candidate_origin": "keyword_search",
      "retrieval_query_id": "rq_user_def456"
    }
  ],
  "message": "1 retrieval candidate(s) for reviewer review."
}
```

Validation: `query_text` is required and must be at least two characters.
`query_type` must be one of the allowed types. `limit` is bounded to a safe
maximum (50). Empty or too-short queries and unsupported query types return 422.
Full extracted page text is never returned.

### POST /api/v1/projects/{project_id}/evidence-retrieval/checklist/{checklist_item_id}

Search indexed evidence for one checklist item. The query text is built from the
checklist item's requirement. Returns the same `EvidenceSearchResponse` shape
with `query_type` `checklist_item`.

### POST /api/v1/projects/{project_id}/evidence-retrieval/findings/{finding_id}

Search indexed evidence for one finding. The query text is built from the
finding's title. Returns the same `EvidenceSearchResponse` shape with
`query_type` `finding_context`.

## Candidate queue routes

### GET /api/v1/projects/{project_id}/evidence-candidates

List saved candidates, newest first. Optional query parameters
`candidate_status` and `finding_id` filter the list.

### POST /api/v1/projects/{project_id}/evidence-candidates

Save a candidate from a retrieval result.

Request:

```json
{
  "document_id": "doc_user_111",
  "document_page_id": "docpage_222",
  "page_number": 4,
  "retrieval_query_id": "rq_user_def456",
  "candidate_title": "Detention basin outlet evidence",
  "candidate_excerpt": "...detention basin outlet structure...",
  "match_terms": ["detention", "basin", "outlet"],
  "ranking_score": 0.82,
  "ranking_reason": "Ranked by keyword match.",
  "candidate_origin": "keyword_search"
}
```

Response: the created `EvidenceCandidate` (status defaults to
`saved_for_review`). `document_id` and `candidate_title` are required.
Reviewer-entered text is rejected if it contains final-decision language (422).

### GET /api/v1/projects/{project_id}/evidence-candidates/{candidate_id}

Read a single candidate. Returns 404 if it does not exist for the project.

### PATCH /api/v1/projects/{project_id}/evidence-candidates/{candidate_id}

Update a candidate's status and/or reviewer note.

```json
{ "candidate_status": "needs_reviewer_triage", "reviewer_note": "Confirm outlet sizing" }
```

`candidate_status` must be an allowed value; otherwise 422.

### POST /api/v1/projects/{project_id}/evidence-candidates/{candidate_id}/dismiss

Dismiss a candidate. The status becomes `dismissed_by_reviewer`, an optional
reviewer note is stored, and the record is retained.

```json
{ "reviewer_note": "Not relevant to this review" }
```

## Promote-to-draft route

### POST /api/v1/projects/{project_id}/evidence-candidates/{candidate_id}/promote-to-draft-finding

Promote a candidate into a reviewer draft finding plus a page-level citation.

Request (all fields optional; prefilled from the candidate when omitted):

```json
{
  "title": "Detention basin outlet sizing needs reviewer confirmation",
  "category": "stormwater",
  "risk_level": "high",
  "evidence_status": "needs_reviewer_confirmation",
  "evidence_to_find": "Outlet structure sizing detail",
  "reason_it_matters": "Affects downstream culvert capacity",
  "recommended_human_action": "Reviewer should confirm the outlet sizing",
  "reviewer_note": "From retrieval candidate",
  "citation_excerpt": "...detention basin outlet structure...",
  "human_review_status": "draft"
}
```

Response:

```json
{
  "finding": {
    "finding_id": "find_draft_777",
    "project_id": "proj_user_abc123",
    "title": "Detention basin outlet sizing needs reviewer confirmation",
    "category": "stormwater",
    "risk_level": "high",
    "evidence_status": "needs_reviewer_confirmation",
    "human_review_status": "draft",
    "finding_origin": "retrieval_candidate",
    "source_mode": "user_created",
    "created_by_name": "Demo Reviewer"
  },
  "citation": {
    "evidence_citation_id": "cite_888",
    "project_id": "proj_user_abc123",
    "finding_id": "find_draft_777",
    "document_id": "doc_user_111",
    "document_page_id": "docpage_222",
    "page_number": 4,
    "citation_type": "reviewer_selected",
    "citation_status": "needs_reviewer_confirmation"
  },
  "candidate": { "...": "the candidate, now promoted_to_draft" }
}
```

Validation: `evidence_status` must be an allowed evidence status and
`human_review_status` must be an allowed reviewer finding status; otherwise 422.
Reviewer-entered content is rejected if it contains final-decision language
(422). A candidate that is already promoted or dismissed returns 422.

## Retrieval query history

### GET /api/v1/projects/{project_id}/retrieval-queries

List retrieval query history for a project, newest first. Each entry includes
the query text, query type, metadata-only filters, result count, and creator.

## Allowed statuses and types

- Query types: `keyword`, `phrase`, `checklist_item`, `finding_context`,
  `document_filter`, `combined`.
- Candidate statuses: `retrieval_candidate`, `saved_for_review`,
  `needs_reviewer_triage`, `reviewer_selected`, `promoted_to_draft`,
  `dismissed_by_reviewer`.
- Candidate origins: `keyword_search`, `phrase_search`, `checklist_search`,
  `finding_context_search`, `manual_save`.
- Evidence statuses (for promotion): `potential_issue`, `missing_evidence`,
  `conflicting_evidence`, `unclear_evidence`, `needs_reviewer_confirmation`.
- Draft finding review statuses: the reviewer finding statuses, including
  `draft` and `needs_reviewer_confirmation`.

## Professional-boundary notes

There is intentionally no `approved`, `certified`, `verified`, `passed`,
`failed`, `resolved`, or `closed` status anywhere in this API. Search results are
candidates, not conclusions. Findings created by promotion are reviewer drafts
under human review. The reviewer remains responsible for every finding. Audit
metadata never includes full extracted page text, raw server file paths,
secrets, or API keys.
