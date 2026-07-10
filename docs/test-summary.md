# Test Summary

What is tested in this repository, what the tests protect, and how to run them. The suites are expected to complete with no failing tests through the existing project scripts.

## Test types

- **Frontend unit and component tests** (vitest, Testing Library): render pages and components, check API client behavior, and assert the seeded fallback works.
- **Content-contract tests** (vitest, file reads): read source files and docs as text and assert copy rules, so wording regressions fail in CI instead of shipping.
- **Backend suite** (pytest, from `backend/`): covers the API, the review-support services, DXF parsing, configuration behavior, and the safety vocabulary boundary, with a coverage floor enforced in CI.
- **Guard-regression test**: keeps every project-owned API route behind tenant access checks.

## What the homepage tests cover

`app/__tests__/homepage.test.tsx` renders the homepage and asserts:

- The Reviewer Command Center heading and positioning line are present.
- The Brookside Meadows hero image renders with descriptive alt text, and the referenced image file actually exists in `public/`.
- The synthetic 47-lot project description appears near the hero.
- No text is overlaid inside the hero image card.
- The proof chips render.
- Each call to action points at a route directory that exists, so a CTA cannot 404.
- The KPI cards and all five dashboard widgets are present.
- The hero image is not repeated elsewhere on the page.
- The human review boundary line is present.
- There is no nested main landmark (the root layout provides the only one).
- Source hygiene: no prohibited final-decision wording, no tool attribution, no em dashes.

## What the copy safety tests cover

- `lib/api/__tests__/publicCopy.test.ts`: capability wording matches actual DXF and CAD intake support across public pages.
- `lib/api/__tests__/deployment.test.ts`: no phase chronology on public surfaces, correct deployment target wording, API base URL examples stay well formed.
- `app/__tests__/releaseReadiness.test.ts` and related docs tests: release docs exist, contain no attribution tokens, and make no prohibited final-decision promises.
- `app/__tests__/recruiterDocs.test.ts`: the recruiter docs in this folder exist, README links resolve to real files, the visual walkthrough is only referenced when the file exists, and the new docs carry no em dashes or attribution tokens.
- Backend safety vocabulary tests: statuses and actions stay within review-support language.

## How to run everything

```bash
npm run typecheck
npm run lint
npm test
npm run build
cd backend && pytest
```

CI runs the backend suite with its coverage floor and the frontend typecheck, lint, and test steps on every push. See `.github/workflows/ci.yml`.

## Why this supports recruiter trust

The claims in the README are not just prose. The hero image path, the CTA routes, the boundary line, the absence of decision language, and the docs links in this folder are all asserted by tests that run in CI. If a claim drifts from the code, the build goes red before the claim reaches a reviewer.
