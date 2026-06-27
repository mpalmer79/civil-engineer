# Live Site Verification

This checklist confirms the deployed Civil Engineer AI frontend matches the
current `main` branch and presents the review-support platform correctly. Run it
after every frontend redeploy.

Live demo URL: https://civil-engineer.up.railway.app/

Civil Engineer AI supports human plan review. It does not approve plans, certify
compliance, verify CAD, validate design, declare a project safe, make final
engineering decisions, resolve issues, close issues, or replace a licensed
Professional Engineer. These checks confirm discoverability and accurate
messaging, not any engineering outcome.

## When to run this

- After a frontend redeploy on Railway.
- After changing `NEXT_PUBLIC_API_BASE_URL`.
- When the live homepage or navigation looks older than the current `main`
  branch. A Next.js build can appear stale if Railway did not redeploy from the
  latest commit. Trigger a fresh frontend deploy and run this checklist again.

`NEXT_PUBLIC_API_BASE_URL` must be the backend origin only, for example
`https://your-backend-service.up.railway.app`. Do not include `/api/v1` in it;
the frontend appends `/api/v1/...` paths itself.

## Manual live-site checks

1. Homepage loads at https://civil-engineer.up.railway.app/.
2. The backend connection banner shows connected.
3. Navigation includes Projects, Dashboard, Reviewer Queue, Rule Packs,
   Organizations, Guided Demo, and Account/Login.
4. `/projects` loads.
5. `/dashboard` loads (Sprint 9 reviewer dashboard).
6. `/dashboard/queue` loads (Sprint 9 reviewer queue).
7. `/login` loads.
8. `/rule-packs` loads.
9. `/organizations` handles the signed-out state safely.
10. `/guided-demo` still loads.
11. The Brookside Meadows public demo still works.

### Demo experience and discovery checks

D1. `/start-here` loads and shows the "Start the Brookside Meadows demo" hero,
    the recommended demo path step cards, the technical foundation section, and
    the review-support boundary.
D2. The Start Here primary call to action links to `/guided-demo`, and an Open
    Brookside Meadows call to action links to `/projects/proj_brookside_meadows`.
D3. `/guided-demo` shows the recommended demo path step cards and the one
    concern end to end deep dive.
D4. The recommended demo path links open the Brookside Meadows documents,
    evidence search, checklists, findings, response matrix, resubmittals, and
    response packages routes, and the reviewer dashboard.
D5. The footer links to Start Here, Guided Demo, Brookside Meadows, and
    Deployment Status. Guided Demo remains in the primary navigation and the
    Demo modules menu remains available.
D6. On a common mobile width the demo step cards stack, chips wrap, and there is
    no horizontal scrolling. The mobile navigation still auto-collapses after
    selecting a primary link and after selecting a demo-module link.
D7. The Brookside Meadows project page shows a demo note that names it the
    sample project. No final-decision wording appears in the demo pages.

### Sprint 10 deployment diagnostics checks

12. `/deployment-status` loads and shows backend, readiness, and storage
    sections (Sprint 10 deployment status page).
13. Backend health route `<backend-origin>/health` returns a status payload.
14. Backend readiness route `<backend-origin>/api/v1/readiness` returns a safe
    status payload with allowed status labels only.
15. Storage health is visible on the deployment status page after sign-in and
    shows the provider and configuration status only, never credentials,
    bucket names, storage keys, signed URLs, or paths.
16. The optional verification script runs:
    `npm run verify:live -- --frontend <frontend-url> --backend <backend-origin>`.
    Against the live deployment, run it as:
    `npm run verify:live -- --frontend https://civil-engineer.up.railway.app --backend <backend-origin>`,
    or set `LIVE_FRONTEND_URL` and `BACKEND_URL` and run `npm run verify:live`.
    The script checks the homepage, `/start-here`, `/guided-demo`, the Brookside
    Meadows sample project, and `/deployment-status`, plus backend `/health` and
    `/api/v1/readiness`. It requires no secrets and prints none. Run it from a
    network that can reach the public deployment; a restricted CI or sandbox
    egress may block outbound requests and report routes as unavailable even
    when the live site is healthy.

### Security and language checks

17. No page or route shows raw storage paths, storage keys, signed URLs,
    tokens, passwords, object storage credentials, the auth secret, the
    database URL, or any other secret.
18. No page claims final approval, compliance, certification, validation,
    issue resolution, or issue closure. Diagnostics show operational status only.
19. The footer and page source do not include generated-by attribution or
    session links.

### Professional design and mobile checks

20. First-impression and workflow pages share a consistent page header,
    surface cards, status chips, and empty states. Pages covered include
    `/me`, `/deployment-status`, `/rule-packs/<id>`, `/organizations/<id>`,
    `/organizations/<id>/dashboard`, the project documents, response matrix,
    resubmittal round, response package, access, and audit-events pages.
21. On a common mobile width the documents list, organization reviewer
    workload, response matrix items, audit events, and access list render as
    stacked responsive cards or lists, not wide tables, and there is no
    horizontal scrolling.
22. Status, role, source, access level, and diagnostic labels render as status
    chips that wrap cleanly. Status is never conveyed by color alone.
23. The mobile navigation still auto-collapses after selecting a primary or
    demo-module link.

## Notes

- The primary navigation leads with the current product workflow (Projects,
  Dashboard, Reviewer Queue, Rule Packs, Organizations, Guided Demo) and groups
  the older Brookside Meadows demo modules under a Demo modules menu. Those demo
  routes are not removed; they remain reachable from the menu and from the
  Guided Demo. Deployment Status is reachable from the footer and the Demo
  modules menu.
- The homepage Production foundation workflow and What is live now sections
  summarize delivered Sprint 1 through 9 review-support capabilities. They are
  operational and workflow indicators only.
- Sprint 10 deployment diagnostics are operational readiness indicators only.
  Detailed environment diagnostics require an organization admin; readiness is
  public but sanitized. Neither approves a project, certifies compliance, or
  makes any engineering determination.
