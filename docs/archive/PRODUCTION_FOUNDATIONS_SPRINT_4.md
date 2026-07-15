# Production Foundations Sprint 4: Checklist-Driven Evidence Review and Rule Pack Foundation

> Historical record. This document describes a completed build phase and is
> not current implementation guidance. See docs/README.md for the current
> documentation index.

This sprint adds the first reusable, versioned checklist-review foundation for
real projects. A reviewer can apply a starter stormwater rule pack to a project
as a working checklist, search indexed evidence against each checklist
requirement, track reviewer-controlled checklist evidence status, link
citations, and create draft findings from checklist items.

The product moves from "reviewers can search project evidence and promote
candidates into draft findings" to "reviewers can apply a structured stormwater
checklist to a real project, search evidence against specific checklist
requirements, track checklist evidence status, and prepare checklist-driven
draft findings without making final engineering decisions."

Everything here is review-support only. A rule pack is a reusable review-support
template, not a legal ordinance, not a compliance standard, and not a binding
requirement set. Checklist status is review-support only. Nothing here approves
plans, certifies compliance, verifies CAD, validates design, declares a project
safe, resolves or closes an issue, or makes a final engineering decision. Draft
findings require reviewer confirmation. There are no live AI calls.

Live demo: https://civil-engineer.up.railway.app/

## What Sprint 4 adds

Backend:

- A `RulePack` model and a `RulePackItem` model: reusable, versioned
  review-support checklist templates with categorized requirement items.
- A `ProjectChecklist` model and a `ProjectChecklistItem` model: the reviewer's
  working copy of a rule pack for one project, with reviewer-controlled
  applicability, evidence, and review statuses.
- A `ChecklistEvidenceLink` model: reviewer links between a checklist item and a
  document page, citation, or evidence candidate.
- Sprint 4 fields on `EvidenceCitation` (`project_checklist_item_id`,
  `rule_pack_item_id`, `citation_context`), all nullable so Sprint 2 citations
  keep working.
- A seeded starter stormwater rule pack ("Brookside Stormwater Review Starter
  Pack") with 16 categorized items, clearly labeled as a starter template.
- A `checklist_review_service` covering rule packs, checklist creation from a
  rule pack, item status updates, checklist evidence search (reusing the Sprint
  3 retrieval service), evidence links, and draft findings from checklist items.
- Review-support vocabulary for rule pack source modes, project checklist
  statuses, checklist applicability/evidence/review statuses, link statuses, and
  citation contexts.
- API routes for rule packs, project checklists, checklist item review, evidence
  search, evidence links, and draft findings.

Frontend:

- A checklist review API client (`lib/api/checklistReview.ts`).
- Rule packs list and detail pages, project checklists page, checklist detail
  page (items grouped by category), and a checklist item detail page with status
  controls, an evidence search panel, and a draft finding form.
- Links from the project overview, evidence search, evidence candidate queue, and
  finding detail views, plus a Rule Packs entry in the primary navigation.
- A homepage update describing Sprint 4.

## How this builds on Sprint 1, Sprint 2, and Sprint 3

Sprint 1 created real projects, documents, reviewer findings, and audit events.
Sprint 2 indexed uploaded digital PDFs into page-level records with extracted
text and added reviewer-selected citations. Sprint 3 added deterministic
evidence retrieval and a reviewer draft finding queue. Sprint 4 uses all three:
a checklist organizes review around specific requirements, checklist evidence
search reuses the Sprint 3 retrieval service over the Sprint 2 indexed pages, and
a draft finding from a checklist item reuses the Sprint 2 citation service to
link the source page. Nothing from earlier sprints was removed or changed in a
breaking way, and Brookside Meadows remains a seeded demo fixture.

## Why checklist-driven review comes before live AI

A checklist gives review structure that any later AI assistance must respect. By
making the checklist reviewer-controlled, deterministic, and auditable first, the
system establishes where evidence belongs, what status language is allowed, and
who decides, before any model is introduced. A later AI step can then suggest
candidate evidence or draft language against a known checklist structure without
being trusted to decide applicability or status.

## How rule packs differ from final engineering decisions

A rule pack is a reusable prompt for review, not a determination. It lists what a
reviewer would expect to find for each requirement. It never states that a
project satisfies a requirement, is compliant, or is approved. Applicability and
evidence status are decided by a reviewer, item by item, using review-support
status values only. The starter pack is explicitly labeled "Starter template,
not ordinance."

## What remains demo-only

Brookside Meadows and every existing demo page are unchanged, including the
seeded demo checklist served at the existing `/checklist` routes. The new
project checklist routes are additive and do not replace the seeded demo
checklist. The starter rule pack is seeded for reuse but is a template, not a
jurisdiction ordinance.

## What remains out of scope

A full jurisdiction rule engine, legal ordinance compliance, embeddings and
vector search, OCR, live AI calls, DWG/DXF parsing, GIS, Bluebeam, applicant
portal functionality, automated engineering calculations, geometry or design
validation, final approval workflows, and SSO or full authentication are out of
scope. Checklist-driven review here is reviewer-controlled and deterministic.

## How reviewers apply a checklist to a project

1. Open a real project.
2. Open Project checklists from the project overview.
3. Choose a rule pack (the seeded starter pack is available) and create a
   checklist. The checklist copies each rule pack item into a reviewer-controlled
   project checklist item.
4. Open the checklist to see items grouped by category, each with its expected
   evidence and review-support status.

## How reviewers search evidence for checklist requirements

From a checklist item detail page, a reviewer runs a deterministic evidence
search over the project's indexed PDF page text using the item's expected
evidence as the query. Results are candidates with short excerpts and a relevance
score; they require reviewer confirmation and are not conclusions. If the project
has no indexed pages, the search returns a safe message asking the reviewer to
upload and index a digital PDF first.

## How checklist status is review-support only

Each checklist item carries three reviewer-controlled statuses: applicability
(applies, not applicable by reviewer, applicability unclear, needs reviewer
confirmation), evidence (not reviewed, evidence found, missing evidence,
conflicting evidence, unclear evidence, extraction unavailable, needs reviewer
confirmation), and review progress (not started, evidence review needed, reviewer
note added, citation added, draft finding created, ready for reviewer handoff).
There is intentionally no compliant, noncompliant, approved, verified, passed,
failed, resolved, or closed value. Creating a draft finding from an item sets its
review status to draft finding created; it never finalizes an outcome.

## How to test the workflow locally

Backend:

```
cd backend
pip install -r requirements.txt pytest-cov
pytest --cov=app --cov-report=term-missing --cov-fail-under=90
```

The checklist tests live in `tests/test_checklist_review.py`.

Frontend:

```
npm install
npm run typecheck
npm run lint
npm test
npm run build
```

Manual end-to-end: create a project, upload and index a digital PDF, open
Project checklists, create a checklist from the starter rule pack, open an item,
search its evidence, update its status, and create a draft finding. Inspect Audit
events to see the checklist actions.

## Audit events

Sprint 4 writes: `project_checklist_created`, `checklist_item_status_updated`,
`checklist_item_note_added`, `checklist_item_marked_not_applicable_by_reviewer`,
`checklist_evidence_search_performed`, `checklist_evidence_linked`, and
`checklist_draft_finding_created`. Audit metadata records rule pack id, checklist
id, checklist item id, status changes, evidence candidate id, citation id,
finding id, and result counts only. It never records full extracted page text,
raw server file paths, secrets, or API keys.

## Limitations and next steps

See [CHECKLIST_RULE_PACK_FOUNDATION.md](CHECKLIST_RULE_PACK_FOUNDATION.md) for the
rule pack and checklist design, and [API_CHECKLIST_REVIEW.md](API_CHECKLIST_REVIEW.md)
for the API contract. The recommended next sprint is Production Foundations
Sprint 5: Real Authentication, Reviewer Roles, and Project Access Control.
