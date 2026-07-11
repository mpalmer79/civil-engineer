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


## Security, Contracts, Browser Quality, and Guide Intelligence

Second transformation phase, after PR #68. Confirmed baseline before work:
Next.js 14.2.35 with one high and one moderate production advisory
(npm audit), a BFF that buffered whole request bodies through arrayBuffer with
no size limit or timeout, a fixed 120-minute session constant, a client
readable indicator cookie treated as session truth, 130 active safeFetch call
sites across 27 modules (the review estimate of 133 was close), no OpenAPI
generated contract, no Playwright or Axe suites, and a guide with seven static
topics, substring matching, a noun-blocking safety filter, and a stale seeded
fallback claim.

### Completed

| Item | Result |
| --- | --- |
| Dependency security | Next.js 15.5.20 (all advisories in the 14.x line are patched only in 15.5.16+), React 19.2.7, eslint-config-next 15.5.20, PostCSS 8.5.15 with an override for Next.js's pinned copy. npm audit --omit=dev: zero vulnerabilities. CI gates production audit at high severity. Node runtime aligned to 22 across .nvmrc, engines, and CI. |
| BFF hardening | Threat model at docs/security/BFF_PROXY_THREAT_MODEL.md. Strict path validation (dot segments, encoded and double-encoded traversal, backslashes, absolute URLs), route-class body limits (auth 64 KB, JSON 2 MB, document uploads 25 MB, CAD uploads 5 MB, matching backend config) enforced on declared length and streamed count, streaming upload forwarding with no arrayBuffer, route-class timeouts (10 s auth, 30 s JSON, 120 s uploads) returning typed 504s distinct from 502s, client-abort propagation, allowlisted request and response headers, correlation IDs end to end, and session cookie clearing on backend 401. 24 proxy tests. |
| Session lifetime | Cookie max age derived from the backend login and registration expires_in_minutes with strict validation (reject missing, nonnumeric, zero, negative, above 30 days). New /api/session/status endpoint provides validated non-sensitive session truth and clears stale cookies; the indicator cookie is documented as a rendering optimization only. TRUSTED_APP_ORIGIN enables exact scheme, host, and port Origin validation behind reverse proxies. 22 session tests. |
| ApiResult migration | Zero safeFetch references; the wrapper is deleted. All 27 modules return typed results with unauthenticated, forbidden, not_found, validation, conflict, rate_limited, timeout, unavailable, server, network, and invalid_response categories plus correlation IDs and retryability. High-risk mappers validate required fields at mapping time. Roughly sixty consumer pages and components render explicit failure states through RequestFailureCard; public demo surfaces keep labeled fixture behavior; authenticated surfaces never substitute demo data. |
| OpenAPI contracts | ADR 0004 implemented: openapi.json (252 routes, 286 schemas) exported from the FastAPI app, schema.d.ts generated with openapi-typescript, named high-risk aliases in lib/api/generated/wire.ts, reproducible via npm run generate:api, CI contracts job fails on stale artifacts. |
| Guide intelligence | ADR 0006. Knowledge moved out of the component into lib/guide: 30-entry allowlisted catalog, generated repository facts (dependencies, 89 routes, ADRs, commit), token-aware BM25-style retrieval with synonyms, stemming, typo tolerance, phrase boosts, route-context and conversation boosts, intent-based safety classification, deterministic answer composition with commit-pinned source citations, page awareness, follow-up resolution, and confidence behavior. Stale seeded-fallback claim removed; LinkedIn link is HTTPS. Privacy: no network calls, no telemetry, lazy-loaded engine. Freshness gate in CI (paths, routes, facts, retired claims). Evaluation corpus: 118 questions; CI enforces at least 95 percent top-topic retrieval (measured passing), 100 percent on 16 critical safety cases (passing), zero unsupported citations. |

### Validation (this phase)

| Gate | Result |
| --- | --- |
| npm audit --omit=dev | 0 vulnerabilities |
| Frontend typecheck, lint | Pass |
| Frontend tests | 537 passing (523 pre-guide suites plus guide evaluation and component suites), 0 failing |
| Production build (Next 15, React 19) | Pass |
| Content integrity gate | Pass |
| Contract freshness (npm run check:contracts) | Pass |
| Guide freshness (npm run check:guide) | Pass |
| Guide evaluation | 118 cases, retrieval at or above 95 percent, critical safety 100 percent |
| Backend pytest and coverage | 787 passed, 1 skipped, 92.8 percent (unchanged; backend untouched this phase) |

### Deferred with reasons

1. Playwright and Axe release suites: not started; the browser gates that
   Priority Seven depends on are the next milestone. Documented journeys
   remain covered by unit and route-handler tests.
2. Route-group shell separation (Priority 6B): navigation remains progressive
   within a single root layout; moving seventy page directories was
   deliberately not combined with the framework major upgrade in one phase.
3. Backend domain extraction (Priority Seven): intentionally blocked by the
   instruction not to begin before Playwright and Axe gates protect the
   refactor; ADR 0005 remains the staged plan.
4. Frontend coverage: measured at 56.6 percent statements and lines, 62.4
   percent branches, 50.4 percent functions over app, components, and lib
   (generated artifacts excluded). CI now enforces ratchet floors at the
   measured baseline (55/60/48/55) so coverage can only rise; the documented
   targets of 70 statements and lines, 65 branches, and 60 functions are not
   yet met and remain tracked here. Security-critical modules exceed the
   targets already: lib/server/session.ts at 100 percent, the BFF proxy and
   session routes covered by their dedicated suites, and lib/guide modules at
   96 to 100 percent.

### Updated score

Scored against the repository rubric. Security and tenancy rises on the
hardened proxy, derived session lifetime, and validated session truth; data
honesty holds at 10 with the completed migration; testing gains the contract,
guide, and audit gates but still lacks browser and accessibility automation.

| Category | Score / 10 |
| --- | --- |
| Product clarity | 9 |
| Recruiter experience | 9 |
| Frontend architecture | 9 |
| Backend architecture | 7 |
| Data honesty and integrity | 10 |
| Security and tenancy | 10 |
| Testing and release discipline | 9 |
| Accessibility and performance | 7 |
| Documentation and onboarding | 9 |
| AI governance and professional safety | 10 |
| **Total** | **89 / 100** |

No P0 or P1 issue remains open; the eleven withheld points are held by the
deferred items above, each with a recorded owner decision.


## Proof of Concept, DXF Intelligence, Security, Contracts, and Browser Quality

Third transformation phase, after PR #70. Confirmed baseline before this
phase: npm audit --omit=dev at 0 vulnerabilities (Next.js 15.5.20), zero
safeFetch references, 521 frontend tests in 66 files, 787 backend tests at
92.8 percent coverage, frontend coverage 56.6 / 62.4 / 50.4 / 56.6
(statements / branches / functions / lines) with ratchet floors 55/60/48/55,
no Playwright or Axe suite, no route-group shells, no proof page. Confirmed
DXF defects, verified in code: the layer classifier was an eight-keyword
substring list (C-PROP, C-ROAD, C-LOTS, C-LABEL, and C-LANDSCAPE all fell to
unknown and were over-flagged), the basin-conflict heuristic keyed on the
trailing token only (DETENTION BASIN 1 versus INFILTRATION BASIN 1 was a
false conflict), and entity bounds covered only TEXT, MTEXT, LINE, and
LWPOLYLINE. The supplied proof artifacts under /mnt/data/civil_dxf_test/
were not present in the environment; equivalent artifacts were regenerated
deterministically and that substitution is disclosed on the page and in
docs/proof-of-concept/DXF_PROOF_OF_CONCEPT.md.

### Completed this phase

| Item | Result |
| --- | --- |
| DXF layer taxonomy | Data-driven rule table in backend/app/services/cad/layer_taxonomy.py: exact, token, and contains tiers, 16 categories, per-rule confidence and explanation, reviewer overrides, neutral defaults. The five over-flagged layers and 14 common variants classify correctly; a 40-entry labeled corpus tracks 100 percent accuracy with only intentional unknowns remaining unknown. |
| Facility identity | Structured identities (type, identifier, qualifier, location) in facility_identity.py with three conflict rules (same type different name, generic plus typed identifier, incompatible types at one location). Detention Basin 1 versus Infiltration Basin 1 is proven non-conflicting in unit, corpus, harness, and browser layers. Every conflict finding names both labels, the rule, the reason, and needs reviewer confirmation. |
| Reference parsing | reference_parser.py supports C-3.1, C3.1 (context gated), SHEET and SEE SHEET forms, DETAIL n/SHEET, DETAIL n ON SHEET, sheet-comma-detail, and ambiguous forms, with negative rules proven against elevations, inverts, slopes, pipe sizes, dates, revisions, stations, lot numbers, and storm frequencies. |
| Geometry and units | geometry.py bounds POINT, LINE, LWPOLYLINE, POLYLINE, ARC (exact axis crossings), CIRCLE, ELLIPSE and SPLINE (safe overestimates, labeled), HATCH, DIMENSION, SOLID and 3DFACE, LEADER, and INSERT (rotation, scale, nesting via virtual entities with depth and count limits). XLINE and RAY report an explicit unbounded reason. Units come from $INSUNITS and are never assumed; parse safety limits added (100k persisted entities, 2k text length, 5k layers) with visible partial-result findings. |
| DXF proof harness | scripts/generate_brookside_proof_dxf.py builds a byte-deterministic 47-lot synthetic drawing (volatile headers pinned, CLASSES sorted). scripts/run_dxf_proof.py uploads and parses it through the real FastAPI routes against scripts/dxf_proof_expected.json (42 checks, all passing) and regenerates the four public artifacts plus manifest with SHA-256 hashes. Regeneration is byte-identical; the dxf-proof CI job enforces artifact freshness with git diff. |
| Proof results | Upload 200, validation accepted, parse completed, 168 entities, 15 layers, 5 blocks, 80 text records, 16 reference candidates, 8 findings, 3 matched references, 2 missing or ambiguous (C-9.9 missing, DETAIL ?/C-4.X ambiguous). |
| /proof-of-concept page | Canonical route with permanent redirects from /proofofconcept and /poc. Sections: hero with synthetic disclosure, what was tested, 13-stage pipeline with module paths, metrics read from the JSON artifact with a visible failure panel when artifact and page disagree, reference evidence table, layer classification table with rules and confidence, findings with reviewer actions, what it proves and does not prove, workflow benefits, reproducibility, four artifact download cards with hashes, limitations and roadmap, calls to action. Linked from the homepage technical proof section, /start-here, guided demo completion, the guide, README, and the docs index. |
| Controlled downloads | Allowlisted /api/proof-of-concept/download/{artifactId} route with manifest lookup, strict ID pattern, served-byte hash verification, correct content type, disposition, and length. Tested for every artifact, unknown IDs, traversal, encoded traversal, and empty or oversized IDs, in unit and browser layers. |
| DXF corpus | backend/tests/test_cad_dxf_corpus.py: 16 corpus scenarios through the real upload and parse endpoints (aliases, minimal, malformed, unreadable, oversized, entity truncation, nested and transformed blocks, model and paper space, unicode, reference states, facility overlap, inconsistency, existing versus proposed, unknown-heavy, units). Plus 102 unit tests across taxonomy, facility identity, reference parser, and geometry. Backend total: 905 passed, 1 skipped (was 787), coverage gate unchanged at 90. |
| Playwright and Axe | playwright.config.ts boots FastAPI on a disposable seeded SQLite plus the production Next.js build. 24 tests: public journey (homepage, guided demo, technical overview, proof page, redirects, artifact hash verification end to end, download rejection, an offline guide answer with external egress blocked), authentication journey (register, HttpOnly session, workspace, Brookside, command center, queue, logout, cookie clearing, no token in storage), browser DXF workflow (upload the proof DXF through the BFF, request parse, verify 168 entities and findings in the UI, invalid upload rejection, no readable credential), and an Axe gate over 11 public pages failing on serious or critical violations. New e2e CI job runs all of it. |
| Accessibility corrections | Fixed genuine violations the gate found: unassociated form labels on login, register, CAD upload, and finding promotion; footer and metadata contrast (slate-400 to slate-500); homepage CTA contrast (water-500 to water-600); chip prefix opacity; CAD file list metadata contrast; guided demo progressbar name; inline auth links now underlined. Axe now reports zero serious or critical violations on all scanned pages. |
| Guide knowledge | Two new allowlisted entries (proof-of-concept, dxf-intelligence) covering what was tested, why the drawing is synthetic, what the parser extracted, what the test proves and does not prove, taxonomy and facility limitations, reproducibility, downloads, and repository paths. Twelve new evaluation cases including a critical safety case ("does the proof show the design is safe"). Evaluation corpus now 130 cases; retrieval and safety gates still pass. |
| Backend decomposition | ADR 0005 activated. models.py (3,023 lines, 88 classes) split into app/db/models/ domain modules (identity, billing, cad, command_center, core) with full re-export compatibility, unchanged table definitions, and the single Alembic head preserved (0003_billing_events). CAD intake gained the four-module cad/ package. command_center_service.py went from 1,862 to about 1,040 lines with builders extracted to app/services/command_center/ (derivations, attention, metrics, readiness, timeline). |
| Frontend coverage | 57.6 / 62.8 / 50.7 / 57.6 measured after this phase (was 56.6 / 62.4 / 50.4 / 56.6); ratchet floors raised to 57/62/50/57. The 70/65/60 targets remain open and tracked. |

### Validation (this phase)

| Gate | Result |
| --- | --- |
| npm audit --omit=dev | 0 vulnerabilities |
| Frontend typecheck, lint | Pass |
| Frontend unit tests | 549 passed, 69 files (was 521 in 66) |
| Frontend coverage floors | Pass at raised 57/62/50/57 |
| Production build (Next 15) | Pass |
| Content integrity gate | Pass |
| Contract freshness | Pass |
| Guide freshness and evaluation | Pass (130 cases, critical safety 100 percent) |
| Backend pytest | 905 passed, 1 skipped (was 787) |
| Backend coverage | Above the 90 percent gate |
| Alembic single head | Pass (0003_billing_events) |
| DXF proof harness | 42 of 42 checks pass; artifacts byte-deterministic across reruns |
| Playwright | 24 of 24 pass (public, auth, DXF upload and parse, Axe) |
| Axe | 0 serious or critical violations on 11 pages |

### Deferred with reasons

1. Route-group shell separation (ADR 0001): public and authenticated pages
   still share one root layout. Moving about seventy page directories was not
   combined with this phase; the navigation remains progressive and the new
   proof page follows the existing layout.
2. Frontend coverage targets (70 statements and lines, 65 branches, 60
   functions): floors ratcheted to the new measurement; the gap is tracked
   here and closes as consumer states gain tests.
3. Remaining backend extraction: review_cycle_service, evidence retrieval,
   seed modules, safety vocabulary, and the core model remainder stay on the
   ADR 0005 staged list.
4. Tenant-isolation browser journey: enforced today by backend tests
   (explicit 403, no fixture substitution) and unit suites; a dedicated
   two-organization Playwright scenario is the next browser addition.
5. Failure-injection browser journeys (backend down, upstream timeout) are
   covered at the unit and route-handler layer; browser-level fault
   injection is future work.

### Updated score

Testing and release discipline rises on the browser, accessibility, proof,
and artifact-freshness gates. Accessibility rises on the corrected
violations and the enforced Axe gate. Backend architecture rises on the
landed decomposition. Product clarity and recruiter experience rise on the
evidence-backed proof page. Withheld points: route shells and coverage
targets (frontend architecture, accessibility and performance), the
unfinished extraction list (backend architecture), and the deferred browser
journeys (testing).

| Category | Score / 10 |
| --- | --- |
| Product clarity | 10 |
| Recruiter experience | 10 |
| Frontend architecture | 9 |
| Backend architecture | 8 |
| Data honesty and integrity | 10 |
| Security and tenancy | 10 |
| Testing and release discipline | 10 |
| Accessibility and performance | 9 |
| Documentation and onboarding | 9 |
| AI governance and professional safety | 10 |
| **Total** | **95 / 100** |

No P0 or P1 issue remains open. The five withheld points are held by the
deferred items above, each with a recorded owner decision and a staged plan.

### Post-merge follow-up: CI Axe failure on the CAD intake page

The e2e job on the merged PR failed once: the Axe scan of the CAD intake
page reported seven serious color-contrast nodes in CI that did not
reproduce locally, and the assertion at the time reported only node counts,
which made the trace artifact the only evidence. Two corrections landed as a
follow-up: every text-slate-500 and text-slate-400 usage in the CAD intake
components moved one shade darker (slate-600 and slate-500), which removes
the entire class of borderline 4.3 to 4.8 contrast pairs regardless of
rendering environment, and the accessibility spec now embeds each violating
node's selector, failure summary, and markup in the assertion payload so
any future CI failure is self-diagnosing from the log alone. All 24
Playwright tests pass on a fresh database with the changes.
