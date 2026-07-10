# Recruiter Walkthrough

This walkthrough is designed for a five-minute review of Civil Engineer AI. It focuses on the Brookside Meadows synthetic subdivision demo, the evidence-first stormwater review workflow, applicant response tracking, and reviewer-controlled handoff.

- Live demo: https://civil-engineer.up.railway.app/
- Quick review: 5 minutes using the route sequence below.
- Deeper technical review: 15 minutes, adding the code inspection points at the end.

Everything in the demo is review-support work. The system organizes evidence for a human reviewer. It does not approve plans, certify compliance, or replace a licensed Professional Engineer. Brookside Meadows is synthetic demo data, not a real submission.

## Five-minute route sequence

### 1. Homepage

- Route: `/`
- What you see: the Brookside Meadows hero image, a short project description, proof chips, calls to action, KPI cards, and operational dashboard widgets.
- What it demonstrates: recruiter-first information design, responsive layout, accessible landmark structure, and a working dashboard composition in a single App Router page.
- Why it matters: the page explains the project before showing metrics, which is a product decision, not just a layout choice.

### 2. Guided Demo

- Route: `/guided-demo`
- What you see: a step-by-step reviewer journey through the Brookside Meadows sample project.
- What it demonstrates: workflow decomposition of a real review discipline into ordered, linked product surfaces.
- Why it matters: it shows domain modeling judgment, since each step maps to work a stormwater reviewer actually does.

### 3. Projects

- Route: `/projects`
- What you see: the project workspace with the seeded Brookside Meadows project and the entry point for real project records.
- What it demonstrates: the split between a public seeded demo and access-controlled real records backed by the FastAPI backend.
- Why it matters: it shows the project is more than static pages; there is a real data model behind it.

### 4. Reviewer Queue

- Route: `/dashboard/queue`
- What you see: the reviewer queue surface. Real queue items require sign-in because queue data is access controlled.
- What it demonstrates: role-aware, access-controlled operational tooling rather than a single shared dashboard.
- Why it matters: workload management is where review tools succeed or die in practice.

### 5. Documents and Findings

- Routes: `/documents`, then `/findings`
- What you see: the submitted document package, then the expected review-support findings with risk levels and evidence links.
- What it demonstrates: evidence-first review. Each finding links back to source material instead of standing alone as an assertion.
- Why it matters: traceability is the core value of the product and the hardest part to fake.

### 6. Response Package

- Route: `/response-package`
- What you see: a draft external response grouped by topic with editable wording and a human review sign-off checklist.
- What it demonstrates: applicant-facing communication workflow with reviewer control at every step.
- Why it matters: multi-round applicant response tracking is the messy real-world part of plan review.

### 7. Review Packet

- Route: `/review-packet`
- What you see: the review-support packet builder that assembles documents, checklist items, findings, and audit evidence.
- What it demonstrates: structured handoff preparation, where the output is a package for a human decision maker.
- Why it matters: the product ends at handoff on purpose. The decision itself stays with a licensed engineer.

### 8. Human Review and Audit

- Routes: `/human-review`, then `/audit`
- What you see: the reviewer action queue for AI draft findings, then the audit trail of reviewer actions.
- What it demonstrates: the human-in-the-loop boundary implemented as product surfaces, plus decision history preservation.
- Why it matters: this is where the professional boundary is enforced in the UI, not just claimed in the README.

## Where the human review boundary appears

- The homepage guidance line: AI provides review support. You make the decisions. Every review is human.
- The safety boundary banner on demo module pages.
- The human review queue at `/human-review`, where every AI draft finding waits for a reviewer action.
- The sign-off checklist inside the response package builder.
- The backend safety vocabulary, which is enforced by tests.

## Fifteen-minute code inspection points

1. `app/page.tsx`: the recruiter-first homepage, typed constants, semantic sections.
2. `lib/api/`: the typed API client modules and the graceful fallback to seeded data when the backend is unreachable.
3. `data/`: the seeded Brookside Meadows fixtures used for the public demo.
4. `backend/app/services/` and `backend/app/api/v1/`: one service and router per capability.
5. `backend/app/core/`: settings and the review-support safety vocabulary.
6. `app/__tests__/` and `backend/tests/`: content-contract tests, component tests, and the backend suite with a coverage gate.
7. `.github/workflows/ci.yml`: the CI gates that run on every push.

For the full capability map, see [real-vs-mocked.md](real-vs-mocked.md). For what the data represents, see [synthetic-demo-data.md](synthetic-demo-data.md).
