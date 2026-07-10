# ADR 0001: Canonical routes and progressive navigation

Status: Accepted

## Context

The route surface grew across many phases: newer project-scoped routes
(`/projects/[projectId]/...`) coexist with older unscoped Brookside demo
routes (`/documents`, `/checklist`, `/findings`, `/cad-intake`, and others).
The global navigation exposed every module at once, and the homepage rendered
its own operational sidebar, creating two competing navigation systems and a
cognitively expensive first impression.

## Decision

1. The homepage is the recruiter-facing product entry. It renders no
   operational widgets and no sidebar. Live operational data stays behind
   sign-in on `/dashboard`.
2. Public navigation exposes only public destinations: Product (`/`), Guided
   Demo (`/guided-demo`), Technical Overview (`/start-here`), and Pilot
   (`/pilot`), plus the Sign in control.
3. Reviewer workspace destinations (`/projects`, `/dashboard`,
   `/dashboard/queue`, `/workspace`, `/organizations`, `/rule-packs`) appear
   in the navigation only after sign-in, detected through the non-sensitive
   session indicator cookie.
4. The older unscoped demo module routes remain available as public demo
   wrappers. They are indexed on the Technical Overview page instead of the
   primary navigation, and each renders a `DataSourceNotice` disclosing its
   data source. They contain no duplicate business logic: they read the same
   backend seed the project-scoped routes use, with the repository fixture as
   a labeled snapshot fallback.
5. `/landing` redirects to `/`; its content was consolidated into the
   homepage. `/start-here` remains as the technical overview destination
   because it carries the evaluator path, technical foundation summary, and
   demo module index.

## Consequences

- One navigation system per audience: public visitors see four destinations;
  signed-in reviewers additionally see the workspace group.
- Bookmarked legacy links keep working, and every demo surface states what it
  is.
- Full route-group layout separation (distinct marketing, demo, and
  application shells as Next.js route groups) remains available as a follow-up
  if the shells diverge further; the current single-layout approach with
  conditional navigation was chosen to avoid moving seventy page directories
  while achieving the same user-facing outcome.

The complete route classification lives in `docs/ROUTE_ARCHITECTURE.md`.
