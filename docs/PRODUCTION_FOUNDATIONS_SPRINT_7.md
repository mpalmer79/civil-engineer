# Production Foundations Sprint 7: Applicant Response Matrix and Resubmittal Collaboration Workflow

> Historical record. This document describes a completed build phase and is
> not current implementation guidance. See docs/README.md for the current
> documentation index.

This sprint adds a reviewer-controlled applicant response matrix and a
resubmittal collaboration workflow on top of the real project, document,
citation, checklist, access-control, and storage foundations from Sprints 1
through 6.

The product moves from "reviewers can create draft findings, citations,
checklist reviews, and response-ready records" to "reviewers can organize
findings into a response matrix, record applicant responses, register
resubmittals, compare response status across review rounds, and carry forward
items that still need reviewer confirmation."

This sprint is about organizing applicant collaboration for reviewer review. It
does not change the engineering-review boundary. An applicant response is
recorded for reviewer review, never as proof and never as a final outcome.
Carry-forward means continued review, not resolution. Civil Engineer AI still
does not approve plans, certify compliance, verify CAD, validate design, declare
a project safe, or replace a licensed Professional Engineer.

Live demo: https://civil-engineer.up.railway.app/

## What Sprint 7 adds

Backend:

- New models: `ResponseMatrix`, `ResponseMatrixItem`, `ResubmittalRound`, and
  `MatrixItemDocumentLink`. All are additive and seed-compatible. They store the
  source finding, checklist item, or citation id so existing records are not
  modified.
- A `response_matrix_service` and a `resubmittal_service` that create matrices,
  add findings and checklist review items as matrix items, record applicant
  responses, link supporting documents, carry items forward, register
  resubmittal rounds, link round documents, and summarize a round.
- Pydantic schemas and access-controlled routes under the existing project
  prefix. Reads require project read access; mutations require project reviewer
  access.
- Sprint 7 safety vocabulary: review-support status sets for matrix status,
  applicant response status, reviewer follow-up status, carry-forward status,
  resubmittal round status, and matrix link type. Free-text fields are checked
  against the prohibited-language guard.
- Audit events: `response_matrix_created`, `response_matrix_item_added`,
  `response_matrix_item_updated`, `applicant_response_recorded`,
  `response_document_linked`, `response_matrix_item_carried_forward`,
  `resubmittal_round_registered`, `resubmittal_document_linked`, and
  `resubmittal_items_carried_forward`. Audit metadata records a response length,
  never the full applicant response text, and never a raw storage path, storage
  key, signed URL, or any credential.

Frontend:

- API clients `lib/api/responseMatrix.ts` and `lib/api/resubmittals.ts`.
- Project-scoped pages: a response matrix landing page, a matrix detail page
  with the item table, a matrix item detail page with reviewer actions, a
  resubmittal rounds landing page, and a resubmittal round detail page.
- Components: `CreateResponseMatrixButton`, `MatrixItemActions`,
  `AddToResponseMatrixButton`, `RegisterResubmittalRound`, and
  `LinkDocumentToResubmittalRound`.
- Wiring into the finding detail, checklist item detail, document detail, and
  project overview pages, plus a homepage paragraph describing Sprint 7.

## How this builds on Sprints 1 through 6

Sprint 1 created real project and finding records. Sprint 2 indexed PDFs and
added citations. Sprint 3 added evidence retrieval and a draft finding queue.
Sprint 4 added checklist-driven review. Sprint 5 added authentication and
project access control. Sprint 6 added durable file storage. Sprint 7 keeps all
of that and adds the layer where a reviewer organizes those findings and
checklist items into a response matrix, records what the applicant said back,
and tracks each item across resubmittal rounds. Access control, audit
attribution, and the review-support boundary are unchanged.

## Why a response matrix and resubmittal workflow matter

Real plan review is a multi-round conversation. A reviewer issues review-support
comments, the applicant responds with revised plans and narrative, and the
reviewer checks each response against the original concern across several rounds.
Without structure, that history is scattered across emails and PDFs. The response
matrix gives each comment a row, a recorded applicant response, a reviewer
follow-up status, and a carry-forward state, so the reviewer can see at a glance
what still needs confirmation in the next round.

## What an applicant response is and is not

An applicant response recorded in the matrix is a reviewer-entered record of what
the applicant submitted, kept for reviewer review. It is not proof that the
concern is satisfied, not a compliance determination, and not a final outcome.
The reviewer follow-up status and the carry-forward status describe reviewer
workflow state. Carrying an item forward keeps it under review in the next round;
it does not resolve or close it.

## What remains demo-only

Brookside Meadows is a seeded public demo. A reviewer can create a response
matrix and resubmittal rounds against it for demonstration, clearly labeled as
review-support data. Seeded data is never described as extracted from real CAD,
PDF, GIS, or plan files.

## What remains out of scope

An applicant-facing portal, applicant authentication, automated response
adequacy scoring, live AI calls, OCR, DWG or DXF parsing changes, GIS, automated
engineering calculations, geometry or design validation, and any final approval
or closure workflow are out of scope. This sprint is a reviewer-side
collaboration-tracking foundation only.

## How to test locally

Backend (from the `backend` directory):

```
pip install -r requirements.txt pytest-cov
pytest --cov=app --cov-report=term-missing --cov-fail-under=90
```

The Sprint 7 tests live in `tests/test_response_matrix.py`.

Frontend (from the repository root):

```
npm install
npm run typecheck
npm run lint
npm test
npm run build
```

The Sprint 7 frontend tests live in `app/__tests__/responseMatrixClient.test.tsx`
and `app/__tests__/responseMatrixUi.test.tsx`.

Manual end-to-end: sign in, open a project, create reviewer findings or checklist
review items, create a response matrix, add items to it, record an applicant
response, set a reviewer follow-up status, carry an item forward, register a
resubmittal round, and link a document to the round. Confirm a read-only user
receives 403 on the mutations.

See [APPLICANT_RESPONSE_MATRIX.md](APPLICANT_RESPONSE_MATRIX.md) for the response
matrix design, [RESUBMITTAL_COLLABORATION_WORKFLOW.md](RESUBMITTAL_COLLABORATION_WORKFLOW.md)
for the resubmittal workflow, and
[API_RESPONSE_MATRIX_AND_RESUBMITTALS.md](API_RESPONSE_MATRIX_AND_RESUBMITTALS.md)
for the API contract. The recommended next sprint is Production Foundations
Sprint 8: Reviewer Response Package Issuance and Comment Letter Workflow.
