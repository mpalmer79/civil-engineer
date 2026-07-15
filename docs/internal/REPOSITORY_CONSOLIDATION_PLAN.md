# Repository Consolidation Plan

Internal engineering document. Companion to REPOSITORY_CONSOLIDATION_BASELINE.md. This plan governs the consolidation and production-hardening initiative executed on this branch.

## 1. Target architecture

Backend (FastAPI): keep the existing layering (api/v1 routers, services, schemas, db) and decompose the oversized modules by bounded context instead of introducing a parallel tree.

- db/models becomes a domain-split package (identity, billing, cad, command_center already extracted): projects, documents, evidence, checklists, findings (AI review, evaluation), plans (plan sheets and consistency), review_packets, workflow, response_packages, responses (matrix, reviewer packages, comment letters), review_cycles, audit. models/__init__.py remains the compatibility facade re-exporting every class so the dominant `from app.db import models` style keeps working and Alembic metadata registration is unchanged.
- core/safety.py becomes a vocabulary package: per-domain status vocabularies move to core/vocab/<domain>.py; the guardrail language and helper functions stay canonical in one module; safety.py remains the stable import facade re-exporting the existing names.
- The three largest services (cad_intake, review_cycle, evidence_retrieval) become packages whose __init__ re-exports the public functions, with cohesive submodules (uploads, parsing, findings, queue/dashboards; lifecycle, resubmittals, comparison, carry-forward; search, chunks, candidates).
- Seeds move to db/seeds/ with an orchestrator and per-domain fixture modules; seed.py remains a facade.
- Transaction ownership convention: services own commits; routers must not commit. Documented in the consolidation ADR; the small number of router commit sites are migrated where low-risk.
- Reference-project isolation: the public demo project ID moves from a hard-coded service constant to configuration (default preserved). The `expected_status_for_brookside_meadows` column is retained as a legacy contract name and documented; renaming it is deferred because it is a database column and generated-contract field.

Frontend (Next.js App Router): decompose in place rather than a wholesale move to a features/ tree, to avoid churning 300+ imports and route behavior. New structure conventions:

- Oversized lib/api modules become directories (lib/api/cadIntake/ with types.ts, queries.ts, mutations.ts, index.ts preserving the `@/lib/api/cadIntake` specifier).
- A shared `postJson`/`patchJson`/`deleteJson` mutation helper joins lib/api/client.ts, replacing the nine per-module copies.
- app/page.tsx and app/proof-of-concept/page.tsx become composition layers over per-section components (components/home/, components/proof/), each section under 300 lines.
- The largest client components extract pure transformations and panel subcomponents.
- Generated artifacts stay isolated under lib/api/generated/ and lib/guide/generated/ with generated-file headers (already true); they are exempt from complexity budgets.

## 2. Migration order

1. Baseline and plan documents (this change).
2. Dependency and toolchain remediation: vitest 4, coverage-v8 4, plugin-react 4.7, vite 7 pinned, eslint 9 with flat config and direct CLI, typescript 5.9, backend fastapi/starlette/python-multipart/pytest upgrades. Full validation after.
3. Backend model split, safety vocabulary split, seed split, reference-project configuration decoupling. Backend tests plus contract freshness after.
4. Backend service decomposition (cad_intake, review_cycle, evidence_retrieval; review_cycle router slimming if low-risk). Backend tests plus DXF proof after.
5. Frontend decomposition (API modules, pages, large components) and shared mutation helper. Frontend validation after.
6. Product repositioning: README, homepage, start-here, footer, guide catalog, route dispositions (/landing removal with redirect preserved). Frontend validation plus content gates after.
7. Documentation consolidation per DOCUMENTATION_DISPOSITION.md: canonical docs, archive moves, reference updates (guide knowledge, tests, scripts, CI comments). Guide freshness and doc tests after.
8. Quality gates: complexity budget script, CI additions (full-tree audit gate, pip-audit, complexity check), CLAUDE.md architecture rules.
9. Final validation, REFACTOR_VALIDATION_REPORT.md, push, pull request.

## 3. Dependency boundaries

- Routers depend on services and schemas; services depend on models, vocab, storage; no service imports a router; no model imports a service. The complexity check script also guards file size; import-boundary enforcement beyond Python's import graph is documented convention.
- Frontend: components depend on lib/api and lib domain helpers; lib/api depends only on client.ts and generated types; no app/api route imports UI components.

## 4. Compatibility strategy

- models/__init__.py, safety.py, seed.py, and each split service package __init__ re-export the pre-split public names, so the 106 `models.X` sites, the safety importers, and service call sites do not change.
- All existing public URLs keep working: /landing becomes a next.config.mjs permanent redirect; /proof-of-concept remains canonical (its copy is reframed as technical validation); /poc and /proofofconcept redirects are retained.
- Table names, column names, constraints, and the Alembic chain (3 migrations, single head) are unchanged by module moves.
- The OpenAPI contract must remain byte-identical through the backend refactor (CI contracts job verifies).

## 5. Test strategy

- Run the full backend suite (906 tests) after each backend phase; full frontend suite (549 tests), typecheck, lint, and build after each frontend phase; DXF proof harness after CAD service changes; content and guide gates after documentation changes.
- Coverage ratchets are preserved: backend cov-fail-under 90; frontend thresholds re-baselined only if the vitest 4 measurement changes, never below documented floors without a note in the validation report.
- Doc-assertion tests (recruiterDocs and friends) are rewritten to assert the new canonical set rather than deleted.

## 6. Rollback strategy

Each phase is a separate commit on this branch with green validation. A regression discovered later reverts the offending phase commit without unwinding the rest. No destructive migration or history rewrite is performed anywhere, so rollback is always a git revert.

## 7. Documentation disposition

See docs/internal/DOCUMENTATION_DISPOSITION.md for the per-file matrix (canonical set, merges, archive moves, reference updates).

## 8. Route disposition

See docs/internal/ROUTE_DISPOSITION.md for the canonical route map, compatibility redirects, and reference-project-only surfaces.

## 9. File decomposition plan

Backend targets: models/core.py into ~12 domain modules under 400 lines each; safety.py into vocab package with a thin facade; cad_intake_service into uploads/parsing/findings/insights modules; review_cycle_service into lifecycle/resubmittals/comparison/carry_forward/dashboard modules; evidence_retrieval_service into page_search/chunk_search/candidates modules; seed.py plus seed_plansheets.py plus seed_evidence.py under db/seeds/.

Frontend targets: cadIntake.ts, reviewCycle.ts, responsePackages.ts, reviewPackets.ts into api directories with types/queries/mutations; app/page.tsx and proof-of-concept/page.tsx into section components; TraceabilityMatrix, ReviewCyclesClient, CadIntakePage, HumanReviewClient decomposed.

Heuristic budgets (enforced by scripts/check-complexity.mjs): warning 300 and failure 500 lines for TS and TSX; warning 400 and failure 700 lines for Python; generated files, migrations, and an explicit allowlist exempt.

## 10. Risk register

| Risk | Likelihood | Impact | Mitigation |
| --- | --- | --- | --- |
| Missed model re-export breaks Alembic autogenerate or a test import | medium | high | facade re-export test; full suite after split |
| vitest 4 changes coverage measurement below ratchets | medium | medium | re-baseline with documented note |
| fastapi/starlette upgrade changes response details tests assert on | medium | medium | full suite; pin compatible versions |
| Doc moves break guide freshness gate or doc tests | high | medium | update references in the same commit; run gates |
| DXF proof artifacts drift | low | high | run proof harness; keep pipeline byte-stable |
| OpenAPI contract drift from backend moves | low | high | CI contracts check after each backend phase |
| Copy rewrite introduces forbidden decision language or em dashes | medium | low | content-integrity gate in every validation pass |

## 11. Completion criteria

- npm audit: 0 critical, 0 high (full tree); production tree 0.
- pip-audit: 0 critical/high-equivalent findings on direct requirements (documented exception only if unavoidable).
- typecheck, eslint CLI, frontend unit tests with coverage, production build, backend pytest with coverage floor, single Alembic head, clean migration to head, contract freshness, DXF proof, guide freshness, content integrity: all pass.
- No customer-facing recruiter or portfolio framing.
- Canonical documentation set active; phase and sprint histories archived with an archive README.
- Largest authored modules materially reduced; complexity budget script wired into CI with a small allowlist.
- All deliverable reports present under docs/internal and docs/adr.
