# Phase 14: Reviewer Command Center and Project Health Dashboard Report

Phase 14 unifies Civil Engineer AI into one reviewer command center. The Project
Dashboard aggregates the review-support data from every prior phase into a single
operational view: a command center snapshot, project health metrics, reviewer
attention items with a recommended next step, a project timeline, review
readiness checks, reviewer notes, next steps, and links into the existing
modules.

Civil Engineer AI remains a review-support and evidence-organization system. The
dashboard organizes review-support work and links into existing modules rather
than replacing them. It does not approve plans, certify compliance, stamp
drawings, verify CAD, validate design, declare a project safe, send official
correspondence, or close or resolve issues. There is no action called approve.
ready_for_human_review means an area is organized enough for human review, never
that it is complete, passed, or approved.

## The command center workflow

1. The reviewer opens the Project Dashboard for Brookside Meadows.
2. The command center generates (or refreshes) a snapshot that aggregates the
   current review-support state across all modules.
3. The reviewer reads the overall status, health metrics, and attention queue to
   answer what needs attention right now.
4. The reviewer works the attention items, each of which deep links into its
   source module (CAD Intake, Review Cycles, Workflow Board, Response Package,
   Review Packet, Sheet Viewer, Plan Sheets, or CAD Review).
5. The reviewer marks attention items reviewer_checked, deferred, or
   not_applicable, reads the recommended next steps, reviews the timeline and
   readiness checks, and records reviewer notes.
6. Refreshing the snapshot re-aggregates the state without creating duplicate
   attention items and preserves the reviewer status of each item by source.
7. A licensed Professional Engineer review is always still required.

## What the dashboard answers

The command center answers what needs attention now, what changed since the last
round, what items are carried forward, what CAD findings still need review, what
applicant responses need mapping or clarification, what response package items
are ready for human review, what resubmittals are waiting for comparison, what is
ready for handoff, where evidence is incomplete, and what the reviewer should do
next.

## Aggregation

The command center aggregates from existing data across phases: documents,
checklist items, findings, audit events, plan sheets, CAD-aware metadata, plan
references, plan consistency findings, sheet hotspots, review packets, workflow
items, follow-up requests, response packages and items, CAD files, CAD parse
runs, CAD review findings, unpromoted CAD findings, review cycles, resubmittal
packages, applicant responses and mappings, revision comparison runs and change
records, issue carry-forwards, response resolution records, and next-cycle
preparation records. It reads this data directly so the aggregation does not
trigger the read audit side effects of the other modules.

## Attention items

Attention items are generated for workflow items in needs_follow_up or
needs_more_information, workflow items ready for handoff, open follow-up requests,
CAD files with a technical parse failure, CAD parse runs needing human review,
unpromoted CAD findings, applicant responses without mappings, low-confidence
applicant response mappings, resubmittals needing comparison, revision changes
needing review, carry-forward items, response package items needing revision,
next-cycle preparation needing human review, and checklist evidence gaps. Each
item carries a severity, a source module, a deep-link target route, and a
recommended next step.

Regenerating the snapshot does not create duplicate attention items for the same
source. Each generation keeps a single latest snapshot, matches the prior
attention items by source, and preserves their reviewer status so a
reviewer_checked, deferred, or not_applicable decision survives a refresh.

## Health metrics

Health metrics summarize the workflow status distribution, response package item
revisions, CAD intake status and parse failures, unpromoted CAD findings,
applicant response mapping gaps, resubmittals awaiting comparison, revision
changes needing review, carry-forward items, and open resolution items. Each
metric carries a severity, a source module, and a source route.

## Timeline

The timeline is rebuilt from existing source records on each snapshot generation
and prefers meaningful product events over low-level noise: review packet
generated, workflow board generated, response package generated, CAD file
registered, DXF parse run recorded, resubmittal received, applicant response
received, revision comparison recorded, issues carried forward, and next cycle
prepared.

## Readiness checks

Readiness checks cover documents reviewed for gaps, CAD intake reviewed,
unpromoted CAD findings reviewed, workflow items triaged, applicant responses
mapped, revision comparison reviewed, carry-forward items reviewed, response
package prepared, and a human review signoff that is always required. A check is
not_started when there is no source data, needs_attention when it has blockers,
and ready_for_human_review otherwise. The human review signoff check is always
ready_for_human_review and is never marked complete or approved.

## Allowed statuses

- Overall command center status: draft, active_review, needs_attention,
  ready_for_handoff, needs_more_information, reviewer_checked.
- Health metric and attention item severity: info, low, medium, high,
  needs_human_review.
- Attention item status: open, reviewer_checked, deferred, not_applicable.
- Readiness status: not_started, needs_attention, in_review,
  ready_for_human_review, reviewer_checked.

No status, label, summary, recommendation, readiness check, health metric,
attention item, or timeline event uses final-decision language: approved,
certified, verified, passed, failed, compliant, noncompliant, safe, unsafe,
design validated, resolved, closed, complete, or completed. A backend test
asserts this.

## Audit events

Phase 14 writes audit events when a command center snapshot is generated
(command_center_snapshot_generated), the command center is viewed
(command_center_viewed), the latest snapshot is viewed
(command_center_latest_viewed), health metrics are viewed
(command_center_metrics_viewed), attention items are viewed
(command_center_attention_viewed), an attention item status changes
(command_center_attention_status_changed), the timeline is viewed
(command_center_timeline_viewed), readiness checks are viewed
(command_center_readiness_viewed), a reviewer note is added
(command_center_note_added), reviewer notes are viewed
(command_center_notes_viewed), next steps are viewed
(command_center_next_steps_viewed), module links are viewed
(command_center_module_links_viewed), and the health summary is viewed
(command_center_health_summary_viewed).

Intentional read side effects: the command center, latest snapshot, health
metrics, attention items, timeline, readiness checks, reviewer notes, next steps,
module links, and health summary GET endpoints each write an audit event
recording reviewer access, and they generate an initial snapshot once if none
exists. This is intentional so the decision history shows reviewer access.

## API endpoints

- `POST /api/v1/projects/{project_id}/command-center/snapshot`
- `GET /api/v1/projects/{project_id}/command-center`
- `GET /api/v1/projects/{project_id}/command-center/latest`
- `GET /api/v1/projects/{project_id}/command-center/health-metrics`
- `GET /api/v1/projects/{project_id}/command-center/attention-items`
- `PATCH /api/v1/command-center/attention-items/{attention_item_id}/status`
- `GET /api/v1/projects/{project_id}/command-center/timeline`
- `GET /api/v1/projects/{project_id}/command-center/readiness-checks`
- `POST /api/v1/projects/{project_id}/command-center/notes`
- `GET /api/v1/projects/{project_id}/command-center/notes`
- `GET /api/v1/projects/{project_id}/command-center/next-steps`
- `GET /api/v1/projects/{project_id}/command-center/module-links`
- `GET /api/v1/projects/{project_id}/command-center/health-summary`

All Phase 1 through Phase 13 endpoints remain available and unchanged.

## Links into modules, not a replacement

The dashboard is a unifying view, not a replacement for the modules. Every
attention item, health metric, timeline event, next step, and module link deep
links into the existing route (for example /cad-intake, /review-cycles,
/workflow-board, /response-package, /review-packet, /sheet-viewer, /plan-sheets,
and /cad-review). The reviewer always acts in the underlying module.

## Frontend

The Project Dashboard page shows a command center summary card, a project health
metric grid, a reviewer attention queue grouped by severity with an attention
item detail panel, a recommended next steps panel, a review readiness checklist,
a project health summary, a project timeline, a module links panel, and a
reviewer notes panel. All data is backend-canonical; the browser does not
simulate command center data.

## What remains out of scope

Phase 14 adds no new parsing, AI, or external integration. It does not add DWG
parsing, Autodesk or Civil 3D integration, PDF parsing, OCR, GIS, computer
vision, vector search, authentication, deployment setup, email sending, or
external paid APIs. It aggregates the existing CAD intake and revision comparison
status alongside every other module; it does not add CAD capabilities. The mock
AI provider remains the default and no live AI calls are included.
