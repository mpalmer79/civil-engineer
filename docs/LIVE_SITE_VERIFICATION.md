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
3. Navigation includes Projects, Rule Packs, Organizations, and Account/Login.
4. `/projects` loads.
5. `/login` loads.
6. `/rule-packs` loads.
7. `/organizations` handles the signed-out state safely.
8. `/guided-demo` still loads.
9. The Brookside Meadows public demo still works.
10. No page shows raw storage paths, tokens, secrets, or backend credentials.
11. The homepage does not claim final approval, compliance, certification,
    validation, issue resolution, or issue closure.
12. The footer and page source do not include generated-by attribution or
    session links.

## Notes

- The primary navigation leads with the current product workflow (Projects,
  Rule Packs, Organizations, Guided Demo) and groups the older Brookside Meadows
  demo modules under a Demo modules menu. Those demo routes are not removed; they
  remain reachable from the menu and from the Guided Demo.
- The homepage Production foundation workflow and What is live now sections
  summarize delivered Sprint 1 through 8 review-support capabilities. They are
  operational and workflow indicators only.
- Reviewer dashboard and reviewer queue routes are not part of this build yet, so
  they should not appear in the navigation or homepage.
