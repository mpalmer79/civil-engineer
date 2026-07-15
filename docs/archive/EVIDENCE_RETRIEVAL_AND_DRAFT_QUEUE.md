# Evidence Retrieval and Reviewer Draft Queue

This document describes the deterministic, local evidence retrieval layer and
the reviewer-controlled draft finding queue added in Production Foundations
Sprint 3.

Retrieval is review-support only. It does not call an external service, does not
call an AI provider, and does not OCR. Search results are candidates for reviewer
evaluation, not conclusions. The system never approves plans, certifies
compliance, verifies CAD, validates design, declares a project safe, resolves or
closes an issue, or makes a final engineering decision.

## Deterministic keyword and metadata retrieval

The retrieval service (`backend/app/services/evidence_retrieval_service.py`)
searches indexed `DocumentPage` rows for a project. It uses only stored data:
the extracted text produced by Sprint 2 indexing and document metadata. The same
query against the same indexed pages always produces the same ranked results.

Supported query types:

- `keyword`: tokenized keyword overlap.
- `phrase`: only pages where the exact phrase appears are returned.
- `checklist_item`: query text is built from a checklist item's requirement.
- `finding_context`: query text is built from a finding's title.
- `document_filter` and `combined`: keyword search with metadata filters.

Optional filters: `document_id`, `document_type`, `text_extraction_status`,
`page_min`, `page_max`, `checklist_item_id`, and `finding_id`.

## Indexed PDF pages as the retrieval source

Only pages with `text_extraction_status` of `text_extracted` are searched. Pages
with no embedded text layer (for example scanned images recorded as
`no_extractable_text` in Sprint 2) are skipped, not treated as errors. There is
no OCR. If a project has no indexed page text, the search returns an empty result
with a helpful message rather than failing.

## Candidate scoring

Scoring is intentionally simple and transparent. Each candidate's score is bounded
below 1.0 so the system never implies a perfect or certain match. The score
combines:

- a base score for any match,
- a strong weight when the exact phrase appears on the page,
- a weight per distinct matched keyword,
- a small weight for the total number of keyword hits,
- a small weight for keyword density (hits per word on the page),
- a small weight when the document type or file name matches.

Results are sorted by score, then by document id and page number so ties resolve
deterministically. Each result carries a plain `ranking_reason` string that
explains why it ranked, for example "Ranked by exact phrase appears on this page;
keyword match: detention, basin."

## Excerpts and match highlights

A result returns a short excerpt centered on the first matched term, bounded well
below the full page text, with an ellipsis when the page extends past the window.
The full extracted page text is never returned in a search result. Highlighting
is represented as `match_terms` (the terms that matched) plus the excerpt; there
is no complex HTML highlighting.

## Reviewer draft queue

A reviewer saves a useful result as an `EvidenceCandidate`. The candidate is a
durable queue row with the document, page, excerpt, match terms, ranking score,
ranking reason, status, and origin. Allowed candidate statuses:

- `retrieval_candidate`
- `saved_for_review`
- `needs_reviewer_triage`
- `reviewer_selected`
- `promoted_to_draft`
- `dismissed_by_reviewer`

Allowed candidate origins: `keyword_search`, `phrase_search`,
`checklist_search`, `finding_context_search`, `manual_save`. There is
intentionally no `approved`, `verified`, `passed`, `failed`, `resolved`, or
`closed` value.

## Promote-to-draft workflow

When a reviewer promotes a candidate:

- a `Finding` is created with `finding_origin` `retrieval_candidate` and a safe
  draft `human_review_status` (default `draft`),
- the evidence status is reviewer-selected from the allowed evidence statuses,
- the risk level is reviewer-entered, never a system conclusion,
- a page-level `EvidenceCitation` links the source document and page to the new
  finding,
- the candidate status becomes `promoted_to_draft` and records the new finding
  id,
- reviewer-entered draft content is rejected if it contains final-decision
  language.

A candidate that was already promoted, or that was dismissed, cannot be promoted
again without reviewer action.

## Dismissal workflow

When a reviewer dismisses a candidate, the status becomes `dismissed_by_reviewer`,
an optional reviewer note is stored, and the dismissal timestamp is recorded. The
record and its audit trail are retained; nothing is deleted.

## Audit events

The service writes `evidence_search_performed`, `evidence_candidate_saved`,
`evidence_candidate_updated`, `evidence_candidate_dismissed`,
`evidence_candidate_promoted_to_draft`, `draft_finding_created_from_candidate`,
and `citation_created_from_candidate`. Audit metadata records query type, result
count, candidate id, document id, page number, finding id, and status changes
only. It never records full extracted page text, raw server file paths, secrets,
or API keys.

## Limitations

- Deterministic keyword and phrase retrieval only. There are no embeddings and no
  semantic similarity.
- No OCR. Pages without an embedded text layer are not searchable.
- No live AI calls.
- Search results are candidates, not conclusions. A reviewer must confirm
  everything.
- Ranking is a transparent local relevance signal, never proof of correctness.
- Uploaded files remain local unless deployment storage is configured.
- There is no real authentication yet; a demo reviewer identity stands in for
  attribution.

## Future hybrid retrieval and live AI work

Later sprints may add a hybrid retrieval step (keyword plus embeddings) evaluated
against this deterministic baseline, and optional live AI assistance that drafts
candidate findings for reviewer confirmation. Any such addition must keep the
reviewer-control and audit guarantees established here and must keep search
results as candidates, not conclusions.
