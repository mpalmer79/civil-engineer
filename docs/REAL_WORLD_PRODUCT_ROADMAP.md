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

Production Foundations Sprint 2: PDF Page Indexing and Evidence Citations.

This sprint adds the first document-understanding layer: uploaded PDFs are
indexed into page-level review records with extracted text, and reviewers can
cite exact pages or sections as evidence for findings. See
[PRODUCTION_FOUNDATIONS_SPRINT_2.md](PRODUCTION_FOUNDATIONS_SPRINT_2.md) and
[PDF_PAGE_INDEXING_AND_EVIDENCE_CITATIONS.md](PDF_PAGE_INDEXING_AND_EVIDENCE_CITATIONS.md).

Sprint 1 (complete) delivered the real-world foundation layer: user-created
project records, document registration and file upload, reviewer-created
findings, basic evidence references, and durable audit events, with Brookside
Meadows preserved as a seeded demo fixture. See
[PRODUCTION_FOUNDATIONS_SPRINT_1.md](PRODUCTION_FOUNDATIONS_SPRINT_1.md).

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
