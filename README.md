# Civil Engineer AI: Stormwater Review Assistant

Civil Engineer AI is a portfolio GenAI system that assists stormwater and
site-plan review using document evidence, checklist validation, risk flagging,
human review, audit logging, and evaluation tracking.

It is a **review-support and evidence-organization** prototype for land
development workflows. It is **not** a licensed engineering tool and does not
replace professional engineering judgment.

> **Professional boundary.** Civil Engineer AI assists review. It does not
> approve plans, certify compliance, stamp or seal drawings, replace a licensed
> Professional Engineer, or make final safety determinations. Every finding is a
> review-support issue that needs reviewer confirmation.

---

## Current phase: Phase 1 — Static Portfolio Prototype

Phase 1 is a polished, **static** Next.js prototype driven entirely by seeded
mock data. It demonstrates the product vision, domain depth, and future
architecture — with **no live AI calls, backend, database, or authentication.**

The prototype reviews a single fictional fixture: **Brookside Meadows**, a
47-lot single-family subdivision in the Town of Hartwell with a green-and-gray
stormwater treatment train and ten intentionally planted review issues.

![Brookside Meadows development map](public/development.png)

The homepage hero uses `public/development.png` as an interactive development
map: HTML/CSS hotspot markers overlay the image, and a side panel updates as you
hover, focus, or select each site feature. See
[`docs/HOMEPAGE_HOTSPOT_PLAN.md`](docs/HOMEPAGE_HOTSPOT_PLAN.md).

---

## Routes

| Route | Page | Purpose |
| --- | --- | --- |
| `/` | Home | Hero map, metrics, how it works, professional boundary, future modules |
| `/project` | Project dashboard | Brookside Meadows summary, site conditions, improvements, constraints |
| `/documents` | Document library | The seeded submission package with status and planted issues |
| `/checklist` | Stormwater checklist | 19 structured review items with expected statuses |
| `/findings` | Findings | The 10 expected review-support findings |
| `/audit` | Audit trail | Seeded, traceable review history |
| `/evaluation` | Evaluation dashboard | 8 evaluation cases with recall and citation metrics |

---

## Tech stack

- **Next.js 14** (App Router) + **React 18**
- **TypeScript** (strict)
- **Tailwind CSS**
- Static seed data in TypeScript under `data/`
- No backend, database, AI calls, or auth in Phase 1

---

## Getting started

```bash
npm install
npm run dev      # start the dev server at http://localhost:3000
npm run build    # production build (all routes prerender as static content)
npm run typecheck
```

---

## Project structure

```text
civil-engineer/
├── app/              # App Router pages (home, project, documents, checklist, findings, audit, evaluation)
├── components/       # Reusable UI (HeroMap, badges, tables, cards, banners)
├── data/             # Static seed data (brookside, documents, checklist, findings, audit, evaluation, hotspots)
├── public/
│   └── development.png   # Hero / interactive map base image
└── docs/             # Phase 0 foundation + Phase 1 hotspot plan
```

---

## Documentation

- [`docs/PHASE_0_FOUNDATION.md`](docs/PHASE_0_FOUNDATION.md) — product definition and boundaries
- [`docs/BROOKSIDE_MEADOWS_PROJECT_STORY.md`](docs/BROOKSIDE_MEADOWS_PROJECT_STORY.md) — the review fixture
- [`docs/DOMAIN_MODEL.md`](docs/DOMAIN_MODEL.md) — core entities and ER diagram
- [`docs/V1_SCOPE.md`](docs/V1_SCOPE.md) — in / out of scope and success criteria
- [`docs/ROADMAP.md`](docs/ROADMAP.md) — staged path from foundation to platform
- [`docs/SEED_DATA_PLAN.md`](docs/SEED_DATA_PLAN.md) — seed-ready data
- [`docs/HOMEPAGE_HOTSPOT_PLAN.md`](docs/HOMEPAGE_HOTSPOT_PLAN.md) — interactive map plan
- [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) — system architecture
- [`docs/RESEARCH_AND_SYSTEM_DESIGN.md`](docs/RESEARCH_AND_SYSTEM_DESIGN.md) — research basis

---

## What Phase 1 proves

- The product story is immediately understandable: an evidence-first stormwater
  review assistant for a realistic subdivision.
- The review is **structured** (a checklist), **evidence-based** (a document
  package), and **human-controlled** (findings need reviewer confirmation).
- The system is designed for **auditability** and **evaluation** from the start.
- The professional boundary holds throughout — no page claims the system
  approves, certifies, or confirms compliance.
- Stormwater is module one of a broader land development platform.

## What comes next

- **Phase 2** — FastAPI backend, PostgreSQL schema, seed scripts, and read APIs
  wired to this frontend.
- **Phase 3** — document chunking, embeddings, and source-evidence retrieval.
- **Phase 4** — the AI review assistant (structured prompts, JSON validation,
  safety checks, human review required).
- **Phase 5** — the live evaluation harness.

See [`docs/ROADMAP.md`](docs/ROADMAP.md) for the full plan.
