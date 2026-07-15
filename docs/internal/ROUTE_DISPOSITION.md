# Route Disposition

Internal engineering document. Canonical route map for the Next.js frontend after the consolidation initiative. Companion to docs/ROUTE_ARCHITECTURE.md (the product-facing route reference) and ADR 0001.

## Principles

- One canonical implementation per surface. Legacy public URLs are preserved through permanent redirects in next.config.mjs, not duplicate pages.
- Reference-project surfaces (seeded Brookside Meadows data) are clearly labeled and never required by authenticated tenant workflows.
- No route is removed without a redirect.

## Public product surfaces

| Route | Disposition | Notes |
| --- | --- | --- |
| / | Canonical | Product homepage, composition of components/home sections |
| /proof-of-concept | Canonical | Technical validation page for the deterministic DXF pipeline; copy reframed as technical validation, URL retained because the committed artifacts, CI job, and inbound links target it |
| /poc, /proofofconcept | Redirect (existing) | Permanent redirects to /proof-of-concept |
| /landing | Redirect (changed) | Was a page stub calling redirect("/"); now a permanent redirect in next.config.mjs |
| /start-here | Canonical | Evaluation starting guide, professional framing |
| /guided-demo | Canonical | Guided product tour over the reference project |
| /evaluation | Canonical | AI draft finding evaluation surface (domain scoring language is legitimate here) |
| /pilot | Canonical | Pilot request intake |
| /deployment-status | Canonical | Operational readiness surface |

## Reference-project surfaces (seeded, public)

/project (reference project overview), /project-dashboard (reference command center), /dashboard and /dashboard/queue (reviewer dashboard), /cad-intake, /cad-review, /ai-review, /human-review, /checklist, /documents, /findings, /plan-sheets, /sheet-viewer, /response-package, /review-packet, /review-cycles, /workflow-board, /rule-packs, /audit, plus their dynamic detail routes.

Disposition: retained as canonical reference-project surfaces. /project, /project-dashboard, and /dashboard overlap in concept but render distinct views (project overview, command center, reviewer queue); consolidating them into one surface is future work recorded in ROADMAP.md, not a redirect-safe change today, because each has distinct committed content, tests, and inbound links.

## Authentication

/login, /register, /reset-password, /reset-password/confirm, /invitations/accept: canonical, unchanged.

## Authenticated tenant surfaces

/me, /workspace, /workspace/team, /workspace/usage, /workspace/settings, /workspace/billing, /organizations, /organizations/[organizationId], /organizations/[organizationId]/dashboard, /projects, /projects/new, /projects/[projectId]/** (documents, checklists, findings, evidence-search, evidence-candidates, citations, command-center, response-matrix, response-packages, review-packets, resubmittals, workflow-board, workload, traceability, plan-sheets, plan-consistency, cad, access, audit-events, comment-letter-drafts), /admin/pilot-requests: canonical, unchanged.

/me and /workspace overlap on account identity; /workspace is the richer hub. Consolidation is future work (both are authenticated, low-traffic, and removing either today buys little).

## Changes made in this initiative

1. app/landing/page.tsx deleted; /landing became a permanent redirect in next.config.mjs. Behavior for visitors is identical.
2. No other URL changed. The homepage, start-here, and proof-of-concept pages were decomposed and their copy reframed, with URLs untouched.

## Duplicate-definition guard

next.config.mjs redirects and the app/ router are the only two sources of route truth. The route inventory in docs/ROUTE_ARCHITECTURE.md is regenerated into lib/guide/generated/repo-facts.json and freshness-checked in CI (check:guide), which fails if a route listed there stops resolving.
