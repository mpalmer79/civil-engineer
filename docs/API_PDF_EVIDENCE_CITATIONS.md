# API: PDF Page Indexing and Evidence Citations

Routes added in Production Foundations Sprint 2. All paths are under the
`/api/v1` prefix. The frontend reads the backend origin from
`NEXT_PUBLIC_API_BASE_URL` (backend origin only, no `/api/v1` path) and appends
the `/api/v1` paths itself.

Professional boundary: every route is review-support only. No route OCRs,
approves plans, certifies compliance, verifies CAD, validates design, declares a
project safe, resolves or closes an issue, or makes a final engineering
decision. A citation is a reviewer-selected source reference, not proof of
correctness. User-provided citation text is rejected if it contains
final-decision wording. Responses never include raw server file paths, and audit
metadata never includes extracted page text.

## PDF indexing routes

### POST /api/v1/projects/{project_id}/documents/{document_id}/index-pdf

Indexes an uploaded PDF into page records and extracts embedded text. Rejects
non-PDF documents, documents with no uploaded file, and unreadable files (422).

Response (200):

```json
{
  "document_id": "doc_user_abc123",
  "page_count": 2,
  "pages_with_text": 2,
  "pages_without_text": 0,
  "warning_count": 0,
  "processing_status": "indexed_with_text",
  "text_extraction_status": "text_extracted",
  "indexed_at": "2026-06-26T00:00:00Z",
  "summary": "2 page(s) indexed: 2 with extractable text, 0 without. 0 page warning(s)."
}
```

## Document page routes

### GET /api/v1/projects/{project_id}/documents/{document_id}/pages

Lists indexed pages for a document, ordered by page number.

### GET /api/v1/projects/{project_id}/documents/{document_id}/pages/{page_number}

Returns one indexed page. 404 if the page does not exist.

```json
{
  "document_page_id": "docpage_abc123",
  "project_id": "proj_user_abc123",
  "document_id": "doc_user_abc123",
  "page_number": 1,
  "page_label": "Page 1",
  "extracted_text": "Outlet detail on page one",
  "text_extraction_status": "text_extracted",
  "text_extraction_method": "pypdf_text_layer",
  "char_count": 25,
  "word_count": 5,
  "extraction_warnings": [],
  "indexed_at": "2026-06-26T00:00:00Z"
}
```

## Evidence citation routes

### GET /api/v1/projects/{project_id}/findings/{finding_id}/citations

Lists citations for one finding.

### POST /api/v1/projects/{project_id}/findings/{finding_id}/citations

Creates a reviewer-selected evidence citation. Requires the project, finding,
and document to exist. Provide `document_page_id` or `page_number` to cite a
specific page. Writes an `evidence_citation_created` audit event.

Request:

```json
{
  "document_id": "doc_user_abc123",
  "page_number": 1,
  "section_label": "Outlet detail",
  "quoted_excerpt": "Outlet detail on page one",
  "reviewer_note": "Supports the missing outlet detail finding"
}
```

Response (201): the citation, including `citation_type`, `citation_status`,
`page_number`, and `document_page_id`.

### GET /api/v1/projects/{project_id}/evidence-citations

Lists every citation for the project.

### PATCH /api/v1/projects/{project_id}/findings/{finding_id}/citations/{citation_id}

Updates a citation's section label, quoted excerpt, reviewer note, status, or
type. Writes an `evidence_citation_updated` audit event.

### DELETE /api/v1/projects/{project_id}/findings/{finding_id}/citations/{citation_id}

Removes a citation. Writes an `evidence_citation_removed` audit event and returns
`{"deleted": true, "evidence_citation_id": "..."}`.

## Status values

Document processing statuses: `registered`, `uploaded`, `intake_pending`,
`metadata_recorded`, `indexing_pending`, `indexing_started`, `indexed_with_text`,
`indexed_without_text`, `indexed_with_warnings`, `indexing_failed`,
`parsing_not_available`, `needs_reviewer_review`.

Text extraction statuses: `not_indexed`, `indexing_started`, `text_extracted`,
`no_extractable_text`, `extraction_failed`, `unsupported_file_type`,
`needs_reviewer_review`.

Citation types: `reviewer_selected`, `manual_reference`,
`extracted_text_reference`, `seeded_demo_reference`.

Citation statuses: `draft`, `needs_reviewer_confirmation`, `reviewer_selected`,
`extraction_unavailable`, `page_reference_only`.

## Professional-boundary notes

There is intentionally no verified or approved citation status and no OCR. A
`no_extractable_text` page is a normal outcome, not an error. The Sprint 1 manual
evidence-reference endpoint
(`POST /api/v1/findings/{finding_id}/evidence-references`) remains available;
the Sprint 2 `EvidenceCitation` model adds page-level, indexing-aware citations
alongside it.
