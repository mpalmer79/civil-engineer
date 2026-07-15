# Repository Consolidation and Production-Hardening: Validation Report

Internal engineering record. Not customer-facing. Captures the verified state
of the consolidation initiative, what was completed, what was deliberately
deferred, and the evidence behind each claim.

## Scope note and honesty statement

This initiative was executed in staged, individually validated increments. Some
planned decomposition work remains deferred and is tracked here and in the
repository complexity budget (`scripts/check-complexity.mjs`). Nothing in this
report is claimed as complete unless it was verified by the command shown.
Deferred work is listed plainly in the Deferred section rather than hidden.

The system remains a review-support platform. Nothing here changes its
professional boundary: it does not approve plans, certify compliance, stamp
drawings, or replace a licensed Professional Engineer.

## Before and after metrics

Counts are tracked files via `git ls-files`.

| Metric | Before | After | Notes |
|---|---|---|---|
| Tracked files | 805 | 903 | Rose by design. Splitting monoliths into cohesive modules increases file count while lowering per-file cognitive load. |
| TypeScript (.ts) | 106 files / 41,458 lines | 128 / 42,263 | Large API modules became directories. |
| TSX (.tsx) | 308 / 38,745 | 336 / 38,539 | Pages and clients decomposed into sections. |
| Python (.py) | 231 / 62,755 | 270 / 63,477 | Models, safety vocab, and seeds split by domain. |
| Markdown (.md) | 105 / 17,661 | 114 / 18,246 | Added ADRs and internal reports; historical docs then archived and the active set consolidated in the follow-up. |
| npm audit (full tree) | 2 critical, 1 high, 3 moderate | 0 | Verified `npm audit`: found 0 vulnerabilities. |

### Largest authored modules: before and after

| Module | Before | After |
|---|---|---|
| backend/app/db/models/core.py | 2,330 | removed; split into 13 domain modules, each <=346 lines |
| backend/app/core/safety.py | 1,380 | 112 (guardrail language) plus `app/core/vocab/` package, each <400 |
| backend/app/db/seed.py | 1,478 | thin facade plus `app/db/seeds/` package by domain |
| lib/api/cadIntake.ts | 1,245 | `lib/api/cadIntake/` (types, queries, mutations, mappers), each <360 |
| lib/api/reviewCycle.ts | 721 | `lib/api/reviewCycle/` package |
| lib/api/responsePackages.ts | 684 | `lib/api/responsePackages/` package |
| lib/api/reviewPackets.ts | 632 | `lib/api/reviewPackets/` package |
| app/proof-of-concept/page.tsx | 844 | 51 (composition over `components/proof/`) |
| app/page.tsx | 525 | 33 (composition over `components/home/`) |
| components/TraceabilityMatrix.tsx | 543 | 134 plus `components/traceability/` |
| components/ReviewCyclesClient.tsx | 498 | 201 plus `components/review-cycles/` |
| components/CadIntakePage.tsx | 492 | 272 plus `components/cad-intake/` |
| components/HumanReviewClient.tsx | 467 | 160 plus `components/human-review/` |

### Generated files isolated

`lib/api/generated/schema.d.ts` (20,576 lines) and `lib/guide/generated/repo-facts.json`
are marked generated and excluded from the complexity budget and manual
complexity reporting.

## Dependency remediation (completed and verified)

- Frontend toolchain migrated as one coordinated change: vitest 2 to 4,
  vite to 7 (via vitest), `@vitejs/plugin-react` to 4.7, `@vitest/coverage-v8`
  to 4, eslint 8 to 9 with flat config, typescript 5.5 to 5.9.
- `next lint` replaced with a direct ESLint CLI invocation and flat config.
- Backend dependencies upgraded to clear all pip-audit findings.
- CI now runs full-tree `npm audit --audit-level=high`, production-only
  `npm audit --omit=dev`, and `pip-audit -r requirements.txt` as release gates.
- Rationale and any exceptions recorded in `docs/internal/DEPENDENCY_REMEDIATION.md`.

Verification: `npm audit` reports 0 vulnerabilities.

## Backend decomposition

Completed and verified (907 passed, 1 skipped):

- `db/models/core.py` split into 13 bounded-context modules under
  `app/db/models/`, table names, columns, relationships, constraints, and
  enum values preserved byte-for-byte. Single Alembic head retained
  (`0003_billing_events`). Import surface preserved via `app/db/models/__init__.py`.
- `core/safety.py` reduced to the canonical guardrail module; 111 status and
  transition vocabularies moved to `app/core/vocab/` and re-exported, so every
  import site is unchanged.
- Seed data split into `app/db/seeds/` by domain with Brookside Meadows
  isolated as an optional reference dataset. Production startup does not
  depend on the reference project.

All oversized service modules were subsequently split into bounded-context
packages in the follow-up. See the Follow-up completion section for the full
list and the remaining deferred items.

## Frontend decomposition and repositioning (completed and verified)

- Four largest `lib/api` modules converted to directories split by
  responsibility; import specifiers preserved.
- `app/page.tsx` and `app/proof-of-concept/page.tsx` reduced to composition
  layers over per-section server components with typed content modules.
- Four large client components decomposed, preserving props, accessibility,
  keyboard behavior, and loading/empty/error/unavailable states.
- Recruiter and portfolio framing removed from the homepage, start-here page,
  and footer; replaced with professional evaluation pathways. Brookside
  Meadows presented as a synthetic reference project. `/landing` kept as a
  permanent redirect to `/`.

Verification: typecheck, lint, unit tests, coverage floors, production
build, and content integrity gate all pass.

## Quality gates added

- `scripts/check-complexity.mjs`: warns at 300 (TS/TSX) and 400 (Python),
  fails at 500 and 700. Generated files and migrations exempt. A small
  cohesion allowlist and a visible, shrink-only deferred-split registry keep
  the gate honest while preventing new oversized files.
- CI wired to run the complexity budget, full-tree and production npm audits,
  and pip-audit.

## Validation results (this branch)

| Gate | Command | Result |
|---|---|---|
| Frontend typecheck | `npm run typecheck` | pass |
| Frontend lint | `npm run lint` | pass |
| Frontend unit tests | `npm run test` | 549 pass |
| Coverage floors | `npm run test:coverage` | pass (statements 52.2%, branches 42.8%, functions 47.6%, lines 53.5%; all above committed floors) |
| Production build | `npm run build` | pass |
| Content integrity | `npm run check:content` | pass |
| Complexity budget | `node scripts/check-complexity.mjs` | pass |
| Full-tree npm audit | `npm audit` | 0 vulnerabilities |
| Backend imports | `python -c "from app.main import app"` | ok |
| Backend tests | `pytest -q` | 907 pass, 1 skip |
| Alembic head | single head check | `0003_billing_events` |
| API contract | `node scripts/generate-api-types.mjs --check` | current |
| DXF deterministic proof | `scripts/run_dxf_proof.py` | artifacts unchanged |

## Follow-up completion (PR after #75)

The items deferred in PR #75 were completed in the follow-up branch and are
recorded here for a single authoritative account.

Completed in the follow-up:

- All remaining oversized backend services were split into bounded-context
  packages, each file under the 700 line ceiling: cad_intake_service,
  review_cycle_service, evidence_retrieval_service, response_package_service,
  reviewer_response_package_service, review_packet_service, workflow_service,
  command_center_service, traceability_service, checklist_review_service,
  real_intake_service, access_control_service, environment_validation_service.
- The `api/v1/review_cycle` router was split by resource with identical route
  count, paths, methods, status codes, and response models.
- `lib/api/realProjects.ts` and `lib/api/workflow.ts` were split into
  responsibility directories.
- Documentation was consolidated into the canonical set (PRODUCT, ARCHITECTURE
  rewritten from about 1,400 lines to roughly 200, SECURITY, OPERATIONS,
  DEPLOYMENT, TESTING, API, DXF_VALIDATION, REFERENCE_PROJECT, ROADMAP, plus
  the retained DOMAIN_MODEL and route map). 89 historical documents were moved
  to `docs/archive/` with git history preserved, and all load-bearing
  references (guide catalog, route context, doc-assertion tests, verification
  scripts, admin links, and source comments) were repointed.

## Deferred work (tracked, not hidden)

Registered in `scripts/check-complexity.mjs` under `DEFERRED_SPLIT` and the
cohesion allowlist. Each is a size or test-structure item, not a capability gap.

1. `app/__tests__/evidenceRetrieval.test.tsx` (720 lines) split by behavior
   (search, ranking, filters, citations). Remaining `DEFERRED_SPLIT` entry.
2. Seed fixtures `backend/app/db/seeds/plan_sheets.py` and `evidence.py`, and
   the curated `lib/guide/knowledge.ts` catalog, remain on the cohesion
   allowlist: they are reviewed as data, not logic, and a split would only
   fragment them.
3. Observability and background-processing work described in OPERATIONS and the
   ROADMAP Deferred section: structured request-correlated logging, moving file
   and DXF processing to background workers, and raising coverage floors.

## Readiness assessment

- Internal engineering review: ready. Architecture is documented in the
  canonical ARCHITECTURE document and ADRs; every oversized module named in the
  baseline has been decomposed and validated.
- Customer demonstration: ready. The product reads professionally; recruiter
  and portfolio framing is gone; the reference project is labeled synthetic.
- Controlled pilot: conditional. The service-layer decomposition and
  documentation consolidation are now complete. Recommended before pilot: add
  the observability items (structured request-correlated logging, background
  workers for file and DXF processing) from OPERATIONS and the ROADMAP.
- Production use: not yet. File processing remains request-bound; background
  workers and structured request-correlated logging should land first. See
  ROADMAP Deferred.

## Known remaining risks

- File and DXF processing runs on the request thread; enterprise-scale load
  should move it to a background worker.
- Coverage floors are modest; raising them is tracked in the ROADMAP.
- One UI test file remains above the size ceiling (tracked in the deferred
  registry); it is a test-structure item, not a behavior risk.
