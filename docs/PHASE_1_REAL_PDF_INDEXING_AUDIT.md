# Phase 1: Real PDF Indexing Implementation Map (Findings Only)

This document is a findings-only audit of the existing PDF indexing, document
upload and storage, page records, and evidence retrieval readiness in the
civil-engineer repository. It changes no application behavior. Its purpose is
to let a reviewer know exactly what already exists, what is real, what is
stubbed or seeded, what is missing, and what should be built next.

Scope note: this audit follows the professional boundary. The system is a
review-support and evidence-organization system. Nothing described here
approves plans, certifies compliance, verifies CAD, validates design, or
declares a project safe. Indexing and retrieval produce review-support
candidates for a human reviewer, not conclusions.

## 1. Existing files and routes

### Backend models (backend/app/db/models.py)

| Model | Location | Table | Role |
| --- | --- | --- | --- |
| `Document` | line 121 | `documents` | Document intake, storage, and indexing state |
| `DocumentPage` | line 202 | `document_pages` | Page-level review records with extracted text |
| `EvidenceCitation` | line 242 | `evidence_citations` | Reviewer-selected page-level citation for a finding |
| `DocumentChunk` | line 547 | `document_chunks` | Short retrievable excerpts (seeded only, see section 3) |
| `FindingSource` | line 579 | `finding_sources` | Manual evidence reference linking a finding to a document |
| `EvidenceCandidate` | line 660 | `evidence_candidates` | Reviewer queue item produced by evidence retrieval search |
| `RetrievalQuery` | line 617 | `retrieval_queries` | Recorded retrieval search history |

### Backend routes

| Route | Method and path | File |
| --- | --- | --- |
| List documents | `GET /projects/{project_id}/documents` | backend/app/api/v1/documents.py |
| Register document | `POST /projects/{project_id}/documents/register` | backend/app/api/v1/documents.py |
| Upload document | `POST /projects/{project_id}/documents/upload` | backend/app/api/v1/documents.py |
| Get document | `GET /documents/{document_id}` | backend/app/api/v1/documents.py |
| Download document | `GET /projects/{project_id}/documents/{document_id}/download` | backend/app/api/v1/file_storage.py |
| Storage status | `GET /projects/{project_id}/documents/{document_id}/storage-status` | backend/app/api/v1/file_storage.py |
| Storage health | `GET /storage/health` | backend/app/api/v1/file_storage.py |
| Index PDF | `POST /projects/{project_id}/documents/{document_id}/index-pdf` | backend/app/api/v1/pdf_evidence.py |
| List pages | `GET /projects/{project_id}/documents/{document_id}/pages` | backend/app/api/v1/pdf_evidence.py |
| Get page | `GET /projects/{project_id}/documents/{document_id}/pages/{page_number}` | backend/app/api/v1/pdf_evidence.py |
| Finding citations | `GET/POST .../findings/{finding_id}/citations` and `PATCH/DELETE .../citations/{citation_id}` | backend/app/api/v1/pdf_evidence.py |
| Project citations | `GET /projects/{project_id}/evidence-citations` | backend/app/api/v1/pdf_evidence.py |
| Chunk listing | `GET /projects/{project_id}/chunks`, `GET /documents/{document_id}/chunks`, `GET /chunks/{chunk_id}` | backend/app/api/v1/chunks.py |
| Chunk keyword search | `GET /projects/{project_id}/search` | backend/app/api/v1/retrieval.py |
| Checklist and finding evidence | `GET /projects/{project_id}/checklist/{checklist_item_id}/evidence`, `GET /projects/{project_id}/findings/{finding_id}/evidence` | backend/app/api/v1/retrieval.py |
| Evidence retrieval search | `POST /projects/{project_id}/evidence-retrieval/search` | backend/app/api/v1/evidence_retrieval.py |
| Evidence candidate queue and promotion | candidate create, update, dismiss, and promote-to-draft-finding routes | backend/app/api/v1/evidence_retrieval.py |

All routers are registered in backend/app/api/routes.py.

### Backend services

| Service | File | Role |
| --- | --- | --- |
| Real intake | backend/app/services/real_intake_service.py | Register and upload documents, store files, write audit events |
| PDF indexing | backend/app/services/pdf_indexing_service.py | Index uploaded PDF into pages, extract text, manage citations |
| Storage | backend/app/services/storage/storage_service.py with local_storage.py and s3_storage.py | Save, read, existence, size, and health for document files |
| Document read | backend/app/services/document_service.py | List and get documents |
| Chunk retrieval | backend/app/services/retrieval_service.py | Keyword and metadata ranking over seeded chunks |
| Evidence retrieval | backend/app/services/evidence_retrieval_service.py | Deterministic search over real indexed page text, candidate queue, promotion |

### Frontend

| Area | File |
| --- | --- |
| Document register and upload form | components/DocumentRegisterForm.tsx |
| Index PDF control | components/IndexPdfButton.tsx |
| Documents list page | app/projects/[projectId]/documents/page.tsx |
| Register page | app/projects/[projectId]/documents/register/page.tsx |
| Document detail page | app/projects/[projectId]/documents/[documentId]/page.tsx |
| Page list and page detail | app/projects/[projectId]/documents/[documentId]/pages/page.tsx and pages/[pageNumber]/page.tsx |
| Evidence search page | app/projects/[projectId]/evidence-search/page.tsx |
| Project document API client | lib/api/realProjects.ts (`listProjectDocuments`, `getProjectDocument`, `registerProjectDocument`, `uploadProjectDocument`) |
| PDF evidence API client | lib/api/pdfEvidence.ts (`indexPdfDocument`, `listDocumentPages`, `getDocumentPage`, citation functions) |
| Evidence retrieval API client | lib/api/evidenceRetrieval.ts |
| Legacy single-project client | lib/api/documents.ts (demo fallback, see section 3) |

### Backend tests already covering this area

- backend/tests/test_pdf_indexing.py
- backend/tests/test_evidence_retrieval.py
- backend/tests/test_file_storage.py
- backend/tests/test_retrieval.py
- backend/tests/test_real_intake.py

## 2. What is already real

The following behavior reads or writes real records from real uploaded files.

1. Document registration. `register_document` records intake metadata and emits
   a `document_registered` audit event. `processing_status` is set to
   `metadata_recorded` and `upload_status` to `not_uploaded`.

2. Document upload and storage. `upload_document` validates the file extension
   and size against configured limits, computes a sha256 checksum, and stores
   the bytes through the configured storage provider (local filesystem or
   S3-compatible). Only a safe generated storage key is recorded. The raw
   filesystem path and any object storage credentials are never returned in a
   response or written to audit metadata. Rejected uploads emit a
   `document_upload_rejected` event and store nothing.

3. Storage provider abstraction. backend/app/services/storage selects local or
   S3 from `STORAGE_PROVIDER`. It provides save, read, existence, size, and
   health helpers. Reading falls back to a legacy `storage_path` for older
   uploads. pypdf 6.14.2 and boto3 1.34.144 are real dependencies in
   backend/requirements.txt.

4. Download and storage status. `GET .../download` streams the stored bytes,
   increments `download_count`, updates `last_downloaded_at`, and writes a
   `document_downloaded` event, or returns 404 and records
   `document_file_unavailable` when the file is missing. `GET .../storage-status`
   re-checks file availability and reports it without exposing internal paths.

5. Real PDF page indexing. `index_pdf_document` loads the stored PDF bytes
   through the storage provider, opens them with pypdf, and creates one
   `DocumentPage` per page. For each page it extracts the embedded text layer
   where one is present, records `text_extraction_status` of `text_extracted`
   or `no_extractable_text`, and stores char count, word count, and per-page
   extraction warnings. Re-indexing is idempotent through `_upsert_page`.
   Document-level rollups (`page_count`, `indexed_at`, `processing_status`,
   `text_extraction_status`, `extraction_warning_count`,
   `text_extraction_summary`) are written, and audit events are emitted for
   start, file load, per-page result, and completion. The summary records
   counts and statuses only; extracted page text and raw file paths are never
   written to audit events.

6. Page records and reads. `GET .../pages` and `GET .../pages/{page_number}`
   return real `DocumentPage` rows produced by indexing.

7. Page-level evidence citations. A reviewer can create, list, update, and
   delete `EvidenceCitation` rows that point at a document and an indexed page.
   Default citation status is chosen safely (for example `page_reference_only`
   when the page has no extractable text). Prohibited language is rejected on
   reviewer-entered text fields.

8. Evidence retrieval over real indexed text. `search_project_evidence` in
   evidence_retrieval_service.py ranks real `DocumentPage` rows whose
   `text_extraction_status` is `text_extracted`. The results feed a
   reviewer-controlled `EvidenceCandidate` queue and a promote-to-draft-finding
   flow under human review. This path operates on real uploaded and indexed
   content.

9. Frontend upload, index, and page review. DocumentRegisterForm supports both
   register and upload modes. IndexPdfButton triggers indexing. The document
   detail page gates indexing on a stored file and surfaces page records. The
   API clients in lib/api/realProjects.ts and lib/api/pdfEvidence.ts call the
   real project-scoped backend routes.

## 3. What is stubbed or seeded

1. DocumentChunk is seeded only. `DocumentChunk` rows are created exclusively by
   backend/app/db/seed_evidence.py (`db.add_all(models.DocumentChunk(**chunk)
   for chunk in CHUNKS)`). The model docstring states it seeds synthetic chunks
   rather than parsing real documents. No code path converts a real indexed
   `DocumentPage` into `DocumentChunk` rows.

2. Chunk keyword search covers seeded chunks only. `retrieval_service.search`
   and the `GET /projects/{project_id}/search` route rank `DocumentChunk` rows.
   Because real uploads never produce chunks, a real uploaded and indexed
   document does not appear in this chunk-based search route. Real indexed text
   is searchable only through the separate evidence retrieval route described in
   section 2 item 8.

3. Two parallel retrieval paths exist. The chunk-based path
   (retrieval_service plus retrieval.py, seeded data) and the page-based path
   (evidence_retrieval_service plus evidence_retrieval.py, real indexed pages)
   are independent. They are not unified behind one search surface.

4. Legacy single-project document client. lib/api/documents.ts uses a hardcoded
   `PROJECT_ID` and returns static demo documents from data/documents.ts when
   the backend does not respond. This is a demo fallback, not the project-scoped
   path used by the documents UI under app/projects/[projectId].

## 4. What is missing

1. No chunking of real indexed page text. There is no service that reads
   `DocumentPage.extracted_text` for a real document and produces
   `DocumentChunk` rows (or any chunk-equivalent records) with page numbers,
   section headings, and keywords. This is the central gap between real indexing
   and the chunk-based retrieval surface.

2. No unified search over real content. There is no single search route that
   covers both seeded chunks and real indexed pages, so a reviewer cannot search
   all available review-support evidence from one call.

3. No OCR. Indexing reads embedded text layers only. Scanned or image-only PDF
   pages are recorded as `no_extractable_text`. This is intentional and out of
   scope for this pass.

4. No vector or embedding search. There is no pgvector, no embedding model, and
   no semantic search. Retrieval is keyword and metadata based. This is
   intentional and out of scope for this pass.

5. No database migration framework. backend/app/db/database.py initializes
   schema with `Base.metadata.create_all`. There is no Alembic or other
   migration tooling. New columns on existing tables would not be applied to an
   existing database automatically.

## 5. Risks

1. Schema evolution risk. With `create_all` only, adding columns to existing
   tables (for example new chunk fields) will not migrate an already-populated
   database. Any future chunk pipeline that extends existing tables needs a
   migration plan, or it risks silent schema drift.

2. Reviewer confusion between two retrieval paths. Because the chunk-based
   `GET /projects/{project_id}/search` route returns seeded data only, a
   reviewer searching a real uploaded document there will see nothing and may
   conclude the document is empty. Clear labeling or unification is needed.

3. Seeded data must stay labeled. Seeded chunks are acceptable review-support
   data, but they must not be presented as extracted from real uploaded files.
   Any future chunk pipeline must keep seeded and real chunks distinguishable
   (for example a source mode field).

4. Professional boundary in user-facing strings. Indexing and retrieval text
   already uses review-support language. Any new feature must keep this and must
   not introduce approved, certified, validated, verified, compliant, or safe in
   user-facing strings.

5. Large file and many-page handling. Indexing reads the full file into memory
   and iterates every page synchronously inside the request. Very large PDFs
   could make the index-pdf request slow. This is acceptable for current demo
   scale but worth noting before real-world volumes.

## 6. Recommended PR sequence

Each step is small, reversible, and keeps existing behavior intact. No step in
this pass adds OCR, embeddings, pgvector, migrations, or frontend changes; those
are listed where they would belong in later phases.

1. PR 1 (implemented): Real chunk pipeline from indexed pages (backend, behind
   existing models). `backend/app/services/page_chunking_service.py` reads real
   `DocumentPage.extracted_text` for an indexed document and produces
   `DocumentChunk` rows with page number, a simple section heading heuristic, and
   keywords. It is exposed as an explicit route,
   `POST /projects/{project_id}/documents/{document_id}/chunk-pages`, and covered
   by `backend/tests/test_page_chunking.py`. It only chunks pages whose
   `text_extraction_status` is `text_extracted` with non-empty text, never spans
   pages, and is idempotent. The existing seeded chunk path is unchanged.

   Provenance limitation carried into PR 2: the `DocumentChunk` table has no
   provenance column, and PR 1 did not add one. Real-derived chunks are marked by
   a `chunk_id` prefix (`rdc_`). Re-running deletes and replaces only chunks with
   that prefix for the same document, so seeded chunks are never deleted. A real
   provenance column remains the work of PR 2.

2. PR 2: Mark chunk provenance. Add a source mode or origin field so seeded
   chunks and real-derived chunks are distinguishable in storage and in API
   responses. This addresses the seeded-versus-real labeling risk before any
   search unification. If this touches an existing table, pair it with the
   migration decision in PR 4.

3. PR 3: Unify or clearly separate the search surfaces. Either extend the
   chunk-based search to include real-derived chunks, or document and label the
   two routes so a reviewer knows which covers seeded demo data and which covers
   real indexed content. Keep all result framing as review-support candidates.

4. PR 4: Migration tooling decision. Introduce a migration approach (for
   example Alembic) before any further schema changes to existing tables, so the
   chunk provenance field and future fields apply cleanly to existing databases.

5. PR 5 (later phase, not this pass): Frontend search over real content. Once
   the backend surfaces real-derived chunks, add or update the evidence search
   UI to let a reviewer search real indexed content and open the cited page.

6. PR 6 (later phase, not this pass): OCR and semantic retrieval. Only if a
   future phase requests it, add OCR for scanned pages and embedding or vector
   search. These remain out of scope until explicitly requested.

## 7. Definition of done check

A reviewer reading this document can see that document upload, storage,
download, storage status, real PDF page indexing, page records, page-level
citations, and a real page-text evidence retrieval path already exist and work
on real files. The one structural gap for real PDF indexing readiness is that
real indexed page text is never converted into chunks, so the chunk-based search
route covers seeded data only. The recommended next implementation is the real
chunk pipeline in PR 1, followed by provenance labeling and search clarity.
