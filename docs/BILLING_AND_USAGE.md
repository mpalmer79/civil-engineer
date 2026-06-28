# Billing and Usage

The billing-readiness and usage-metering foundation added in Production Phase
4B/4C. Billing is deferred in this phase: the plan model, usage tracking, and UI
exist, but live Stripe checkout and webhooks are not wired and no payment is
collected. This document states exactly what is implemented and what is deferred.

A plan or subscription status is an account-posture label only. It never implies
a review outcome, approval, certification, or compliance. A human reviewer
remains responsible for every finding.

## Stripe status: deferred

Stripe is not active. The billing UI and API report an honest inactive state
until a Stripe secret key is configured. No real payment is processed in this
phase.

- `billing_enabled` is true only when `STRIPE_SECRET_KEY` is set
  (`backend/app/core/config.py`). It is false by default.
- The checkout endpoint
  (`POST /api/v1/organizations/{organization_id}/billing/checkout`) returns an
  honest `available: false` response with no checkout URL, so the UI shows a
  disabled state rather than a button that would error. Even when a Stripe key is
  set, hosted checkout creation is intentionally deferred to a future phase.
- Reserved, nullable Stripe mapping columns exist on
  `organization_subscriptions` (`stripe_customer_id`, `stripe_subscription_id`)
  for a future integration. They are unused and never hold a secret.

The environment variables `STRIPE_SECRET_KEY`, `STRIPE_WEBHOOK_SECRET`,
`STRIPE_PRICE_PROFESSIONAL`, and `STRIPE_TEST_MODE` are documented and read
backend-only. They are never required for local development or tests, and no
secret is exposed to the frontend.

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

## Limits: advisory, not enforced

Usage limits are advisory in this phase. Usage is tracked and surfaced with
warning states, but actions are not hard-blocked, so existing behavior and the
public Brookside Meadows demo are never interrupted.

`GET /api/v1/organizations/{organization_id}/usage` (organization member) returns
a usage summary. Each metered limit reports `used`, `limit`, and a status:

- `ok`: below 80 percent of the limit.
- `approaching`: at or above 80 percent.
- `over`: at or above the limit.

A limit of `null` means the category is not metered for that plan (advisory
unlimited). The summary always reports `enforcement: "advisory"`.

## Frontend surfaces

- `/workspace/billing`: current plan, honest inactive billing status, the plan
  catalog, and a disabled checkout action.
- `/workspace/usage`: advisory usage counters against plan limits with warning
  states, and a note that limits do not block actions.
- `/workspace/settings`: links to the billing and usage pages.

No surface claims an active subscription unless the backend reports one, and no
"Subscribe" button errors: checkout is disabled while billing is inactive.

## Migrations

The `organization_subscriptions` and `usage_events` tables are created by the
Alembic migration `0002_auth_billing_usage`. Apply it with `alembic upgrade
head`. See `docs/PRODUCTION_DATABASE.md`.

## Tests

Backend: `backend/tests/test_billing_usage.py` covers the plan catalog, the
inactive billing status, membership-gated organization billing and usage, the
deferred-checkout response, usage category validation, the demo-org exclusion,
usage totals and limit status, and that no secret is exposed. Frontend:
`app/__tests__/accountBillingTeam.test.tsx` covers the billing and usage clients,
including the inactive state and the advisory note.

## Remaining work before paid production billing

- Wire live Stripe checkout-session creation for a single plan.
- Add a Stripe webhook endpoint with signature validation and idempotency, and
  map subscription lifecycle events onto `organization_subscriptions`.
- Decide which limits become enforced (hard) versus advisory, and add enforcement
  without affecting the public demo.
- Add a billing customer/event mapping if needed for reconciliation.
