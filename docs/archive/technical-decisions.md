# Technical Decisions

Key product and engineering decisions in this repository, with the reasoning specific to this project. Nothing here is generic architecture advice; each entry explains a choice a reviewer can see in the code.

## Recruiter-first homepage instead of dashboard-first

The homepage originally opened on dashboard widgets. A recruiter landing at `/` had to reverse-engineer what the product was from KPI numbers. The page now leads with the Brookside Meadows hero image, a one-paragraph project description, proof chips, and calls to action, and only then shows the operational dashboard. A first-time visitor understands the project before seeing its metrics, and the dashboard reads as proof instead of as a puzzle.

## Operational metrics after project context

The KPI cards and widgets stayed on the homepage on purpose. Removing them would make the page a brochure. Showing them after the context section keeps the operational feel while giving them a frame: these are the numbers a reviewer would manage, in a demo you now understand.

## Brookside Meadows is synthetic

A public portfolio cannot use a real submittal, and a live-upload demo would give every visitor a different experience. A synthetic subdivision with intentionally planted review issues gives every reviewer the same five-minute path and keeps the professional boundary unambiguous. See [synthetic-demo-data.md](synthetic-demo-data.md).

## Human-in-the-loop boundary everywhere

The system is review support, not review. There is no approve action in the codebase, statuses come from a safety vocabulary enforced by backend tests, and every workflow terminates at a human reviewer surface (`/human-review`, the sign-off checklist, the handoff packet). This is a legal and ethical requirement of the domain: a licensed Professional Engineer is responsible for engineering decisions, and software that blurs that line is not a portfolio asset.

## Evidence-first review

Findings without sources are opinions. Every finding in the system links to its evidence, PDF citations resolve to a specific page, and retrieval results are labeled candidates until a reviewer confirms them. This mirrors how plan review actually works: the reviewer's product is a defensible comment, and defensibility comes from traceability.

## Seeded data with a real backend behind it

The public demo runs from seeded fixtures so it works without an account or an API key, and the typed API client falls back to the same fixtures if the backend is unreachable. Behind that, the FastAPI backend implements real project intake, document indexing, citations, checklist review, response packages, and access control. The seeded layer is a demo strategy, not the architecture. [real-vs-mocked.md](real-vs-mocked.md) maps which is which.

## Route structure mirrors the review workflow

Routes are named for review artifacts (`/documents`, `/findings`, `/review-packet`, `/response-package`, `/resubmittals`) rather than for UI patterns, and the guided demo walks them in the order a reviewer would. The older demo modules stay reachable under their own routes instead of being deleted, because they document the build history and still demonstrate the workflow end to end.

## No text overlaid on the hero image

The Brookside Meadows hero image already contains the project name. Overlaying a duplicate title would look like a template and would break at small widths. The title, subtitle, and description live in HTML next to the image, which also keeps them selectable, translatable, and readable by screen readers.

## Known limitations are documented, not hidden

The README states what is seeded, what is simulated, and what is out of scope, and this docs folder goes a level deeper. For a portfolio project the honesty is the feature: a reviewer who finds an undisclosed mock stops trusting the rest of the repo, while a disclosed boundary reads as engineering judgment.
