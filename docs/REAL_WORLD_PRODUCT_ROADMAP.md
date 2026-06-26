# Real-World Product Roadmap

This document is the source-of-truth roadmap for Civil Engineer AI as it moves
from a controlled portfolio demo toward a real-world stormwater submission
review-support system for small municipal engineering teams.

## 1. Product positioning

Civil Engineer AI is a stormwater submission review-support and
evidence-organization system for municipal reviewers and consulting engineers.
It helps a human reviewer organize evidence, draft review-support findings,
track review workflow, and prepare reviewer-controlled response language.

Civil Engineer AI is not:

- a permitting system
- a final approval system
- a Professional Engineer replacement
- a CAD validation engine
- a design verification system
- a generic chatbot over plans

Every output is review-support only. The system does not approve plans, certify
compliance, stamp drawings, verify CAD, validate design, declare a project safe,
make final engineering decisions, or close or resolve issues. There is no action
named approve.

## 2. Current demo baseline

The seeded Brookside Meadows fixture demonstrates the review-support workflow
end to end:

- Brookside Meadows synthetic review fixture
- seeded documents
- checklist-driven review
- planted review-support findings
- document chunks and evidence links
- review packet builder
- workflow board
- response package builder
- review cycles and resubmittal concepts
- CAD intake and DXF metadata parsing
- audit trail concept
- deterministic mock AI by default
- human-review boundary language throughout

## 3. Production gap

The gap between the demo and a real-world trusted engineering records system
includes:

- real project creation
- authentication and roles (later)
- tenant separation (later)
- a persistent database
- durable file storage
- real file uploads
- PDF ingestion (later)
- page-level citations (later)
- reviewer-owned findings
- immutable audit events
- jurisdiction-specific rule packs (later)
- applicant response workflow (later)
- production security (later)

## 4. MVP direction

The first real-world MVP is:

Real Project Intake + Persistent Review Records.

A reviewer can create a real project record, register or upload documents, view
those documents, create a review-support finding tied to the project, attach
evidence metadata where available, and see audit events showing what happened,
while Brookside Meadows remains a seeded demo fixture.

## 5. Phased roadmap

### Phase 1: Real Project Records

- real project creation
- persistent project model
- durable document metadata
- upload registration
- reviewer-created findings
- basic evidence references
- audit events from real actions
- Brookside Meadows retained as demo mode

### Phase 2: Evidence-Grounded Review

- PDF ingestion (delivered in Sprint 2: page indexing and text extraction)
- page-level citations (delivered in Sprint 2: reviewer-selected citations)
- document chunking from real files
- hybrid retrieval
- no-citation rejection for AI drafts
- prompt and model versioning
- human review queue
- expanded evaluation cases

Sprint 2 delivered the foundation of Phase 2: uploaded PDFs are indexed into
page-level review records with extracted text, and reviewers can cite exact
pages or sections as evidence for findings. Chunking, retrieval, and AI draft
findings remain ahead.

### Phase 3: Jurisdiction and Resubmittal Workflow

- configurable rule packs
- jurisdiction-specific checklists
- applicant response matrix
- resubmittal comparison
- issue carry-forward for reviewer confirmation
- comment letter workflow

### Phase 4: Production Readiness

- authentication
- role-based access
- tenant separation
- object storage
- malware scanning
- backups
- monitoring
- queue workers
- SSO (later)
- GIS, Bluebeam, and permit integrations (later)
- legal and professional governance

## 6. Current sprint

Production Foundations Sprint 8: Reviewer Response Package Issuance and Comment
Letter Workflow.

This sprint adds the first controlled reviewer output workflow. Reviewers can
assemble selected findings, checklist items, response matrix items, and citations
into a controlled response package, generate a deterministic, reviewer-editable
comment letter draft, preview the package, issue it as a reviewer communication
record, and preserve a revision history with a durable audit trail. Package
issuance records a reviewer communication only. It does not approve a project,
certify compliance, validate design, resolve an issue, or close an issue, and it
does not change the review-support boundary. See
[PRODUCTION_FOUNDATIONS_SPRINT_8.md](PRODUCTION_FOUNDATIONS_SPRINT_8.md),
[RESPONSE_PACKAGE_AND_COMMENT_LETTER_WORKFLOW.md](RESPONSE_PACKAGE_AND_COMMENT_LETTER_WORKFLOW.md),
[API_RESPONSE_PACKAGES.md](API_RESPONSE_PACKAGES.md), and
[COMMENT_LETTER_TEMPLATE_BOUNDARY.md](COMMENT_LETTER_TEMPLATE_BOUNDARY.md).

Sprint 7 (complete) added a reviewer-controlled applicant response matrix and a
resubmittal collaboration workflow: reviewers can organize findings and checklist
review items into a response matrix, record applicant responses for reviewer
review, register resubmittal rounds, link documents to a round, and carry items
forward across review rounds. See
[PRODUCTION_FOUNDATIONS_SPRINT_7.md](PRODUCTION_FOUNDATIONS_SPRINT_7.md),
[APPLICANT_RESPONSE_MATRIX.md](APPLICANT_RESPONSE_MATRIX.md),
[RESUBMITTAL_COLLABORATION_WORKFLOW.md](RESUBMITTAL_COLLABORATION_WORKFLOW.md), and
[API_RESPONSE_MATRIX_AND_RESUBMITTALS.md](API_RESPONSE_MATRIX_AND_RESUBMITTALS.md).

Sprint 6 (complete) replaced local-only uploaded file persistence with a storage
provider abstraction that supports local development storage and S3-compatible
object storage for deployment. Storage credentials stay on the backend, file
download is access controlled, and PDF indexing reads files through the storage
layer. See [PRODUCTION_FOUNDATIONS_SPRINT_6.md](PRODUCTION_FOUNDATIONS_SPRINT_6.md),
[STORAGE_PROVIDER_ABSTRACTION.md](STORAGE_PROVIDER_ABSTRACTION.md), and
[API_FILE_STORAGE.md](API_FILE_STORAGE.md).

Sprint 5 (complete) added the first real authentication and access-control
foundation: real users can sign in, belong to organizations, hold reviewer or
admin roles, and access only the projects they are permitted to view or act on,
with real audit attribution. See
[PRODUCTION_FOUNDATIONS_SPRINT_5.md](PRODUCTION_FOUNDATIONS_SPRINT_5.md),
[AUTHENTICATION_AND_ACCESS_CONTROL.md](AUTHENTICATION_AND_ACCESS_CONTROL.md), and
[API_AUTH_AND_ACCESS_CONTROL.md](API_AUTH_AND_ACCESS_CONTROL.md).

Sprint 4 (complete) added the first reusable, versioned checklist-review
foundation: a reviewer can apply a starter stormwater rule pack to a project as a
working checklist, search indexed evidence against each checklist requirement,
track reviewer-controlled checklist evidence status, link citations, and create
draft findings from checklist items. See
[PRODUCTION_FOUNDATIONS_SPRINT_4.md](PRODUCTION_FOUNDATIONS_SPRINT_4.md),
[CHECKLIST_RULE_PACK_FOUNDATION.md](CHECKLIST_RULE_PACK_FOUNDATION.md), and
[API_CHECKLIST_REVIEW.md](API_CHECKLIST_REVIEW.md).

Sprint 3 (complete) added a deterministic, local evidence retrieval layer over
the Sprint 2 indexed PDF page text, plus a reviewer-controlled queue of evidence
candidates that a human reviewer can promote into draft review-support findings.
See [PRODUCTION_FOUNDATIONS_SPRINT_3.md](PRODUCTION_FOUNDATIONS_SPRINT_3.md),
[EVIDENCE_RETRIEVAL_AND_DRAFT_QUEUE.md](EVIDENCE_RETRIEVAL_AND_DRAFT_QUEUE.md),
and [API_EVIDENCE_RETRIEVAL.md](API_EVIDENCE_RETRIEVAL.md).

Sprint 2 (complete) added the first document-understanding layer: uploaded PDFs
are indexed into page-level review records with extracted text, and reviewers can
cite exact pages or sections as evidence for findings. See
[PRODUCTION_FOUNDATIONS_SPRINT_2.md](PRODUCTION_FOUNDATIONS_SPRINT_2.md) and
[PDF_PAGE_INDEXING_AND_EVIDENCE_CITATIONS.md](PDF_PAGE_INDEXING_AND_EVIDENCE_CITATIONS.md).

Sprint 1 (complete) delivered the real-world foundation layer: user-created
project records, document registration and file upload, reviewer-created
findings, basic evidence references, and durable audit events, with Brookside
Meadows preserved as a seeded demo fixture. See
[PRODUCTION_FOUNDATIONS_SPRINT_1.md](PRODUCTION_FOUNDATIONS_SPRINT_1.md).

The recommended next sprint is Production Foundations Sprint 9: Reviewer Dashboard,
Workload Management, and Operational Metrics.

## 7. Out of scope

The following are intentionally not included yet:

- live AI calls
- single sign-on
- full authentication and role-based access
- tenant separation
- DWG parsing
- OCR
- GIS integrations
- Bluebeam integrations
- applicant portal functionality
- automated engineering calculations
- geometry or design validation
- PDF parsing and page-level citations (Phase 2)
- jurisdiction rule packs (Phase 3)

A clearly labeled demo reviewer identity stands in for real authentication. It
grants no access and will be replaced when authentication lands.
