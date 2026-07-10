# Route architecture

Every frontend route, classified by audience and status. The classification
policy is recorded in `docs/adr/0001-canonical-routes-and-shells.md`.

Categories:

- **Public**: marketing and recruiter entry, no session required.
- **Demo**: public Brookside Meadows demo wrapper rendering seeded data with a
  visible `DataSourceNotice`.
- **Auth**: authenticated workspace surface; failures render explicit
  sign-in or permission states, never seeded substitutions.
- **Project**: authenticated, project-scoped operational surface (public for
  the `demo_public` Brookside project, access-controlled otherwise).
- **Admin**: organization or platform administration.
- **Internal**: technical evaluation surface, reachable from the Technical
  Overview page rather than primary navigation.
- **Redirect**: legacy compatibility route that forwards elsewhere.

## Public and session routes

| Route | Category | Notes |
| --- | --- | --- |
| `/` | Public | Recruiter-first product entry; no operational widgets |
| `/guided-demo` | Public | Curated Brookside reviewer journey (primary CTA) |
| `/start-here` | Public | Technical overview, evaluator paths, demo module index |
| `/pilot` | Public | Pilot interest page |
| `/landing` | Redirect | Redirects to `/`; content consolidated into the homepage |
| `/login`, `/register` | Public | Session establishment via `/api/session` endpoints |
| `/reset-password`, `/reset-password/confirm` | Public | Password reset flow |
| `/invitations/accept` | Public | Invitation acceptance |

## Authenticated workspace routes

| Route | Category |
| --- | --- |
| `/dashboard`, `/dashboard/queue` | Auth |
| `/projects`, `/projects/new` | Auth |
| `/workspace`, `/workspace/billing`, `/workspace/team`, `/workspace/usage`, `/workspace/settings` | Auth |
| `/organizations`, `/organizations/[id]`, `/organizations/[id]/dashboard` | Auth |
| `/me` | Auth |
| `/rule-packs`, `/rule-packs/[rulePackId]` | Auth |
| `/admin/pilot-requests` | Admin |

## Project-scoped operational routes

All under `/projects/[projectId]`: overview, `access`, `audit-events`, `cad`,
`checklists` (and item detail), `command-center`, `comment-letter-drafts`
(and preview), `documents` (register, detail, pages), `evidence-candidates`,
`evidence-citations`, `evidence-search`, `findings` (new, detail),
`plan-consistency`, `plan-sheets` (and sheet detail), `response-matrix` (and
items), `response-packages` (detail, preview), `resubmittals` (and round),
`review-packets`, `traceability`, `workflow-board`, `workload`.

Category: Project. These are the canonical operational surfaces. The Brookside
project is publicly readable by design (`demo_public`); all other projects
enforce per-project access.

## Legacy demo module routes

These predate project scoping. Each is a thin public demo wrapper over the
same backend seed (no duplicate business logic) and renders a
`DataSourceNotice`. They are indexed on `/start-here`, not in the primary
navigation.

| Route | Category | Canonical equivalent |
| --- | --- | --- |
| `/project` | Demo | `/projects/proj_brookside_meadows` |
| `/project-dashboard` | Demo | `/projects/proj_brookside_meadows/command-center` |
| `/documents` | Demo | `.../documents` |
| `/checklist` | Demo | `.../checklists` |
| `/findings` | Demo | `.../findings` |
| `/plan-sheets`, `/sheet-viewer`, `/sheet-viewer/[sheetId]` | Demo | `.../plan-sheets` |
| `/cad-intake`, `/cad-intake/[cadFileId]`, `/cad-review` | Demo | `.../cad` |
| `/review-packet`, `/review-packet/[packetId]` | Demo | `.../review-packets` |
| `/workflow-board`, `/workflow-board/[workflowItemId]` | Demo | `.../workflow-board` |
| `/response-package`, `/response-package/[responsePackageId]` | Demo | `.../response-packages` |
| `/review-cycles`, `/review-cycles/[reviewCycleId]` | Demo | `.../resubmittals` |
| `/resubmittals/[resubmittalPackageId]` | Demo | `.../resubmittals` |
| `/revision-comparisons/[comparisonRunId]` | Demo | `.../resubmittals` |
| `/audit` | Demo | `.../audit-events` |
| `/human-review` | Internal | Human review queue demo |
| `/ai-review` | Internal | AI draft-finding demo (mock provider) |
| `/evaluation` | Internal | Brookside evaluation case results |
| `/deployment-status` | Internal | Diagnostics-derived status (not static) |

## API routes (Next.js server)

| Route | Purpose |
| --- | --- |
| `/api/session/login`, `/api/session/register`, `/api/session/logout` | HttpOnly cookie session management (ADR 0003) |
| `/api/backend/[...path]` | Backend-for-frontend proxy; CSRF gate plus server-side token attachment |
