# Reviewer Dashboard and Workload

This document describes the Sprint 9 reviewer dashboard, reviewer queue,
organization workload, and per-project workload views. These are operational
review-support helpers. They do not approve plans, certify compliance, verify
CAD, validate design, resolve issues, close issues, or make final engineering
decisions.

## Dashboard concept

The reviewer dashboard is a cross-project operational view. It aggregates pending
reviewer actions and review-support metrics across the projects the signed-in
user can access, so a reviewer can understand workload and decide what to work on
next. The dashboard is read-only aggregation over existing review records. It
introduces no new review outcome.

Every dashboard view is access controlled. The reviewer dashboard only includes
projects the user can read under Sprint 5 access control. The organization
dashboard requires organization membership. Project workload requires project
read access.

## Reviewer queue

The reviewer queue lists pending reviewer actions across accessible projects. Each
queue item names an action type, the project, a count, a safe aging bucket, and a
link to the project workflow page where human review continues. The queue item
types are:

- document indexing
- evidence candidate triage
- checklist evidence review
- applicant response review
- carried-forward matrix item
- response package handoff

The queue can be filtered by item type. The queue is an operational helper, not a
final review outcome, and it never closes or resolves anything.

## Organization workload

The organization dashboard summarizes workload across the projects an
organization member can access. It reports:

- project count and projects needing reviewer attention
- project counts by review-support status
- review priority counts
- aggregate review-support metrics
- per-project summaries

A reviewer workload summary groups projects by assigned reviewer. It is limited to
organization admins and senior reviewers. Read-only and reviewer-role members can
view the organization dashboard but not the reviewer workload summary.

## Pending action cards

The dashboard and project workload views present pending reviewer action counts
as metric cards with review-support labels only, for example pending reviewer
action, documents needing indexing, evidence candidates needing triage, checklist
items with missing evidence, applicant responses needing reviewer review, carried
forward for review, and packages ready for reviewer handoff. None of these labels
implies approval, compliance, verification, or issue resolution.

## Aging indicators

Aging is computed from the most recent activity timestamp on a project and mapped
to a safe bucket:

- updated today
- waiting 1 to 3 days
- waiting 4 to 7 days
- waiting more than 7 days

When a project has an explicit review due date, due date indicators are added:

- due date set
- due soon
- past due for reviewer attention

Past due is a workflow timing indicator that the due date has passed. It is not an
engineering outcome and never implies a project is noncompliant or unsafe.

## Workflow links

Every dashboard card and queue item links to an existing project workflow page
(documents, evidence candidate queue, checklists, response matrix, resubmittal
rounds, or response packages). The dashboard adds visibility; the underlying
review work continues on the existing pages.

## Access-control filtering

Dashboard data is filtered on the backend. The reviewer dashboard calls the same
access-control service used by every protected route to list the user's
accessible projects, and only those projects are aggregated. The organization
dashboard intersects organization projects with the member's accessible projects,
so a member never sees a project they cannot read. Assignment and priority updates
require project admin access.

## Limitations

- Metrics are operational indicators only, not a compliance or final-review
  dashboard.
- Counts do not represent approval, certification, or issue resolution.
- Aging and due date indicators are workflow timing helpers.
- Authentication is local only; enterprise SSO is future work.
- The applicant portal is not complete; applicant responses are recorded for
  reviewer review only.
- Organization workload includes only projects the member can read. Projects
  created without an organization are not attributed to an organization
  dashboard.
