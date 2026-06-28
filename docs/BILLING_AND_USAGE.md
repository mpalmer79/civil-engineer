# Billing and Usage

The billing-readiness and usage-metering foundation added in Production Phase
4B/4C. Billing is deferred in this phase: the plan model, usage tracking, and UI
exist, but live Stripe checkout and webhooks are not wired and no payment is
collected. This document states exactly what is implemented and what is deferred.

A plan or subscription status is an account-posture label only. It never implies
a review outcome, approval, certification, or compliance. A human reviewer
remains responsible for every finding.

## Stripe status: configured by environment

Stripe checkout and webhooks are implemented (Production Phase 4D) and become
active when configured. Until then the billing UI and API report an honest
inactive state, and no real payment is processed. Full detail is in
`docs/STRIPE_BILLING.md`.

- `billing_enabled` is true only when `STRIPE_SECRET_KEY` is set
  (`backend/app/core/config.py`). It is false by default.
- Checkout (`POST /api/v1/organizations/{organization_id}/billing/checkout`)
  requires an organization admin, creates a Stripe Checkout session for the
  professional plan when fully configured, and otherwise returns an honest
  `available: false` response with no checkout URL.
- The webhook endpoint (`POST /api/v1/billing/webhook`) verifies the Stripe
  signature and processes subscription events idempotently, mapping Stripe
  customer/subscription state onto `organization_subscriptions`.
- The Stripe mapping columns on `organization_subscriptions`
  (`stripe_customer_id`, `stripe_subscription_id`) hold the customer and
  subscription ids; they never hold a secret key.

The environment variables `STRIPE_SECRET_KEY`, `STRIPE_WEBHOOK_SECRET`,
`STRIPE_PRICE_PROFESSIONAL`, `STRIPE_SUCCESS_URL`, `STRIPE_CANCEL_URL`, and
`STRIPE_TEST_MODE` are read backend-only. None are required for local development
or tests, and no secret is exposed to the frontend.

## Plans

Plans are defined in code (`backend/app/services/billing_service.py`) and exposed
publicly at `GET /api/v1/billing/plans`. Tiers:

- `demo`: public Brookside Meadows demo and evaluation.
- `design_partner`: scoped design-partner pilot for a single firm.
- `professional`: for a civil/AEC firm running pre-submittal QA.
- `team`: for a larger team or municipal review group.

Each plan carries advisory usage limits. Prices are descriptive only while
billing is inactive (for example "Contact us"); no charge is asserted.

## Subscriptions

Each organization has at most one subscription
(`organization_subscriptions`), created on demand with the default `demo` plan
and `inactive` status. Statuses: `inactive`, `trialing`, `active`, `canceled`.
The default posture is `demo` / `inactive`: billing is not active and no payment
is collected.

`GET /api/v1/organizations/{organization_id}/billing` (organization member)
returns the subscription, the billing status, and the plan catalog. The Stripe
customer id is never exposed.

## Usage tracking

Usage is metered internally as an append-only ledger (`usage_events`) per
organization. No usage record carries file content, document text, or any
secret, and usage is never sent to any external service.

Tracked categories (`backend/app/core/safety.py`,
`ALLOWED_USAGE_CATEGORIES`):

- `project_created`
- `document_uploaded`
- `pdf_indexed`
- `pages_indexed`
- `cad_parsed`
- `review_packet_generated`
- `pilot_request_submitted`
- `ai_call_attempted` (future category; live AI stays disabled by default)

Wired hooks in this phase (best-effort, never blocking the action):

- `project_created`: when a signed-in user creates a real project.
- `document_uploaded`: when a document is registered on a real project.
- `pilot_request_submitted`: when a public pilot request is submitted (recorded
  as a global event with no tenant).

The seeded demo organization (`org_internal_demo`) is excluded from metering, so
seeded demo activity never counts against any plan or pollutes a usage summary.
The remaining categories are available in the ledger and are wired incrementally;
`record_usage` accepts any allowed category.

## Limits: advisory by default, enforceable for selected categories

Usage limits are advisory by default. Usage is tracked and surfaced with warning
states, but actions are not hard-blocked, so local development, tests, existing
flows, and the public Brookside Meadows demo are never interrupted.

Enforcement (Production Phase 4D) is controlled by `USAGE_ENFORCEMENT_ENABLED`
(default false). When enabled, the following categories are hard-enforced for
real organizations:

- `project_created`
- `document_uploaded`
- `review_packet_generated`

These are single-mutation, organization-scoped, user-driven actions where a clean
pre-check leaves no partial state. When an enforced action is at or over its plan
limit, the API returns `402` with a `limit_exceeded` detail (category, limit,
used, plan) before any mutation, so the action is fully blocked and nothing is
written.

The following stay advisory and are never blocked:

- `ai_call_attempted` (no live AI), `pages_indexed` and `cad_parsed` (counted
  inside internal and seed flows), `pilot_request_submitted` (public lead), and
  any demo usage.

Never enforced regardless of the flag:

- The public Brookside demo and the seeded demo organization
  (`org_internal_demo`). The demo is excluded so it can never be blocked by a
  paid limit. The public pilot request remains public.

`GET /api/v1/organizations/{organization_id}/usage` (organization member) returns
a usage summary. Each metered limit reports `used`, `limit`, a status (`ok`
below 80 percent, `approaching` at or above 80 percent, `over` at or above the
limit), and an `enforced` flag. A limit of `null` means the category is not
metered for that plan. The top-level `enforcement` is `enforced` when enforcement
is enabled, else `advisory`.

## Frontend surfaces

- `/workspace/billing`: current plan, billing status and mode (inactive, test, or
  live), the plan catalog, and a checkout CTA shown only when checkout is
  available; otherwise an honest "Billing is not active in this environment"
  disabled state. It states that billing is required only for production SaaS,
  not the public demo.
- `/workspace/usage`: usage counters against plan limits with warning states, an
  `enforced` badge on enforced limits, and a note reflecting whether limits are
  advisory or enforced.
- `/workspace/settings`: links to the billing and usage pages.

No surface claims an active subscription unless the backend reports one, and no
"Subscribe" button errors: the CTA appears only when checkout is available.

## Migrations

The `organization_subscriptions` and `usage_events` tables are created by the
Alembic migration `0002_auth_billing_usage`. The `billing_events` webhook
idempotency table is created by `0003_billing_events`. Apply them with
`alembic upgrade head`. See `docs/PRODUCTION_DATABASE.md`.

## Tests

Backend: `backend/tests/test_billing_usage.py` covers the plan catalog, billing
status, membership-gated organization billing and usage, usage category
validation, the demo-org exclusion, usage totals and limit status, and that no
secret is exposed. `backend/tests/test_stripe_billing.py` covers checkout and
webhooks (see `docs/STRIPE_BILLING.md`), and
`backend/tests/test_usage_enforcement.py` covers advisory and enforced behavior.
Frontend: `app/__tests__/accountBillingTeam.test.tsx` covers the billing and
usage clients, including the unavailable state and the checkout CTA.

## Remaining work before paid production billing

- Configure live Stripe keys and verify an end-to-end checkout in test mode.
- Add invoice and payment-failure handling (dunning) if needed, and a customer
  portal link for self-serve plan changes.
- Consider enforcing additional categories once their flows have dedicated
  user-entry guards.
