# Phase 2: Retrieval Brain

This document describes the implemented retrieval behavior for real-derived chunk
evidence. It reflects what the code does today. The system provides
review-support evidence candidates only. It does not make engineering decisions
and does not state that evidence satisfies a requirement.

## Real-derived chunks

Real PDF page indexing extracts embedded text into DocumentPage rows. The chunk
pipeline (`POST /projects/{project_id}/documents/{document_id}/chunk-pages`)
turns indexed page text into DocumentChunk rows. Chunks are only built from pages
whose `text_extraction_status` is `text_extracted`, never span pages, and are
idempotent on re-run.

The document detail page gates "Build page chunks" on indexed extractable text.
A document that is uploaded but not indexed shows a message to index first. A
document indexed with no extractable text shows that page chunks cannot be built
from no-text pages, framed as a workflow state and not a finding about document
content.

## Chunk provenance

DocumentChunk has a durable `chunk_origin` field:

* `seeded_demo` for seeded demo chunks
* `real_derived` for chunks built from indexed page text

Older rows created before this field have a null `chunk_origin`. For those, the
real-derived chunk_id prefix (`rdc_`) is used as a fallback so a transition
database keeps working. New code writes and prefers `chunk_origin`.

Migration note: the backend initializes schema with
`Base.metadata.create_all` and has no migration tooling, so the `chunk_origin`
and `chunk_embeddings` additions apply automatically to fresh databases only. An
existing production database needs a one-time `ALTER TABLE` (and a backfill of
`chunk_origin`) before these features behave correctly there.

## Retrieval modes

All chunk retrieval runs over real-derived chunks only and excludes seeded demo
chunks. Every mode applies the not-indexed guardrail: only chunks whose source
page is indexed with extractable text are searchable. Scores are relevance
indicators, not correctness, and are bounded below 1.0.

Route: `POST /projects/{project_id}/evidence-retrieval/chunk-search` with a
`mode` of `keyword`, `semantic`, or `hybrid`.

### Keyword

Deterministic local scoring by exact phrase match, keyword overlap, term
frequency, and document metadata match. `match_terms` lists the matched terms.

### Semantic

Backend-only, deterministic, local embeddings (no provider keys, no network, no
frontend secrets). The embedding model is a concept-lexicon model that maps text
onto domain concept dimensions plus hashed token dimensions, so a query about a
"retention pond" can surface a chunk about a "detention basin" through a shared
concept. Query text is embedded backend-side and chunks are ranked by cosine
similarity. A semantic-only match has an empty `match_terms`; the system does not
fabricate keyword terms. `ranking_reason` reads: "Ranked by semantic similarity
using chunk embedding."

Embeddings are stored in the `chunk_embeddings` table as JSON vectors with the
provider, model name, model version, dimension, and a content hash. The backfill
(`POST /projects/{project_id}/evidence-retrieval/embed-chunks`) embeds
real-derived chunks, skips chunks already embedded with the current model and
unchanged content, refreshes stale-model vectors, never embeds empty content, and
reports per-chunk failures as counts so keyword retrieval is never broken.

JSON vector storage with in-Python cosine similarity is a small-scale fallback.
For larger datasets it should be replaced by a pgvector column and an indexed
similarity query. The embedding abstraction (provider, model, version, dimension)
is designed so a real external provider can be added later behind configuration
without changing callers.

### Hybrid

Combines keyword and semantic rankings with Reciprocal Rank Fusion (rank-based,
not raw score addition), then deduplicates to one result per page keeping the
strongest chunk for that page. `ranking_reason` reads: "Ranked by keyword and
semantic signals from real-derived page chunks." Filters (document_id,
document_type, text_extraction_status, page_min, page_max) are applied before
ranking.

## Checklist and finding scoped retrieval

`POST /projects/{project_id}/evidence-retrieval/checklist/{checklist_item_id}`
and `POST /projects/{project_id}/evidence-retrieval/findings/{finding_id}` run
hybrid chunk retrieval over real chunks. Checklist query text is built from the
requirement and expected evidence, with a soft boost from supporting document
hints. Finding query text is built from the title, evidence to find, and why it
matters. When no searchable chunks exist, the response states that indexed chunk
evidence is not available yet, never a false absence.

## Auto-link suggestions

`POST /projects/{project_id}/evidence-retrieval/suggest-links` scans real-derived
chunks and suggests likely checklist items and findings, populating
`related_checklist_items` and `related_findings`. These are reviewer-support
suggestions, not facts. The service does not assert that evidence satisfies a
checklist item, does not create or change findings, and does not change any human
review status.

Confidence limitation: the related arrays are list-of-id columns, so only the
suggested ids are persisted. Per-link confidence scores are returned in the route
response for the reviewer but are not persisted per link. A future scoring table
could persist them.

## Candidate save and promotion

Search results are saved as evidence candidates
(`POST /projects/{project_id}/evidence-candidates`). The saved
`candidate_status` is persisted from the request and the UI displays only the
status the backend returns. When a candidate supplies a page number without a
page id, the service resolves the matching DocumentPage so the candidate carries
a real `document_page_id`. Promotion
(`.../evidence-candidates/{candidate_id}/promote-to-draft-finding`) creates a
reviewer draft finding and a real page-level citation. Promotion is always
reviewer-initiated.

## Not-indexed versus no-match guardrail

"Not indexed" is never the same as "not found." A missing or no-match response is
only meaningful over content that was actually indexed, chunked, and searched.
Empty responses state that they are not a finding about document content, and the
distinct messages separate "indexed chunk evidence is not available yet" from "no
matching indexed text found."

## Retrieval quality harness

`app/services/retrieval_eval_service.py` evaluates keyword, semantic, and hybrid
retrieval over a small labeled query set and computes Recall@5, Precision@5, and
Mean Reciprocal Rank. `tests/test_retrieval_quality.py` builds a controlled
corpus, runs the harness, and asserts conservative thresholds that catch major
regressions without being brittle. The generated report is at
docs/PHASE_2_RETRIEVAL_QUALITY.md; regenerate it by running that test with
`CIVIL_WRITE_RETRIEVAL_REPORT=1`. The goal is measured behavior; semantic is not
required to beat keyword on every query.

## Frontend

The evidence search page offers a search source (real-derived chunk evidence or
indexed page text) and, for chunk evidence, a retrieval mode (hybrid, keyword,
semantic). Result cards show document name and type, page number and label, text
extraction status, candidate origin, excerpt, match terms, ranking score as
relevance, ranking reason, and chunk id. A semantic-only result shows that it has
no exact keyword terms. Save candidate and promote-to-draft-finding preserve
page-level citation context.

## Known limitations

* No database migration tooling; schema additions apply to fresh databases only.
* Embeddings are a deterministic local concept model and JSON-stored vectors with
  in-Python cosine similarity, suitable for demo scale only. pgvector and a real
  embedding model are the production path.
* Per-link suggestion confidence is not persisted, only returned at suggest time.
* The seeded chunk keyword search route and the page-text search route still
  exist alongside chunk retrieval; they are separate surfaces.

## Future build steps

* Add migration tooling, then a pgvector-backed embedding column and index.
* Add an external embedding provider behind configuration (backend only).
* Persist suggestion confidence in a dedicated table.
* Surface a per-document chunked and embedded status on the documents list.
