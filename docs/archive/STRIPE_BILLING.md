# Stripe Billing

How Civil Engineer AI handles Stripe checkout and webhooks, added in Production
Phase 4D. It builds on the billing-readiness foundation from Phase 4B/4C and
pairs with `docs/BILLING_AND_USAGE.md`.

A subscription status is an account-posture label only. It never implies a review
outcome, approval, certification, or compliance. Billing is required only for
production SaaS use; the public Brookside Meadows demo never requires billing.

## Status: configured by environment

Stripe is inactive until configured. No real payment is processed unless the
Stripe settings are set. The UI and API report honest states:

- `billing_enabled` is true only when `STRIPE_SECRET_KEY` is set.
- Checkout is available only when checkout is fully configured
  (`Settings.stripe_checkout_configured`): secret key, professional price id, and
  both redirect URLs.
- Webhooks are verified only when `STRIPE_WEBHOOK_SECRET` is set.
- `billing_mode` is `inactive`, `test`, or `live` (test unless live keys are
  configured), and never leaks a secret.

## Configuration

Backend service variables (set on the backend only; never exposed to the
frontend):

- `STRIPE_SECRET_KEY` - the Stripe secret key. Use a test-mode key (`sk_test_...`)
  unless you intend to process live payments.
- `STRIPE_WEBHOOK_SECRET` - the webhook signing secret (`whsec_...`).
- `STRIPE_PRICE_PROFESSIONAL` - the price id for the professional plan.
- `STRIPE_SUCCESS_URL`, `STRIPE_CANCEL_URL` - the redirect URLs after checkout.
- `STRIPE_TEST_MODE` - descriptive flag; keep true unless live keys are
  configured.

None of these are required for local development or tests. The Stripe SDK is
isolated to `backend/app/services/stripe_service.py` and is only called when
checkout is configured.

## Checkout

`POST /api/v1/organizations/{organization_id}/billing/checkout`:

- Requires an authenticated organization admin (org_admin). An anonymous caller
  gets 401 and a non-admin gets 403.
- When checkout is not configured, returns an honest unavailable response
  (`available: false`, no URL), so the UI shows a disabled state rather than a
  button that would error. No payment is processed.
- When configured, ensures the organization has a Stripe customer mapping
  (reusing an existing `stripe_customer_id`), creates a Checkout session for the
  professional price, and returns the session URL. The Stripe secret is never
  returned.

The checkout session sets `client_reference_id` and subscription metadata to the
organization id so the webhook can map the resulting subscription back to the
organization.

Only the professional plan has checkout in this phase. The other plans remain
catalog entries.

## Webhooks

`POST /api/v1/billing/webhook`:

- Verifies the `Stripe-Signature` header against `STRIPE_WEBHOOK_SECRET` using
  the documented Stripe HMAC-SHA256 scheme. The verification is implemented with
  the standard library so it is deterministic and testable without the SDK or a
  network call. A missing, malformed, expired, or mismatched signature is
  rejected with 400.
- Processes these events:
  - `checkout.session.completed`
  - `customer.subscription.created`
  - `customer.subscription.updated`
  - `customer.subscription.deleted`
- Any other event type is acknowledged and ignored.

### Idempotency

Each processed Stripe event id is recorded in the `billing_events` table. A
duplicate delivery (same event id) is ignored and reported as `duplicate`. No
Stripe secret, signature, or raw payload is stored.

### Subscription mapping

The organization is resolved from the event without trusting a single source:
`client_reference_id`, then subscription metadata, then a match on the stored
`stripe_customer_id`. The organization subscription is updated with the Stripe
customer and subscription ids and a mapped status:

- Stripe `active` -> `active`
- Stripe `trialing` -> `trialing`
- Stripe `past_due` / `unpaid` -> `past_due`
- Stripe `canceled` / `incomplete_expired` -> `canceled`
- Stripe `incomplete` -> `inactive`
- `customer.subscription.deleted` -> `canceled`

On `checkout.session.completed`, the organization is set to the professional plan
with status `active`.

## Testing webhooks locally

- Use the Stripe CLI to forward events to the local webhook endpoint and to
  trigger test events, with `STRIPE_WEBHOOK_SECRET` set to the CLI's signing
  secret.
- The automated suite verifies signatures with a locally computed HMAC, so the
  security path is covered without the SDK or any network call.

## Security

- No Stripe secret, webhook secret, or signature is logged or returned.
- The webhook requires a valid signature; an invalid signature is rejected.
- Webhook processing never trusts client-side state; it maps state from the
  verified Stripe object only.
- Checkout requires an organization admin.

## Tests

`backend/tests/test_stripe_billing.py` covers signature verification (valid,
invalid, expired, malformed, missing secret), idempotent event handling
(duplicate ignored, unknown ignored, deletion maps to canceled), the org-admin
checkout gate, the unavailable response when Stripe is not configured, a mocked
checkout success path (no real network call), and the webhook endpoint
(invalid-signature rejection, processing, and duplicate handling).

## Remaining work before live billing

- Decide on invoice and payment-failure handling
  (`invoice.payment_failed`/`succeeded`) if dunning is needed.
- Add a customer portal link for self-serve plan changes and cancellation.
- Configure live keys and verify a real end-to-end checkout in test mode first.
