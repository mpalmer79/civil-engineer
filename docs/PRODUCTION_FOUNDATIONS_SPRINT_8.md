# Production Foundations Sprint 8: Reviewer Response Package Issuance and Comment Letter Workflow

This sprint adds the first controlled reviewer output workflow on top of the
project, document, citation, checklist, access-control, storage, response matrix,
and resubmittal foundations from Sprints 1 through 7.

The product moves from "reviewers can track findings, checklist items, applicant
responses, resubmittals, and carried-forward review items" to "reviewers can
assemble a controlled response package, generate a reviewer-editable comment
letter draft, include selected matrix items and citations, issue a review-support
package record, and preserve a durable audit trail."

This sprint is about packaging reviewer-controlled communication. It is not about
final approval, legal compliance, issue closure, or automated engineering
decisions. A response package is a reviewer communication artifact. Issuing a
package records that a reviewer issued a communication. It does not approve a
project, certify compliance, verify CAD, validate design, declare a project safe,
resolve an issue, or close an issue.

Live demo: https://civil-engineer.up.railway.app/

## What Sprint 8 adds

Backend:

- New additive, seed-compatible models: `ReviewerResponsePackage`,
  `ReviewerResponsePackageItem`, `CommentLetterDraft`, and
  `ReviewerResponsePackageRevision`. These are distinct from the Phase 10 demo
  response package builder, which is preserved unchanged.
- A `reviewer_response_package_service` and a `comment_letter_service` that
  create packages, add reviewer-selected records as package items, update items,
  preview a package, mark a package ready for reviewer handoff, issue a package,
  create revisions, generate a deterministic comment letter draft, edit a draft,
  and preview a draft.
- Pydantic schemas and access-controlled routes under the existing project prefix
  at `reviewer-response-packages` and `comment-letter-drafts`. Reads require
  project read access; mutations require project reviewer access.
- Sprint 8 review-support vocabulary: package statuses, package types, package
  item source types, package item statuses, and comment letter draft statuses.
- Audit events: `response_package_created`, `response_package_item_added`,
  `response_package_item_updated`, `response_package_ready_for_handoff`,
  `response_package_issued`, `response_package_revision_created`,
  `comment_letter_draft_created`, `comment_letter_draft_updated`, and
  `comment_letter_ready_for_handoff`. Audit metadata records ids, statuses, and
  counts only, never full comment letter text, full applicant response text, full
  extracted page text, storage keys, raw paths, or secrets.

Frontend:

- API clients `lib/api/reviewerResponsePackages.ts` and
  `lib/api/commentLetters.ts`.
- Project-scoped pages: a response packages landing page, a package detail page,
  a package preview page, a comment letter draft page, and a comment letter
  preview page.
- Components: `CreateResponsePackageButton`, `AddToResponsePackageButton`,
  `AddMatrixItemsToPackagePanel`, `AddSourcesToPackagePanel`,
  `PackageItemActions`, `ResponsePackageWorkflow`, and `CommentLetterEditor`.
- Wiring into the project overview, response matrix detail, response matrix item
  detail, finding detail, and checklist item detail pages, plus a homepage
  paragraph describing Sprint 8.

## How this builds on Sprints 1 through 7

Sprint 1 created real project and finding records. Sprints 2 and 3 indexed PDFs,
added citations, and added evidence retrieval. Sprint 4 added checklist review.
Sprint 5 added authentication and access control. Sprint 6 added durable storage.
Sprint 7 added the response matrix and resubmittal workflow. Sprint 8 keeps all of
that and adds the layer where a reviewer collects those records into a controlled
response package and a comment letter draft for reviewer handoff. Access control,
audit attribution, storage security, and the review-support boundary are
unchanged.

## Why response package issuance matters in municipal review

A municipal stormwater review ends each round with a written communication to the
applicant: a comment letter that lists what the reviewer asks the applicant to
address. Today reviewers assemble that letter by hand from scattered findings and
notes. The response package gives that assembly structure: each comment traces to
a reviewer finding, checklist item, response matrix item, or citation, the letter
is generated from a fixed template, and the issued communication is recorded with
a durable audit trail and revision history.

## How response packages are assembled

A reviewer creates a response package, then adds reviewer-selected records to it:
response matrix items, findings, checklist items, citations, document references,
and manual reviewer notes. Each added record becomes a package item with a
reviewer comment, optional requested evidence, an optional applicant response
summary, and a review-support status. Items can be reordered, edited, included in
or excluded from the comment letter, and given a review-support status. Adding a
record never modifies the source record.

## How comment letter drafts are created from selected records

A reviewer generates a comment letter draft from the package. Generation is
deterministic and template-based. There are no live AI calls. The draft includes a
title, subject line, introduction, project summary, review scope, a comment block
built from the included package items, an optional resubmittal summary, and a
closing. Each section is reviewer-editable. A fixed review-support boundary
statement is rendered with every draft and preview and is never an editable
section.

## Why comment letters are reviewer-editable drafts

The generated text is a starting point, not a finished letter. The reviewer is
responsible for the wording sent to an applicant, so every section is editable and
every reviewer-entered field is checked against the prohibited-language guard to
keep the letter within the review-support boundary.

## Why issuance is a communication record, not final approval

Issuing a package records that a reviewer issued a communication. It stores who
issued it and when. It never sets an approved, certified, compliant, verified,
validated, resolved, or closed status, and it never decides whether the applicant
response satisfies engineering requirements.

## How revisions preserve prior records

Starting a revision increments the revision number, sets the package status to
revision started, and records a revision row capturing the prior status. The prior
issued record (issued by and issued at) is preserved, not overwritten, and prior
issued comment letter drafts are marked superseded rather than deleted.

## What remains demo-only

Brookside Meadows is a seeded public demo. A reviewer can assemble a package and a
comment letter draft against it for demonstration, clearly labeled as
review-support data. Seeded data is never described as extracted from real CAD,
PDF, GIS, or plan files. The Phase 10 demo response package builder is preserved
unchanged.

## What remains out of scope

Live AI calls, OCR, DWG parsing, GIS integrations, Bluebeam integrations,
automated engineering calculations, geometry or design validation, final approval
workflows, enterprise SSO, and a full applicant portal are out of scope. This
sprint is a reviewer communication-packaging foundation only.

## How to test the workflow locally

Backend (from the `backend` directory):

```
pip install -r requirements.txt pytest-cov
pytest --cov=app --cov-report=term-missing --cov-fail-under=90
```

The Sprint 8 tests live in `tests/test_reviewer_response_package.py`.

Frontend (from the repository root):

```
npm install
npm run typecheck
npm run lint
npm test
npm run build
```

The Sprint 8 frontend tests live in
`app/__tests__/responsePackagesClient.test.tsx` and
`app/__tests__/responsePackagesUi.test.tsx`.

Manual end-to-end: sign in, open a project, create reviewer findings or checklist
review items, create a response package, add records to it, preview the package,
generate a comment letter draft, edit the draft, preview the comment letter, mark
the package ready for reviewer handoff, issue the package, and start a revision.
Confirm a read-only user receives 403 on the mutations.

See [RESPONSE_PACKAGE_AND_COMMENT_LETTER_WORKFLOW.md](RESPONSE_PACKAGE_AND_COMMENT_LETTER_WORKFLOW.md)
for the workflow, [API_RESPONSE_PACKAGES.md](API_RESPONSE_PACKAGES.md) for the API
contract, and [COMMENT_LETTER_TEMPLATE_BOUNDARY.md](COMMENT_LETTER_TEMPLATE_BOUNDARY.md)
for the template boundary. The recommended next sprint is Production Foundations
Sprint 9: Reviewer Dashboard, Workload Management, and Operational Metrics.
