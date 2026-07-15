# Production Foundations Sprint 9: Reviewer Dashboard, Workload Management, and Operational Metrics

> Historical record. This document describes a completed build phase and is
> not current implementation guidance. See docs/README.md for the current
> documentation index.

## What Sprint 9 adds

Sprint 9 adds the first cross-project operational view to Civil Engineer AI.
Before this sprint, reviewers could manage individual project records and issue
reviewer communication packages, but there was no way to see workload across the
projects they can access. Sprint 9 adds:

- A reviewer dashboard that aggregates pending reviewer actions and
  review-support metrics across all accessible projects.
- A reviewer queue that lists pending reviewer actions across projects with safe
  aging indicators and direct links to the relevant project workflow page.
- An organization dashboard that summarizes workload across the projects an
  organization member can access, with project counts by review-support status
  and a reviewer workload summary for organization admins and senior reviewers.
- Per-project workload summaries and a pending-actions list.
- A project assignment and review priority foundation, with audit-attributed
  updates.

All dashboard data is computed in real time from existing review records. No new
persistent metric table was added. The reviewer dashboard, organization
dashboard, and project workload views reuse the same per-project metric
computation so the same safe counts appear everywhere.

## How it builds on Sprints 1 through 8

Sprint 9 reads, but does not change, the data produced by earlier sprints:

- Sprint 1 project records, documents, findings, and audit events.
- Sprint 2 PDF page indexing status.
- Sprint 3 evidence retrieval candidates.
- Sprint 4 checklist evidence status.
- Sprint 5 authentication and project access control, which scopes every
  dashboard result to the projects a user can read.
- Sprint 6 storage metadata (read at a safe summary level only; storage keys,
  paths, and credentials are never exposed).
- Sprint 7 response matrix items, applicant responses, and resubmittal rounds.
- Sprint 8 reviewer response packages and issuance records.

The dashboard adds a single aggregation layer on top of this data. It does not
introduce new review outcomes or change any existing workflow.

## Why dashboard visibility matters in municipal review

A municipal stormwater reviewer typically carries many concurrent projects, each
at a different stage: documents waiting to be indexed, evidence candidates waiting
for triage, checklist items missing evidence, applicant responses waiting for
review, resubmittals registered, and response packages ready to hand off. Without
a cross-project view, it is hard to know which project needs attention next.

The reviewer dashboard organizes this work. It surfaces pending reviewer actions
and safe aging indicators so a reviewer can sequence their day, and it gives
organization admins a workload view across their team. This is workload
coordination, not a decision engine.

## How reviewer dashboard data is computed

For each project the signed-in user can read, the operational metrics service
computes safe counts directly from the database:

- documents uploaded, needing indexing, indexed with text, and with extraction
  unavailable
- findings needing reviewer confirmation
- evidence candidates needing triage
- checklist items with missing or unclear evidence
- applicant responses needing reviewer review
- resubmittal rounds registered
- response matrix items carried forward
- response packages in draft, ready for reviewer handoff, and issued by reviewer

A project's pending reviewer action count is the sum of the outstanding
categories (indexing, candidate triage, checklist evidence review, applicant
response review, carry-forward, and package handoff). Aging is computed from the
most recent of the project's last reviewer activity, updated, or created
timestamps and mapped to a safe bucket (updated today, waiting 1 to 3 days,
waiting 4 to 7 days, waiting more than 7 days). When a review due date is set,
due date indicators (due date set, due soon, past due for reviewer attention) are
added as workflow timing helpers.

The reviewer dashboard sums these per-project metrics into accessible totals and
builds a reviewer queue from the per-project pending-action categories.

## How organization dashboard data is computed

The organization dashboard requires organization membership. It includes only
projects whose organization matches the requested organization and that the
member can read. It reports project counts by review-support status, priority
counts, aggregate metrics, and per-project summaries. The reviewer workload
summary groups projects by assigned reviewer and is limited to organization
admins and senior reviewers.

## Why dashboard metrics are review-support indicators, not final outcomes

Every count answers an operational question: how much review-support work is
outstanding, and how long has it been waiting. No count represents approval,
certification, compliance, verification, or issue resolution. There is no count
labeled approved, closed, resolved, passed, failed, compliant, verified,
certified, safe, or unsafe. Pending items always require human review. Aging and
due date indicators are workflow timing helpers, never an engineering outcome.

## What remains demo-only

Brookside Meadows remains a seeded public demo fixture and is fully preserved. It
appears in the demo organization dashboard and has a workload summary like any
other project. Seeded demo users (a demo reviewer and a demo admin) exist for the
local demo only with documented local passwords.

## What remains out of scope

Sprint 9 does not add live AI calls, OCR, DWG parsing, GIS or Bluebeam
integrations, automated engineering calculations, geometry or design validation,
final approval workflows, enterprise SSO, a full applicant portal, or billing. It
does not rewrite the architecture, remove Brookside Meadows, or weaken
authentication, access control, audit, or storage enforcement.

## How to test the workflow locally

1. Start the backend and frontend.
2. Sign in (or register) as a reviewer.
3. Create a project and register a document, then open `/dashboard`.
4. Confirm the reviewer dashboard shows accessible projects, pending reviewer
   action counts, and a reviewer queue.
5. Open `/dashboard/queue` and confirm pending actions are listed with safe
   aging buckets and links to the project workflow pages.
6. Open a project, then `/projects/{projectId}/workload`, and confirm the
   workload metrics, pending actions, and the assignment and priority controls.
7. As an organization admin, open
   `/organizations/{organizationId}/dashboard` and confirm the organization
   workload summary and reviewer workload table.

Automated tests live in `backend/tests/test_dashboard.py`,
`lib/api/__tests__/dashboard.test.ts`, and `app/__tests__/dashboardUi.test.tsx`.
Run the backend suite with `pytest --cov=app --cov-fail-under=90` and the
frontend suite with `npm run typecheck`, `npm run lint`, `npm test`, and
`npm run build`.
