# Staff-level transformation tracker

This document records the verified baseline, the confirmed defect register,
the work performed, validation evidence, deferred items, and the final scoring
for the product and engineering transformation.

## Verified baseline (Phase 0)

Environment: Node 20, npm 10, Python 3.12 (matches CI), SQLite for local
backend runs.

| Check | Baseline result |
| --- | --- |
| Frontend clean install | Pass |
| Frontend typecheck (tsc) | Pass |
| Frontend lint (next lint) | Pass |
| Frontend unit tests | 476 passed, 62 files |
| Frontend production build | Passed locally, skipped in CI because next/font/google required network access |
| Backend clean install (Python 3.12) | Pass |
| Backend pytest with coverage | 787 passed, 1 skipped, coverage 92.82 percent (gate 90) |
| Alembic heads | Single head `0003_billing_events` |
| Backend health endpoint | 200, demo_mode true |

Inventory: 91 frontend routes (see `docs/ROUTE_ARCHITECTURE.md`), 37 backend
API modules under `backend/app/api/v1`, 206 backend Python files, 3 Alembic
migrations, 38 frontend API modules, 86 documentation files.

## Confirmed defect register

| ID | Priority | Defect | Status |
| --- | --- | --- | --- |
| D1 | P0 | Browser stored the bearer token in localStorage (`civil_engineer_auth_token`) | Fixed: HttpOnly cookie session with BFF proxy (ADR 0003) |
| D2 | P0 | No CSRF protection existed for a cookie-based session model | Fixed: same-origin check plus custom header gate, tested |
| D3 | P0 | CI skipped the production build (next/font/google network dependency) | Fixed: system font stack; build runs in CI |
| D4 | P0 | React Testing Library cleanup was not configured; test isolation depended on per-file discipline | Fixed: global afterEach cleanup plus storage reset |
| D5 | P0 | `safeFetch()` collapsed all failures into null; six demo modules silently substituted static fixtures | Fixed: typed ApiResult plus explicit DemoSourced model with visible DataSourceNotice (ADR 0002) |
| D6 | P1 | Homepage rendered fabricated operational data: static KPIs, seeded relative timestamps, "Near You" location language, static "All Systems Operational" | Fixed: recruiter-first homepage with fixture-derived case-study facts only |
| D7 | P1 | Two competing navigation systems (homepage sidebar plus global nav); demo modules dominated the first impression | Fixed: single nav, public links only when signed out, workspace links after sign-in, demo module index on /start-here |
| D8 | P1 | Hero image implied a completed luxury neighborhood rather than preliminary review | Fixed: site-plan review hero with synthetic case-study labeling |
| D9 | P1 | `/landing` duplicated the homepage role | Fixed: redirect to `/` |
| D10 | P1 | Mutating API calls lacked a CSRF marker | Fixed: `authHeaders()` adds the marker centrally; all 45 mutating call sites verified |
| D11 | P2 | `models.py` about 3,000 lines; several services over 1,500 lines | Deferred with transitional architecture (ADR 0005) |
| D12 | P2 | Frontend types maintained by hand against backend schemas | Deferred with staged plan (ADR 0004) |
| D13 | P2 | 86 docs with overlapping phase records and stale statements | Fixed: docs index, historical notices on 32 archived records, stale auth and homepage claims corrected |
| D14 | P2 | CLAUDE.md forbade already-implemented features (PDF parsing, DXF, auth, deployment) | Fixed: scope rules updated to match the repository |
| D15 | P2 | Attribution-adjacent phrasing in AI-draft descriptions and literal em dashes in guard tests | Fixed: reworded to AI-drafted, guard tests build strings by concatenation, CI content gate added |
| D16 | P2 | Session cookie lifetime initially mismatched the backend token expiry | Fixed: aligned to AUTH_TOKEN_EXPIRE_MINUTES |

## Phase status

| Phase | Status |
| --- | --- |
| 0 Baseline and inventory | Complete |
| 1 Release engineering integrity | Complete (fonts, CI build, test isolation, check/verify scripts, content gate, migration and import checks in CI) |
| 2 Route and shell architecture | Complete for navigation, classification, and redirects; full route-group shell split documented as follow-up (ADR 0001) |
| 3 Homepage | Complete |
| 4 Data-source boundaries | Complete for the ambiguous-fallback defect and typed results; module-by-module apiFetch migration continues opportunistically |
| 5 Secure session architecture | Complete and verified end to end |
| 6 Design system | Existing component system retained; DemoDataBadge and DataSourceNotice added; full token consolidation deferred |
| 7 Brookside narrative | Existing guided demo retained; homepage now routes one canonical journey into it |
| 8 Backend decomposition | Deferred with transitional architecture (ADR 0005) |
| 9 Observability | Existing health/readiness/diagnostics retained; deployment-status page reads real diagnostics |
| 10 Test strategy | Frontend 488 tests; backend 787 tests at 92.8 percent coverage; CSRF and proxy tests added; Playwright end-to-end suite deferred |
| 11 Performance and accessibility | Build-verified route sizes; homepage reworked with semantic landmarks and labeled sections; formal budget measurement deferred |
| 12 AI and evidence architecture | Existing mock-default provider, evidence-bounded validators, and evaluation cases verified present |
| 13 Documentation | Complete (index, ADRs, route map, archived notices, corrected claims) |
| 14 Recruiter experience | Complete (five-minute and fifteen-minute paths on the homepage and /start-here) |

## Validation results (final)

| Gate | Result |
| --- | --- |
| Frontend typecheck | Pass |
| Frontend lint | Pass |
| Frontend tests | 488 passed, 64 files |
| Content integrity gate (attribution, em dash) | Pass |
| Frontend production build | Pass, no network access required |
| Backend pytest and coverage | 787 passed, 1 skipped, 92.8 percent (gate 90) |
| Alembic single head | Pass (`0003_billing_events`) |
| Application import | Pass |
| Session smoke test (live servers) | Login sets HttpOnly cookie; proxy authenticates; 401 explicit without cookie; cross-origin mutation rejected; logout clears cookies |
| localStorage token | Absent from all non-test source |

## Deferred items and remaining risks

1. Backend domain decomposition (ADR 0005): `models.py` and the four largest
   services remain single modules, protected by the test suite and coverage
   gate. Extraction should proceed one domain per change.
2. OpenAPI type generation (ADR 0004): wire types remain hand-maintained
   behind narrow adapters until the generation pipeline lands.
3. Playwright end-to-end and automated accessibility suites: the documented
   public, authentication, authorization, and failure journeys are covered by
   unit and route-handler tests plus the manual smoke run recorded above, not
   yet by browser automation.
4. Route-group shell separation: navigation is progressive but public and
   authenticated pages share one root layout.
5. Session rotation: tokens expire at 120 minutes; renewal means signing in
   again. A refresh endpoint is future work.

## Final score

Scored against the required rubric. Category evidence lives in the sections
above; deductions reflect the deferred items.

| Category | Score / 10 |
| --- | --- |
| Product clarity | 9 |
| Recruiter experience | 9 |
| Frontend architecture | 8 |
| Backend architecture | 7 |
| Data honesty and integrity | 10 |
| Security and tenancy | 9 |
| Testing and release discipline | 9 |
| Accessibility and performance | 7 |
| Documentation and onboarding | 9 |
| AI governance and professional safety | 10 |
| **Total** | **87 / 100** |

The remaining thirteen points are held by the deferred items above, each of
which has a recorded decision and a staged plan. No P0 or P1 defect remains
open.
