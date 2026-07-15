# Pilot Operations

How to run the design-partner pilot once requests start arriving. This is an
internal operator guide. It pairs with `docs/RELEASE_READINESS.md`,
`docs/PILOT_RELEASE_CHECKLIST.md`, and `docs/DESIGN_PARTNER_OUTREACH.md`.

## Operator model

The pilot operator is an organization admin (`org_admin`). The pilot admin APIs
and the `/admin/pilot-requests` page are gated by `require_admin_user`, which
requires a signed-in org_admin: an anonymous caller gets 401 and a signed-in
non-admin gets 403. A dedicated `pilot_operator` role was considered in
Production Phase 4B and deliberately not added, because organization admin is
sufficient for the current pilot and a separate role would add membership-model
churn without a clear benefit. If a finer-grained operator separation is needed
later, add a `pilot_operator` role behind the same gate. The public pilot request
form stays public.

## Where requests live

Submitted pilot requests are stored locally (no email, no external service).
Review them at `/admin/pilot-requests`, which uses the admin-gated pilot APIs.
Anonymous and non-admin users cannot see any data; sign in as an organization
admin. There is no public list endpoint and no file-upload control.

## How to review pilot requests

1. Open `/admin/pilot-requests`.
2. Filter by status, interest level, or sample-package, or search by firm, name,
   or email.
3. Open a request and read the firm, role, project type, primary pain, interest
   level, and the submitter's notes.
4. Set a status and, when you reach out, mark it contacted. Record operator-only
   internal notes. Internal notes are never shown publicly or returned by the
   public submission endpoint.
5. Export a CSV of all requests for offline triage if needed (operator only).

## Statuses and what they mean

- `new` - submitted, not yet triaged.
- `contacted` - outreach sent; awaiting a reply.
- `qualified` - a real design-partner fit after a first conversation.
- `active_pilot` - running a scoped pilot with this firm.
- `closed` - conversation finished (won, paused, or simply done).
- `rejected` - not a fit for the pilot.

## How to qualify a design-partner conversation

Aim to confirm the firm feels the pain the product addresses and can give real
usage and feedback. Good fits are small to mid-sized civil/AEC firms preparing
stormwater, site, or civil packages for municipal submittal.

Suggested qualification questions:

- How many resubmittal cycles does a typical package go through, and what does a
  cycle cost you in schedule?
- Who runs pre-submittal QA today, and how long does it take?
- Which review comments tend to come back most often?
- Do you have a recent DXF plan set and stormwater report you could run through a
  scoped pilot later?
- What would make this worth your team's time during a pilot?

## What to say about current capabilities

Describe only what is implemented, using the canonical wording in
`docs/SAAS_POSITIONING.md`:

- Real DXF parsing with the ezdxf library: it extracts layers, entities, blocks,
  text, and reference candidates. This is metadata extraction, not geometry
  validation or compliance certification.
- Real PDF text-layer indexing with pypdf, where extractable text exists.
- Evidence traceability that ties each finding back to a specific page or sheet.
- Plan and report consistency checks, a workflow board, and a draft reviewer
  handoff package.

What not to claim: do not say the product approves plans, certifies compliance,
verifies CAD, validates design, guarantees compliance, makes a project safe,
passes review, meets all requirements, or guarantees first-pass acceptance. A
human reviewer remains responsible for every item.

## What is not included

- No OCR, so scanned-image PDF pages without a text layer are not read.
- No DWG parsing (uploads are limited to `.dxf`) and no GIS or georeferencing.
- No computer vision and no vector or semantic search.
- Live AI is disabled by default; the default provider is a deterministic mock.

## How to explain the demo data

The public Brookside Meadows demo is seeded review-support data for a synthetic
subdivision, plus CAD findings produced by really parsing a bundled sample DXF.
It is not a real submission. Use it to show the workflow, not to claim a real
outcome.

## When to request real files

- Request a real DXF or PDF only after a firm is `qualified` and has agreed to a
  scoped pilot, and only with their explicit consent.
- Confirm the firm understands this is a pilot-ready prototype, not production
  SaaS, before they share anything sensitive.

## When not to request real files

- Not during first outreach or before qualification.
- Not for any project the firm is not authorized to share.
- Never ask for credentials, secrets, or anything beyond the plan set and report
  needed for the scoped pilot.

## Follow-up workflow

1. New request arrives -> status `new`.
2. Send outreach (see `docs/DESIGN_PARTNER_OUTREACH.md`) -> mark `contacted`.
3. Hold a qualifying call -> `qualified` or `rejected`.
4. Scope and run a pilot -> `active_pilot`, recording notes as you go.
5. Wrap up -> `closed`.

Keep internal notes factual and free of any approval, certification, or
compliance language.
