# Phase 13: Resubmittal Intake, Revision Comparison, and Applicant Response Cycle Report

> Historical record. This document describes a completed build phase and is
> not current implementation guidance. See docs/README.md for the current
> documentation index.

Phase 13 turns Civil Engineer AI into a multi-round review-support system. A
reviewer can create or load a review cycle for Brookside Meadows, record a
resubmittal package, link uploaded DXF files and applicant response notes,
compare the new DXF parse metadata against a previous round, map applicant
responses to prior response package or workflow items, mark review-support
resolution statuses, carry unresolved items forward, and prepare the next review
cycle.

Civil Engineer AI remains a review-support and evidence-organization system.
Revision comparison compares extracted DXF metadata only (layers, references,
blocks, and review findings). It does not verify CAD, validate geometry or
design, certify compliance, approve plans, send official correspondence, or
replace a licensed Professional Engineer. There is no action called approve, and
no status uses final-decision language.

## The review cycle workflow

1. The initial review produces findings, a review packet, a workflow board, and
   a response package (Phases 1 through 10).
2. The applicant or design engineer returns a resubmittal.
3. The reviewer records the resubmittal package against the active review cycle.
4. The reviewer links uploaded DXF files (parsed through the Phase 11 and 12 DXF
   path) and applicant response notes to the resubmittal.
5. The reviewer runs a revision comparison between the previous and current DXF
   parse runs.
6. The system creates review-support revision change records.
7. The reviewer maps applicant responses to prior response package or workflow
   items (manually or with deterministic keyword suggestions).
8. The reviewer marks items as addressed_for_review, still_open,
   needs_more_information, carried_forward, or reviewer_checked.
9. The system carries unresolved items forward and prepares a next-cycle summary.
10. The human reviewer remains responsible for any final determination.

## Supported file type

DXF only, through the existing Phase 11 and Phase 12 DXF parsing path. DWG
parsing, Autodesk and Civil 3D integration, PDF parsing, OCR, GIS, and computer
vision remain out of scope.

## Models

Phase 13 adds ten models: ReviewCycle, ResubmittalPackage, ResubmittalDocument,
ApplicantResponse, ApplicantResponseMapping, RevisionComparisonRun,
RevisionChangeRecord, IssueCarryForward, ResponseResolutionRecord, and
NextCyclePreparation. They reuse the existing project, response package, workflow
board, and CAD parse data rather than duplicating it.

## Revision comparison compares extracted DXF metadata only

`run_revision_comparison(previous_parse_run_id, current_parse_run_id)` compares
the two parse rounds across:

- layer names and review categories
- reference candidates grouped by type: sheet references, detail references, pipe
  labels, basin labels, outfall labels, wetland buffer labels, and other text
  references
- block names
- CAD review findings (keyed by finding type and title)

It produces RevisionChangeRecord rows with a change type of added, removed,
changed, unchanged, or carried_forward. It detects added references, removed
references, changed text values, unchanged references, carried-forward missing
references (a sheet still referenced and still without a matching plan sheet in
both rounds), previously flagged labels still present, and new references to
missing sheets.

This is a metadata comparison for review support. It never compares geometry in a
way that implies engineering validation, and it does not claim design
correctness or CAD verification. A second synthetic fixture,
`app/cad_samples/brookside_meadows_r2.dxf`, represents a resubmittal revision of
the Phase 11 sample and is used by the demo and tests.

## Applicant response mapping

`auto_suggest_response_mappings(review_cycle_id)` creates deterministic mapping
suggestions between unmapped applicant responses and prior response package items
and workflow items using shared keywords (and any explicit applicant target).
There are no live AI calls and no vector search. Every mapping carries a
mapping_confidence (high, medium, low, or needs_human_review, never verified), a
mapping_reason, and a requires_human_review flag.

## Resolution and carry-forward

A reviewer records review-support resolution statuses with
`create_response_resolution_record` and `update_response_resolution_status`. The
allowed statuses are addressed_for_review, still_open, needs_more_information,
carried_forward, reviewer_checked, and excluded_from_cycle. addressed_for_review
means an item appears addressed in the reviewer's judgment and is ready for human
review, never that it is resolved, closed, fixed, approved, or certified.

`carry_forward_unresolved_items(review_cycle_id)` carries forward, without
duplication, workflow items still in needs_follow_up or needs_more_information,
response package items still in needs_revision or draft, CAD review findings not
promoted and still needing review, and revision change records marked
needs_follow_up or carried_forward. Re-running does not create duplicate
carry-forward records for the same source item.

## Next-cycle preparation

`prepare_next_cycle(review_cycle_id)` generates a NextCyclePreparation summary of
what should move into the next review round: carried-forward items, items needing
more information, applicant responses needing clarification, and revision changes
needing review. The summary organizes review-support work and never issues a
final decision.

## Allowed statuses

- Review cycle: draft, active, reviewer_checked, ready_for_next_cycle, archived.
- Resubmittal package: received, intake_review, needs_more_information,
  ready_for_comparison, comparison_complete, reviewer_checked, archived.
- Resubmittal document type: dxf_cad_file, applicant_response_note,
  revised_plan_reference, supplemental_document, other.
- Resubmittal document status: received, linked, needs_human_review,
  excluded_from_review_cycle.
- Applicant response: received, mapped_to_issue, needs_clarification,
  reviewer_checked, carried_forward.
- Mapping confidence: high, medium, low, needs_human_review.
- Revision comparison run: draft, completed, completed_with_warnings,
  needs_human_review, archived.
- Revision change type: added, removed, changed, unchanged, carried_forward.
- Revision change reviewer status: draft, needs_follow_up, needs_more_information,
  reviewer_checked, carried_forward, excluded_from_cycle.
- Carry-forward status: carried_forward, needs_more_information, needs_follow_up,
  reviewer_checked.
- Resolution status: addressed_for_review, still_open, needs_more_information,
  carried_forward, reviewer_checked, excluded_from_cycle.
- Next-cycle status: draft, ready_for_next_cycle, needs_human_review, archived.

## Forbidden language

No status, action name, generated label, summary, change record, resolution
record, carry-forward record, or next-cycle preparation uses final-decision
language: approved, certified, verified, passed, failed, compliant, noncompliant,
safe, unsafe, design validated, resolved, closed, fixed, or final. A backend test
asserts this. There is no action called approve.

## Audit events

Phase 13 writes audit events when a review cycle is created
(review_cycle_created) or viewed (review_cycle_viewed), the review cycle
dashboard is viewed (review_cycle_dashboard_viewed), a resubmittal package is
created (resubmittal_created), viewed (resubmittal_viewed), or its status changes
(resubmittal_status_changed), a CAD file is linked (resubmittal_cad_file_linked),
an applicant response is created (applicant_response_created), a mapping is
created (applicant_response_mapping_created), mappings are suggested
(response_mappings_suggested), a revision comparison is run
(revision_comparison_run) or viewed (revision_comparison_viewed), revision
changes are viewed (revision_changes_viewed), an issue is carried forward
(issue_carried_forward), a carry-forward summary is viewed
(carry_forward_summary_viewed), a response resolution is created
(response_resolution_created) or its status changes
(response_resolution_status_changed), a next cycle is prepared
(next_cycle_prepared) or viewed (next_cycle_preparation_viewed), a response
mapping summary is viewed (response_mapping_summary_viewed), and a resolution
summary is viewed (resolution_summary_viewed).

Intentional read side effects: the GET endpoints for a single review cycle, the
review cycle dashboard, a revision comparison run and its changes, the response
mapping summary, the carry-forward summary, the resolution summary, and the
next-cycle preparation each write an audit event recording reviewer access. This
is intentional so the decision history shows reviewer access.

## API endpoints

Review cycle:

- `POST /api/v1/projects/{project_id}/review-cycles`
- `GET /api/v1/projects/{project_id}/review-cycles`
- `GET /api/v1/review-cycles/{review_cycle_id}`
- `GET /api/v1/projects/{project_id}/review-cycle-summary`
- `GET /api/v1/projects/{project_id}/review-cycle-dashboard`

Resubmittal:

- `POST /api/v1/projects/{project_id}/resubmittals`
- `GET /api/v1/projects/{project_id}/resubmittals`
- `GET /api/v1/resubmittals/{resubmittal_package_id}`
- `PATCH /api/v1/resubmittals/{resubmittal_package_id}/status`
- `POST /api/v1/resubmittals/{resubmittal_package_id}/cad-files/{cad_file_id}`
- `POST /api/v1/resubmittals/{resubmittal_package_id}/applicant-responses`

Applicant responses:

- `GET /api/v1/projects/{project_id}/applicant-responses`
- `POST /api/v1/applicant-responses/{applicant_response_id}/mappings`
- `POST /api/v1/review-cycles/{review_cycle_id}/suggest-response-mappings`
- `GET /api/v1/review-cycles/{review_cycle_id}/response-mapping-summary`

Revision comparison:

- `POST /api/v1/review-cycles/{review_cycle_id}/revision-comparisons`
- `GET /api/v1/projects/{project_id}/revision-comparisons`
- `GET /api/v1/revision-comparisons/{comparison_run_id}`
- `GET /api/v1/revision-comparisons/{comparison_run_id}/changes`
- `GET /api/v1/revision-comparisons/{comparison_run_id}/summary`

Carry-forward:

- `POST /api/v1/review-cycles/{review_cycle_id}/carry-forward`
- `GET /api/v1/projects/{project_id}/carry-forwards`
- `GET /api/v1/review-cycles/{review_cycle_id}/carry-forward-summary`

Resolution:

- `POST /api/v1/review-cycles/{review_cycle_id}/resolution-records`
- `PATCH /api/v1/resolution-records/{resolution_record_id}/status`
- `GET /api/v1/projects/{project_id}/resolution-records`
- `GET /api/v1/review-cycles/{review_cycle_id}/resolution-summary`

Next cycle:

- `POST /api/v1/review-cycles/{review_cycle_id}/prepare-next-cycle`
- `GET /api/v1/review-cycles/{review_cycle_id}/next-cycle-preparation`

All Phase 1 through Phase 12 endpoints remain available and unchanged.

## Frontend

The Review Cycles page shows the review cycle dashboard, a review round timeline,
a resubmittal intake form and package panel, an applicant response panel and
mapping panel, a revision comparison panel with a change table, a response
resolution panel, an issue carry-forward panel, and a next-cycle preparation
panel. Detail routes show a single review cycle, a resubmittal package, and a
revision comparison run. All data is backend-canonical; the browser does not
simulate review cycle data.

## What remains out of scope

Phase 13 does not add DWG parsing, Autodesk or Civil 3D integration, PDF parsing,
OCR, GIS, computer vision, vector search, authentication, deployment setup, email
sending, external paid APIs, design validation, quantity certification, or
automated engineering decisions. The mock AI provider remains the default and no
live AI calls are included.
