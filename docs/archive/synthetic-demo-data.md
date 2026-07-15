# Synthetic Demo Data

Brookside Meadows is synthetic demo data. The Town of Hartwell is fictional. Nothing in the demo is a real engineering submittal, a real permitting decision, or a real approval, and the app does not make real approval decisions. This page explains what the data represents and why the project uses it.

## What Brookside Meadows represents

Brookside Meadows is a fictional 47-lot single-family residential subdivision on a 38.5-acre parcel, reviewed by the fictional Town of Hartwell. The fixture was written like a real preliminary subdivision and stormwater submission, then intentionally seeded with gaps and conflicts so the review-support workflow has something real to find. The full narrative lives in [BROOKSIDE_MEADOWS_PROJECT_STORY.md](BROOKSIDE_MEADOWS_PROJECT_STORY.md).

## What review artifacts it demonstrates

- A submitted document package with intake status tracking.
- Indexed PDF pages with per-page extraction records.
- Review-support findings with risk levels, each linked to source evidence.
- Checklist-driven review against a stormwater rule pack.
- An applicant response matrix and multi-round resubmittal tracking.
- A draft response package with editable wording and a human sign-off checklist.
- A review-support packet assembled for reviewer handoff.
- An audit trail of reviewer actions.

## Why synthetic data is appropriate for a portfolio

- Every reviewer sees the same demo. Seeded data makes a five-minute recruiter review reproducible instead of dependent on whatever was uploaded last.
- Real submittals are owned by real applicants and municipalities. Using one in a public portfolio would be wrong even if it were available.
- Planted issues let the demo show the interesting path. A clean submission would demonstrate nothing about findings, responses, or resubmittals.
- The boundary stays honest. Synthetic data makes it unambiguous that no real engineering decision is being made anywhere in the app.

## Where the data lives

- `data/*.ts`: the frontend fixtures (project, documents, checklist, findings, hotspots, audit events, evaluation cases) used by the public demo and as the fallback when the backend is unreachable.
- `backend/app/db`: the backend seed data and loaders that populate the Brookside Meadows fixture at startup.
- `backend/app/cad_samples`: bundled sample DXF fixtures for CAD intake.
- `docs/SEED_DATA_PLAN.md`: the original plan for the seeded dataset.

Seeded records are labeled as seeded review-support data in the UI. They were not extracted from real CAD, PDF, GIS, or plan files.

## How to extend the dataset

1. Extend the story first. Add the new scenario to the Brookside Meadows narrative so the data stays coherent.
2. Add matching records to the frontend fixtures in `data/` and the backend seeds in `backend/app/db`, keeping the two aligned.
3. Keep review-support language. New statuses must come from the existing safety vocabulary, and nothing may imply approval or compliance.
4. Update the expected findings and evaluation cases if the new scenario changes what the system should surface.
5. Run the frontend and backend test suites, which include content contracts that guard the boundary wording.
