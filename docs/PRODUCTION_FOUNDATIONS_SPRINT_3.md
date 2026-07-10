# Production Foundations Sprint 3: Evidence Retrieval and Reviewer Draft Finding Queue

> Historical record. This document describes a completed build phase and is
> not current implementation guidance. See docs/README.md for the current
> documentation index.

This sprint adds a deterministic, local evidence retrieval layer over the Sprint
2 indexed PDF page text, plus a reviewer-controlled queue of evidence candidates
that a human reviewer can promote into draft review-support findings.

The product moves from "reviewers can manually inspect indexed pages and create
citations" to "reviewers can search indexed project evidence, review citation
candidates, and promote useful evidence into draft review-support findings."

Everything here is review-support only. Retrieval is deterministic and local. It
does not call an external service, does not call an AI provider, and does not
OCR. It does not approve plans, certify compliance, verify CAD, validate design,
declare a project safe, resolve or close an issue, or make a final engineering
decision. Search results are candidates for reviewer evaluation, not
conclusions. Promotion creates a reviewer draft finding under human review; it
never finalizes a review outcome.

## What Sprint 3 adds

Backend:

- An `EvidenceCandidate` model: a durable, reviewer-controlled queue row holding
  a retrieval result, its match terms, ranking score, ranking reason, status,
  origin, reviewer note, and any promotion link.
- Sprint 3 fields on the existing `RetrievalQuery` model: `query_type`,
  `filters`, `related_finding_id`, `created_by_actor_id`, `created_by_name`, and
  `event_metadata`. All are nullable with safe defaults so the seeded Phase 3
  retrieval query records keep working.
- An `evidence_retrieval_service` that searches indexed `DocumentPage` rows,
  ranks them deterministically, records `RetrievalQuery` rows, manages the
  candidate queue, and promotes a candidate into a draft finding plus a
  page-level citation.
- Review-support vocabulary for retrieval query types, candidate statuses, and
  candidate origins, plus a bounded result limit.
- API routes for search, checklist-item and finding-context search, candidate
  queue management, promotion, and retrieval query history.

Frontend:

- An evidence retrieval API client (`lib/api/evidenceRetrieval.ts`).
- An evidence search page with a query input, query type selector, document and
  document-type and page-range filters, a result limit, ranked results with
  excerpts and match terms, and save-candidate actions.
- A candidate queue page and a candidate detail page with reviewer note editing,
  dismissal, and a promote-to-draft form.
- Links from the project overview, finding detail, and document page views.
- A homepage update describing Sprint 3.

## How this builds on Sprint 1 and Sprint 2

Sprint 1 created the real-world foundation: user-created projects, document
registration and upload, reviewer-created findings, basic evidence references,
and durable audit events. Sprint 2 indexed uploaded digital PDFs into
page-level `DocumentPage` records with extracted text and added reviewer-selected
`EvidenceCitation` records.

Sprint 3 reads those indexed pages. Retrieval searches the `DocumentPage.extracted_text`
produced in Sprint 2, and promotion reuses the Sprint 2 citation service to link
the source page to the new draft finding. Nothing in Sprint 1 or Sprint 2 was
removed or changed in a breaking way.

## Why retrieval comes before live AI

Retrieval is the trustworthy substrate that any later AI assistance must sit on.
Before adding embeddings or a live model, the system needs a deterministic,
auditable way to find candidate evidence, a reviewer-controlled queue, and a
clear boundary that keeps search results as candidates rather than conclusions.
Building that first means a later hybrid or AI-assisted retrieval step can be
evaluated against a known-good deterministic baseline, and the reviewer-control
and audit guarantees are already in place.

## What remains demo-only

Brookside Meadows and every existing demo page are unchanged. The seeded demo
has checklist items and findings but no indexed PDF page text, so an evidence
search there returns a safe empty result with the message "No indexed page text
is available yet. Upload and index a digital PDF before searching evidence." A
checklist-item search against the demo runs deterministically and returns the
same safe empty result.

## What remains out of scope

Embeddings and vector search, OCR, live AI calls, DWG/DXF parsing, GIS,
Bluebeam, applicant portal functionality, automated engineering calculations,
geometry or design validation, final approval workflows, and SSO or full
authentication are out of scope. Retrieval covers deterministic keyword and
phrase matching over indexed digital PDF page text only.

## How reviewers search indexed evidence

1. Open a real project that has at least one uploaded, indexed digital PDF.
2. Open Evidence search from the project overview.
3. Enter search text and choose a query type (keyword, exact phrase, or
   combined). Optionally filter by document, document type, or page range, and
   set a result limit.
4. Review ranked results. Each result shows the document name, page number, a
   short excerpt, match terms, a relevance score, and a ranking reason.
5. Save useful results as evidence candidates, or add them to the draft queue.

A reviewer can also run a checklist-item search or a finding-context search,
which build the query text from the checklist requirement or the finding title.

## How citation candidates differ from findings

A retrieval result is a candidate: a page the reviewer might want to use. A
saved candidate is a durable queue row that still requires reviewer triage. A
finding is a reviewer-owned review-support issue. A candidate becomes a finding
only when a reviewer promotes it and confirms or edits the finding content. The
candidate carries a ranking score; a finding never does. Neither a candidate nor
a finding is a conclusion, and neither uses final-decision language.

## How draft findings require reviewer control

Promotion is always a reviewer action. The system never auto-promotes a
candidate. The promote-to-draft form prefills values from the candidate, but the
reviewer can edit the title, category, risk level, evidence status, evidence to
find, reason it matters, recommended human action, reviewer note, and citation
excerpt. The risk level is reviewer-entered, never a system conclusion. The new
finding is created with `finding_origin` `retrieval_candidate` and a safe draft
`human_review_status`. The candidate moves to `promoted_to_draft` and links to
the new finding. A page-level `EvidenceCitation` is created from the source
document and page.

## How to test the workflow locally

Backend:

```
cd backend
pip install -r requirements.txt pytest-cov
pytest --cov=app --cov-report=term-missing --cov-fail-under=90
```

The retrieval and queue tests live in `tests/test_evidence_retrieval.py`. They
upload small in-memory PDFs with a known text layer, index them, search,
save candidates, dismiss, and promote.

Frontend:

```
npm install
npm run typecheck
npm run lint
npm test
npm run build
```

Manual end-to-end: create a project, upload a digital PDF, index it, open
Evidence search, run a keyword search, save a candidate, open the candidate
queue, open the candidate, and promote it to a draft finding. Inspect Audit
events to see the search, save, queue, promotion, and citation events.

## Audit events

Sprint 3 writes these audit events: `evidence_search_performed`,
`evidence_candidate_saved`, `evidence_candidate_updated`,
`evidence_candidate_dismissed`, `evidence_candidate_promoted_to_draft`,
`draft_finding_created_from_candidate`, and `citation_created_from_candidate`.
Audit metadata records query type, result count, candidate id, document id, page
number, finding id, and status changes only. It never records full extracted
page text, raw server file paths, secrets, or API keys.

## Limitations and next steps

See [EVIDENCE_RETRIEVAL_AND_DRAFT_QUEUE.md](EVIDENCE_RETRIEVAL_AND_DRAFT_QUEUE.md)
for the retrieval design, scoring, and limitations, and
[API_EVIDENCE_RETRIEVAL.md](API_EVIDENCE_RETRIEVAL.md) for the API contract. The
recommended next sprint is Production Foundations Sprint 4: Checklist-Driven
Evidence Review and Rule Pack Foundation.
