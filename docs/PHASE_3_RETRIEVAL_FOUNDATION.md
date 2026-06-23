# Phase 3: Document Evidence and Retrieval Foundation

**Product:** Civil Engineer AI: Stormwater Review Assistant
**Phase:** 3, Document Evidence and Retrieval Foundation

Phase 2 delivered the FastAPI backend, the SQLAlchemy data model, the seeded
Brookside Meadows fixture, API endpoints, tests, and frontend integration.
Phase 3 adds the foundation for source evidence and retrieval so that every
review-support finding can trace back to specific pages and sections of the
submitted documents.

Civil Engineer AI is a review-support and evidence-organization system. It does
not approve plans, certify compliance, stamp drawings, replace a licensed
Professional Engineer, or make final safety determinations. Phase 3 does not add
live AI-generated findings, embeddings, or a vector store. Retrieval is keyword
and metadata based.

## What Phase 3 adds

- A `document_chunks` table and 56 seeded synthetic chunks across the document
  package.
- A `finding_sources` table and 21 seeded source evidence records that link the
  ten expected findings to specific chunks, each with an evidence role and a
  confidence value.
- A `retrieval_queries` table and a few seeded queries for future auditing.
- A keyword and metadata retrieval service.
- Backend endpoints for chunks, search, checklist evidence, finding evidence,
  and finding sources.
- Frontend evidence display on the findings, checklist, and documents pages, and
  an evidence-first section on the homepage.
- Backend tests proving retrieval works on the seeded fixture.

It also completes the Phase 2 review cleanup: the package description is updated,
the `BrooksideProject` type name is corrected, configuration uses
`pydantic-settings`, attribution suppression is strengthened, and stale naming
and dash characters are removed.

## Why source evidence matters

A review-support system earns trust by showing its work. A finding that says
"infiltration testing not found" is only useful if a reviewer can see exactly
which documents were checked and what they did or did not contain. Source
evidence makes findings inspectable and keeps the human reviewer in control. It
is also the groundwork for Phase 4, where live AI review must cite retrieved
evidence rather than answer from memory.

## How document chunks are modeled

A `document_chunk` is a short, retrievable excerpt of a document. Phase 3 seeds
synthetic chunks rather than parsing real files. Each chunk carries:

- `chunk_id`, `project_id`, `document_id`
- `document_type` and `file_name` (denormalized for fast, source-linked results)
- `page_number`, `section_heading`, `chunk_index`
- `content` (the excerpt)
- `keywords` (a small list used for ranking)
- `related_checklist_items` and `related_findings` (links into the review model)

Chunks are short and realistic but synthetic. They do not reproduce any real
private engineering document. They intentionally carry both the evidence and the
gaps behind the planted review issues.

## How finding sources connect to findings

A `finding_source` links a finding to a chunk and records the role that evidence
plays. The evidence roles are:

- `supports_finding`
- `shows_missing_evidence`
- `shows_conflict`
- `context_only`
- `requires_reviewer_confirmation`

A finding source is not a conclusion. It records where a reviewer can inspect
evidence relevant to a finding and how strong that evidence appears
(`confidence`). For example, the missing infiltration testing finding links to a
soils report chunk that states field testing was not performed
(`shows_missing_evidence`) and to a municipal checklist chunk that requires it
(`context_only`).

## How keyword retrieval works in Phase 3

The retrieval service ranks chunks with a simple, transparent score:

- Keyword overlap between the query and a chunk's keyword list (strongest)
- Whole-phrase appearance in the keyword list or content
- Token overlap with the chunk content
- Token overlap with the section heading

The score is bounded below 1.0 so the system never implies a perfect or certain
match, and every result includes a plain `relevance_reason`. Checklist evidence
is retrieved by the `related_checklist_items` link, and finding evidence is
retrieved from the seeded `finding_sources`, ordered by evidence role and
confidence. Weak results (no overlap) are dropped rather than forced.

Every retrieval result includes a `safety_note`:

> This is source evidence for reviewer evaluation, not a final engineering
> conclusion.

## API endpoints

Document chunks:

- `GET /api/v1/projects/{project_id}/chunks`
- `GET /api/v1/documents/{document_id}/chunks`
- `GET /api/v1/chunks/{chunk_id}`

Retrieval and evidence:

- `GET /api/v1/projects/{project_id}/search?query=...`
- `GET /api/v1/projects/{project_id}/checklist/{checklist_item_id}/evidence`
- `GET /api/v1/projects/{project_id}/findings/{finding_id}/evidence`
- `GET /api/v1/findings/{finding_id}/sources`

A retrieval result looks like:

```json
{
  "chunk_id": "chunk_soil_004",
  "document_id": "doc_soils_report",
  "file_name": "soils-geotechnical-report.pdf",
  "document_type": "soil_report",
  "page_number": 5,
  "section_heading": "Infiltration Feasibility",
  "excerpt": "Field infiltration testing was not performed as part of this geotechnical scope.",
  "relevance_reason": "Matches on keyword match: infiltration testing.",
  "score": 0.86,
  "evidence_role": "shows_missing_evidence",
  "safety_note": "This is source evidence for reviewer evaluation, not a final engineering conclusion."
}
```

## Frontend integration

The frontend API client adds functions to fetch project chunks, document chunks,
search results, checklist evidence, and finding evidence. The findings page shows
a source evidence section for each finding (excerpt, document, page, section,
evidence role, and source strength). The checklist page expands each item to show
the seeded chunks linked to it, or shows "Evidence not found" when there are
none. The documents page exposes seeded chunks per document. The homepage adds an
evidence-first section.

## Data consistency: backend seed data is canonical

Starting in Phase 3, the backend seed data is the canonical source for evidence.
To avoid drift, the frontend does not duplicate the full chunk set. When the
backend is reachable, the evidence views render live data. When it is not, the
views show an evidence status note rather than stale or duplicated data. The
existing project, document, checklist, finding, audit, evaluation, and hotspot
views retain their minimal static fallback from Phase 2.

## Why embeddings and live AI are still out of scope

Phase 3 deliberately keeps retrieval simple and explainable. Keyword and
metadata ranking is enough to demonstrate evidence-first review on the seeded
fixture, it is easy to test deterministically, and it avoids introducing model
calls or a vector store before the review workflow needs them. Embeddings,
semantic retrieval, and live AI-generated findings are deferred so the evidence
model and the safety boundaries can be proven first.

## How Phase 3 prepares for Phase 4

- Findings already carry source evidence, so Phase 4 AI review can be required to
  cite retrieved chunks rather than answer from memory.
- The evidence roles and the safety note give Phase 4 a vocabulary for framing
  AI output as review-support, not conclusions.
- The retrieval service is a clean seam: an embedding based ranker can be added
  behind the same interface without changing the API or the UI.

## Safety boundaries for retrieval outputs

- Retrieval returns source evidence, never a decision. Every result carries the
  safety note and findings remain under human review.
- Statuses and finding conclusions never use prohibited final-decision language
  (approved, certified, fully compliant, safe). Tests assert this for retrieval
  responses and finding evidence.
- Scores are bounded below 1.0 to avoid implying certainty.

## Known limitations

- Keyword retrieval has no semantic understanding. A query that uses different
  words than the seeded keywords and content may miss relevant chunks.
- Chunks are synthetic and short. They illustrate the evidence model rather than
  reproduce full documents.
- Confidence and score values are heuristic, not calibrated.
- The frontend evidence views require the backend to be running; with the
  backend down they show an evidence status note instead of data.

## What Phase 4 should build next

- Live AI review generation that cites retrieved evidence and returns structured,
  validated findings.
- Prohibited-wording and schema validation on AI output before it is stored.
- Human review required for every AI-generated finding.
- Optionally, an embedding based ranker behind the existing retrieval interface.
