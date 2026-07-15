# Testing

This is the canonical testing reference for Civil Engineer AI. It folds in the
former test-summary document and the guide-freshness portion of the guide
document. It describes the test types, coverage and complexity budgets, and the
local and CI expectations.

## Test types

- Frontend unit and component tests (Vitest, Testing Library): render pages and
  components and assert API client behavior and state handling.
- Content-contract tests (Vitest, file reads): read source and docs as text and
  assert copy rules, so wording regressions fail in CI. These include the
  documentation-assertion tests that pin canonical docs and their content.
- Backend suite (pytest, from `backend/`): covers the API, the review-support
  services, DXF parsing, configuration behavior, and the safety vocabulary
  boundary.
- Guard-regression test: keeps every project-owned API route behind tenant access
  checks (`backend/tests/test_guard_coverage.py`).
- Contract test: regenerates the OpenAPI schema and the generated types and fails
  if the committed artifacts differ.
- DXF proof harness: generates the synthetic DXF, parses it through the real
  routes, compares against versioned ground truth, and verifies the committed
  artifacts byte-for-byte. See `docs/DXF_VALIDATION.md`.
- Browser suite (Playwright plus Axe): public, authentication, DXF
  upload-and-parse, and accessibility journeys. Serious and critical
  accessibility violations fail the build.

## Guide knowledge freshness

The local project guide has its own freshness gate. `scripts/generate-guide-knowledge.mjs`
regenerates `lib/guide/generated/repo-facts.json` from allowlisted sources
(dependency versions, the route list, ADR titles, and key document locations),
and `scripts/check-guide-knowledge.mjs` fails when a repository path referenced by
a knowledge entry no longer exists, when an internal route link no longer
resolves, when the generated facts are stale, or when a retired claim reappears.

## Coverage and complexity budgets

- Backend coverage floor: 90 percent, enforced in CI
  (`pytest --cov-fail-under=90`). Raise the floor as coverage grows; never lower
  it to make a build pass.
- Frontend coverage floors: enforced through `npm run test:coverage`.
- Complexity budget: `scripts/check-complexity.mjs` fails when an authored source
  file crosses the hard size ceiling without an allowlisted cohesion reason.
- Dependency audits: production and full-tree audits run as release gates; any
  accepted finding requires a documented owner and expiry in
  `docs/internal/DEPENDENCY_REMEDIATION.md`.
- Content integrity: `scripts/check-content-integrity.mjs` blocks attribution
  text and em dashes across the tracked tree.

## Running everything locally

```bash
npm run typecheck
npm run lint
npm run check:content
npm run check:guide
npm test
npm run build
cd backend && pytest
```

`npm run check` runs typecheck, lint, content integrity, and the frontend tests;
`npm run verify` also runs the build. CI runs the backend suite with its coverage
floor, the frontend gates, the contract job, the DXF proof harness, and the
browser suite on every push. See `.github/workflows/ci.yml`.
