# Reference Project: Brookside Meadows

Brookside Meadows is the synthetic reference project for Civil Engineer AI. It is
used for evaluation, acceptance, training, regression, and demonstration. This
document folds in the former Brookside Meadows project story, seed data plan,
homepage hotspot plan, and synthetic-demo-data notes.

Brookside Meadows is synthetic demo data. The Town of Hartwell is fictional.
Nothing in the reference project is a real engineering submittal, a real
permitting decision, or a real approval. The app
does not make real approval decisions. Seeded records are labeled as seeded
review-support data and were not
extracted from real CAD, PDF, GIS, or plan files.

## What it represents

Brookside Meadows is a fictional 47-lot single-family residential subdivision on
a 38.5-acre parcel draining toward a wetland and stream corridor near Quarry
Road, reviewed by the fictional Town of Hartwell. The fixture was written like a
real preliminary subdivision and stormwater submission, then intentionally seeded
with gaps and conflicts so the review-support workflow has something real to
find.

The planted issues include a design storm discrepancy, missing infiltration
testing, a groundwater separation concern, a missing downstream culvert
discussion, unclear maintenance ownership, an erosion-control phasing mismatch,
an undocumented sediment observation, an open pipe-material RFI, a Pond A versus
Basin 1 naming inconsistency, and a missing revised sheet C-3.1.

## Why a synthetic reference project

- Every reviewer sees the same demo. A stable synthetic fixture makes evaluation
  reproducible instead of dependent on whatever was uploaded last.
- Real submittals are owned by real applicants and municipalities. Using one in a
  public demonstration would be wrong even if it were available.
- Planted issues let the workflow show the interesting path. A clean submission
  would demonstrate nothing about findings, responses, or resubmittals.
- The boundary stays honest. Synthetic data makes it unambiguous that no real
  engineering decision is being made anywhere in the app.

## What review artifacts it demonstrates

- A submitted document package with intake status tracking.
- Indexed PDF pages with per-page extraction records.
- Review-support findings with risk levels, each linked to source evidence.
- Checklist-driven review against a stormwater rule pack.
- An applicant response matrix and multi-round resubmittal tracking.
- A draft response package with editable wording and a human sign-off checklist.
- A review-support packet assembled for reviewer handoff.
- An audit trail of reviewer actions.
- Homepage hotspot annotations over synthetic plan-sheet previews, which are
  seeded review-support metadata and not parsed from real files.

## Where the data lives

The `app/db/seeds` package holds the backend seed data and loaders that populate
the Brookside Meadows fixture at startup, split by domain: `reference_project`,
`documents`, `checklist`, `findings`, `evidence`, `plan_sheets`, `hotspots`, and
`workflow`. The frontend fixtures live in `data/*.ts` and drive the public demo
surfaces. Bundled sample DXF fixtures for CAD intake live in
`backend/app/cad_samples`.

## How to extend the reference project

1. Extend the story first so the data stays coherent.
2. Add matching records to the backend seeds in `app/db/seeds` and the frontend
   fixtures in `data/`, keeping the two aligned.
3. Keep review-support language. New statuses must come from the existing safety
   vocabulary in `app/core/vocab`, and nothing may imply approval or compliance.
4. Update the expected findings and evaluation cases if the new scenario changes
   what the system should surface.
5. Run the frontend and backend test suites, which include content contracts that
   guard the boundary wording.
