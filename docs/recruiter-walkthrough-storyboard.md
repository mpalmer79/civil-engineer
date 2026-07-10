# Recruiter Walkthrough Storyboard

This storyboard defines the visual walkthrough shipped at `public/images/civil-engineer/recruiter-walkthrough.gif`. Every frame is a screenshot of the actual app UI rendered from the production build at 1280x720. The GIF loops through nine frames in the order a recruiter should experience the product: context first, then workflow, then the human review boundary.

The written companion is [recruiter-walkthrough.md](recruiter-walkthrough.md).

## Frames

| Frame | Route | Screenshot target | Caption | Purpose | Duration | Crop and focus notes |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | `/` | Top of page: heading, status pill, Brookside hero image | Homepage: the Brookside Meadows demo project | First impression matches the first thing a visitor sees | 3.0s | Viewport top, hero image dominant, no scroll |
| 2 | `/` | Below the hero: description, CTAs, review path, proof chips, KPI cards | Project context, review path, and proof before metrics | Shows the page explains the demo before showing metrics | 2.4s | Crop of a tall capture starting just under the hero image |
| 3 | `/guided-demo` | Page header and the five-step demo overview card | Guided demo: the reviewer journey, no login needed | The primary CTA target and the recommended entry point | 2.4s | Viewport top, keep the numbered step list visible |
| 4 | `/projects` | Page header, create action, and the projects workspace panel | Projects workspace: seeded demo plus real project records | Shows the split between seeded demo and real records | 2.4s | Viewport top |
| 5 | `/documents` | Status summary cards and the top of the document table | Documents: submitted package with intake status tracking | Evidence starts with what was actually submitted | 2.4s | Keep the Present, Partial, Missing counters readable |
| 6 | `/findings` | Findings counters, boundary banner, first finding chips | Findings: review-support issues linked to evidence | The core product idea: findings tied to evidence and risk | 2.4s | Boundary banner should stay in frame |
| 7 | `/response-package` | Page header and the builder description card | Response package: applicant communication draft | Applicant response workflow with reviewer control | 2.4s | Viewport top |
| 8 | `/review-packet` | Page header and the packet builder description card | Review packet: reviewer-controlled handoff | The workflow ends at handoff, not at a decision | 2.4s | Viewport top |
| 9 | `/human-review` | Page header and the How human review works card | Human review: every decision stays with the reviewer | Closes on the human-in-the-loop boundary | 2.4s | Keep the six-step human review list visible |

Total loop: roughly 22 seconds. The reviewer queue route (`/dashboard/queue`) is intentionally not a frame: real queue items require sign-in, so a screenshot from a logged-out build would show an empty state instead of the product.

## How to regenerate the GIF

The repo does not include screenshot tooling as a dependency; the GIF is regenerated with a headless Chromium and any image tool that assembles PNGs into an animated GIF (the original was built with Pillow).

1. Build and run the frontend: `npm run build && npm start`.
2. Screenshot each route above at 1280x720, for example:
   `chromium --headless=new --hide-scrollbars --window-size=1280,720 --virtual-time-budget=8000 --screenshot=frame.png http://localhost:3000/<route>`
3. For frame 2, capture `/` at 1280x1700 and crop the band from y=700 to y=1420.
4. Add a caption bar (46px, slate background, light text) at the bottom of each frame with the captions from the table.
5. Assemble the frames into a looping GIF with the durations from the table, 256-color adaptive palette per frame.
6. Keep the output under about 2 MB and replace `public/images/civil-engineer/recruiter-walkthrough.gif`.
