# Metrics Boundary and Limitations

This document states the professional boundary for the Sprint 9 reviewer
dashboard, workload management, and operational metrics. It exists so the meaning
of every dashboard count stays clear and bounded.

## Dashboard metrics are operational indicators

Every number on the dashboard answers an operational question: how much
review-support work is outstanding, and how long has it been waiting. The metrics
help a reviewer sequence work and help an organization admin understand team
workload. They are operational indicators, nothing more.

## Counts do not represent approval or compliance

No dashboard count represents approval, certification, compliance, verification,
or validation. There is intentionally no count or status labeled approved, closed,
resolved, passed, failed, compliant, noncompliant, verified, certified, safe, or
unsafe anywhere in the dashboard. A count of zero pending actions means there is
no outstanding review-support work listed, not that a project is approved,
compliant, or complete.

## Pending items require human review

Pending reviewer action counts list work that a human reviewer must perform.
Promoting an evidence candidate, confirming a finding, reviewing an applicant
response, or handing off a package are all human actions. The dashboard never
performs them and never auto-resolves a pending item.

## Aging indicators are workflow helpers

Aging buckets (updated today, waiting 1 to 3 days, waiting 4 to 7 days, waiting
more than 7 days) and due date indicators (due date set, due soon, past due for
reviewer attention) describe how long an item has been waiting for reviewer
attention. They are workflow timing helpers. Past due means a reviewer-set due
date has passed; it is not an engineering outcome and does not imply a project is
noncompliant, unsafe, or late in any regulatory sense.

## No automated conclusions

The dashboard draws no conclusions. It aggregates existing review records into
counts and lists. It does not decide whether documents satisfy requirements, does
not rank project quality, and does not produce a recommendation.

## No engineering validation

The dashboard performs no engineering calculation, geometry check, design
validation, or CAD verification. It reads review-support metadata only.

## No legal compliance determination

The dashboard makes no legal or regulatory compliance determination. Civil
Engineer AI supports human plan review. It does not approve plans, certify
compliance, stamp drawings, declare a project safe, or replace a licensed
Professional Engineer.

## Additional limitations

- Authentication is local only; enterprise SSO is future work.
- The applicant portal is not complete; applicant responses are recorded for
  reviewer review only and are never treated as proof.
- Organization workload includes only projects the member can read. A project
  created without an organization is not attributed to an organization dashboard.
- Metrics are computed in real time and are not a historical analytics system.
