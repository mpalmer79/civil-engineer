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

### Security and language checks

17. No page or route shows raw storage paths, storage keys, signed URLs,
    tokens, passwords, object storage credentials, the auth secret, the
    database URL, or any other secret.
18. No page claims final approval, compliance, certification, validation,
    issue resolution, or issue closure. Diagnostics show operational status only.
19. The footer and page source do not include generated-by attribution or
    session links.

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
