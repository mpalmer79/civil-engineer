# Real vs Mocked

This document removes ambiguity about what is implemented, what is seeded, and what is intentionally bounded. It exists so a recruiter or technical reviewer never has to guess which parts of the demo are real code paths and which parts are curated demo data.

Status labels used below:

- **Implemented**: a real code path backed by the FastAPI backend or working frontend logic.
- **Seeded demo**: synthetic fixture data that exercises a real UI, clearly labeled as demo data.
- **Simulated**: behavior that stands in for a future capability, deterministic and honest about being illustrative.
- **Static prototype**: fixed values chosen for presentation stability.
- **Planned**: named in the roadmap, not built.
- **Out of scope**: deliberately excluded, with the boundary documented.

| Area | Current status | Evidence in repo | Why it is this way | Future production path |
| --- | --- | --- | --- | --- |
| Brookside Meadows project data | Seeded demo | `data/*.ts`, `backend/app/db` seed loaders, `docs/BROOKSIDE_MEADOWS_PROJECT_STORY.md` | A stable synthetic fixture gives every reviewer the same demo with intentionally planted review issues | Real submissions enter through project intake and document upload, which already exist |
| Homepage KPI metrics | Static prototype | Constants in `app/page.tsx` | The homepage is a recruiter-facing snapshot, so the numbers stay stable across visits | Bind to the backend operational metrics API that already powers `/dashboard` |
| Reviewer queue | Implemented, access controlled | `app/dashboard/queue/page.tsx`, `backend/app/services`, `docs/REVIEWER_DASHBOARD_AND_WORKLOAD.md` | Queue data is filtered by per-project access, so real items require sign-in | Assignment and priority foundations exist; richer workload balancing is roadmap work |
| Document review | Implemented plus seeded demo library | Backend upload, registration, and PDF page indexing; `app/documents` shows the seeded package | Real uploads flow through the storage abstraction; the public demo shows a curated document set | OCR for scanned documents is out of scope today and named as future work |
| Evidence citations | Implemented | PDF page indexing (pypdf), page-level citations, deterministic retrieval; `docs/API_EVIDENCE_RETRIEVAL.md` | Citations anchor every finding to a source page, which is the core product idea | Retrieval quality work and live AI assistance are roadmap items |
| DXF and plan review support | Implemented for DXF metadata; plan sheets seeded | ezdxf parsing in the backend, `backend/app/cad_samples`, seeded hotspots in `data/hotspots.ts` | DXF metadata is real and parseable without CAD licenses; geometry validation is a different product | DWG, Autodesk, Civil 3D, GIS, and computer vision are out of scope and documented as such |
| Applicant response packages | Implemented | Response matrix, resubmittal rounds, package issuance, comment letter drafts in the backend; `docs/API_RESPONSE_PACKAGES.md` | Multi-round applicant communication is where review work actually accumulates | Applicant-facing portal is out of scope; the reviewer-side workflow is the foundation |
| Review packet handoff | Seeded demo module in front, implemented issuance in back | `/review-packet` builder uses seeded data; backend response package issuance is real | The packet builder demonstrates handoff structure; issuance records a reviewer communication only | Merge the demo packet builder onto backend-issued packages |
| Audit trail | Implemented plus seeded demo events | Backend audit events with attribution; `data/auditEvents.ts` for the public demo | Decision history must survive, so reviewer actions write durable events | External log shipping and application performance monitoring are future work |
| AI guidance and assistant behavior | Simulated | Mock provider, live AI disabled by default, deterministic retrieval | The demo must run without API keys and never imply AI makes engineering decisions | Live AI retrieval assistance is a roadmap item behind the same human review boundary |
| Authentication and roles | Implemented, local | Sign-in, organizations, reviewer and admin roles, per-project access, guard-regression test | Local auth protects real records without claiming enterprise identity | Enterprise single sign-on and email confirmation are out of scope today |
| Deployment | Implemented | Two Railway services, `railway.json`, health and readiness diagnostics, CI in `.github/workflows/ci.yml`, live URL in the README | A live demo with CI gates is stronger proof than local-only instructions | Production hardening beyond the pilot posture is documented in `RELEASE_READINESS.md` |

## How to use this table

If you have five minutes, read the status column and spot-check one Implemented row against the code. If you have fifteen, follow the evidence column for the rows that matter to you. The point of the table is that nothing here needs to be taken on trust.

None of the rows above, individually or together, make this a licensed engineering review system. Every output is review-support material for a human decision maker.
