# Production Foundations Sprint 2: PDF Page Indexing and Evidence Citations

This sprint adds the first document-understanding layer for uploaded PDF files.
It indexes a real uploaded PDF into page-level review records, extracts embedded
text where the PDF carries a text layer, and lets a human reviewer cite an exact
page or section as evidence for a review-support finding.

The product moves from "documents are uploaded and registered" to "documents are
indexed into page-level review records that reviewers can cite."

Everything here is review-support only. Indexing is deterministic and local. It
does not OCR scanned pages, send content to any AI provider, approve plans,
certify compliance, verify CAD, validate design, declare a project safe, resolve
or close an issue, or make a final engineering decision. A citation is a
reviewer-selected source reference, not proof of correctness, and it never
changes a finding to a final outcome.

## What Sprint 2 adds

Backend:

- A `DocumentPage` model: one row per indexed PDF page with extracted text,
  extraction status, character and word counts, and warnings.
- An `EvidenceCitation` model: reviewer-selected, page-level citations linking a
  finding to a document page or section.
- Sprint 2 fields on `Document`: `indexed_at`, `text_extraction_status`,
  `text_extraction_summary`, `extraction_warning_count`.
- A `pdf_indexing_service` that opens an uploaded PDF with pypdf, counts pages,
  extracts text per page, records page records, updates the document, and writes
  audit events.
- Review-support vocabulary for text extraction statuses, document processing
  statuses, citation types, and citation statuses.
- API routes for indexing, reading pages, and managing citations.

Frontend:

- A PDF evidence API client (`lib/api/pdfEvidence.ts`).
- A document detail page with an Index PDF action, a page index view, and a page
  detail view with an extracted-text preview and a citation helper.
- A finding detail page listing evidence citations, and a project-level evidence
  citations page.
- Document list columns for processing status, page count, and text extraction.
- A homepage update describing Sprint 2.

## What remains demo-only

Brookside Meadows and every existing demo page are unchanged. Seeded documents
have no uploaded file, so they cannot be indexed; the UI shows "PDF indexing
requires an uploaded PDF file."

## What remains out of scope

OCR, live AI calls or retrieval, DWG parsing, GIS, Bluebeam, applicant portal
functionality, automated engineering calculations, geometry or design
validation, SSO, full authentication, and multi-tenant enterprise controls are
out of scope. Text extraction covers digital PDFs with an embedded text layer
only.

## How uploaded PDFs become indexed page records

1. A reviewer uploads a PDF through the Sprint 1 upload endpoint. The file is
   stored under a safe generated name with a sha256 checksum.
2. The reviewer opens the document detail page and clicks Index PDF pages.
3. The backend opens the file with pypdf, counts pages, and for each page
   extracts embedded text, computes character and word counts, captures any
   warnings, and writes a `DocumentPage` record.
4. The document is updated with the page count, indexed timestamp, extraction
   summary, and a processing status (`indexed_with_text`, `indexed_without_text`,
   or `indexed_with_warnings`).
5. Audit events record the start, each page outcome, and completion using counts
   and statuses only. Extracted text is never written to audit metadata.

## How reviewers create evidence citations

From a page detail view, a reviewer enters a finding ID and an optional section
label, quoted excerpt, and note, then creates a citation. The citation links the
finding to the document page. A citation to a page with no extractable text is
recorded as `page_reference_only`. A citation with no resolved page is recorded
as `extraction_unavailable`. Every citation starts under reviewer confirmation.

## How this differs from automated model conclusions

Indexing only extracts text that is already in the PDF. Citations are created by
a human reviewer who chooses the page and writes the note. Nothing is inferred,
scored, or concluded by a model. There are no AI drafts and no automated
findings in this sprint.

## How this prepares the app for later RAG

Page-level records with extracted text and stable page identifiers are the
substrate a later retrieval layer needs. A future sprint can chunk and embed
this text and ground AI draft findings in the same page records, with citations
that point to exactly these pages, while keeping the no-citation-rejection and
human-review rules.

## How to test the workflow locally

1. Start the backend: from `backend/`, run `uvicorn app.main:app --reload`.
2. Start the frontend: from the repository root, run `npm run dev`.
3. Create a project, then upload a PDF on the register page (Upload file).
4. Open the document, click Index PDF pages, then open a page.
5. Enter a finding ID (create one first under Reviewer findings) and create a
   citation. Review it on the finding detail and the project evidence citations
   pages, and see the audit events.
