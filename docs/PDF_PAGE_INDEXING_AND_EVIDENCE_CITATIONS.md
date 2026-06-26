# PDF Page Indexing and Evidence Citations

This document describes the Sprint 2 PDF indexing pipeline and the reviewer
evidence citation workflow. Both are review-support only. Indexing is
deterministic and local, does not OCR, and never calls an external service.
Citations are reviewer-selected source references, not engineering conclusions.

## PDF indexing pipeline

Indexing is triggered manually for one document at a time
(`POST /api/v1/projects/{project_id}/documents/{document_id}/index-pdf`). The
service:

1. Confirms the document exists and belongs to the project.
2. Confirms the document is a PDF (by stored extension or content type).
3. Confirms an uploaded file path is recorded and the file exists on disk.
4. Sets the document to `indexing_started` and writes a
   `document_indexing_started` audit event.
5. Opens the file with pypdf. If the file cannot be opened at all, the document
   is set to `indexing_failed`, a `document_indexing_failed` event is written,
   and the request returns a safe error.
6. Counts pages and processes each page (see below).
7. Updates the document with page count, indexed timestamp, an extraction
   summary, an extraction warning count, and a processing status.
8. Writes a `document_indexed` audit event with counts and statuses only.

## Page records

Each page produces a `DocumentPage` row with a stable `document_page_id`, the
1-based `page_number`, a `page_label`, the extracted text (when available),
`text_extraction_status`, `text_extraction_method`, `char_count`, `word_count`,
`extraction_warnings`, and an `indexed_at` timestamp. Re-indexing a document
updates existing page rows in place, so indexing is idempotent.

## Text extraction from digital PDFs only

Text is read from the PDF's embedded text layer with pypdf. There is no OCR, so
scanned image pages produce no text. A page with no extractable text is a normal
outcome recorded as `no_extractable_text`, not an error and not a conclusion.

Per-page text extraction statuses: `not_indexed`, `indexing_started`,
`text_extracted`, `no_extractable_text`, `extraction_failed`,
`unsupported_file_type`, `needs_reviewer_review`.

## Extraction failure states

- A single page that raises during extraction is recorded with a page warning
  and `no_extractable_text`, and indexing continues with the remaining pages.
- A file that cannot be opened at all sets the document to `indexing_failed` and
  returns a safe error. The whole backend never crashes on a bad file.
- A non-PDF document, or a document with no uploaded file, is rejected before
  any indexing begins.

## Manual evidence citation workflow

A reviewer creates a citation from a page detail view or directly through the
API. The citation requires the project, finding, and document to exist. A
`document_page_id` or `page_number` may be provided to cite a specific page; the
service resolves the page record when possible. A `quoted_excerpt` is optional
and reviewer-selected.

Citation types: `reviewer_selected`, `manual_reference`,
`extracted_text_reference`, `seeded_demo_reference`.

Citation statuses: `draft`, `needs_reviewer_confirmation`, `reviewer_selected`,
`extraction_unavailable`, `page_reference_only`. There is intentionally no
verified or approved citation status.

## Finding-to-page citation workflow

Citations are listed per finding and per project. The finding detail page shows
all citations for a finding. The project evidence citations page lists every
citation with its finding, document, page, status, type, and reviewer note. A
citation never changes the finding's status to a final outcome.

## Audit events

Indexing and citation actions write audit events:
`document_indexing_started`, `document_indexed`, `document_indexing_failed`,
`document_page_text_extracted`, `document_page_no_extractable_text`,
`evidence_citation_created`, `evidence_citation_updated`, and
`evidence_citation_removed`. Audit metadata records counts, statuses, and
identifiers only. Extracted page text and raw server file paths are never
written to audit events.

## Limitations

- Digital PDF text extraction only; no OCR.
- No live AI retrieval or automated model findings.
- Citations are reviewer-selected evidence references, not engineering
  conclusions.
- Uploaded files remain on local storage unless deployment storage is
  configured.
- No real authentication yet; actions are attributed to the demo reviewer.

## Future OCR and retrieval work

A later sprint can add OCR for scanned pages, chunk and embed extracted page
text, and ground AI draft findings in the same page records with required
citations and human review, building directly on the page-level records and
citations introduced here.
