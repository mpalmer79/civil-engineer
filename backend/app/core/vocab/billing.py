"""Auth lifecycle, team invitation, and billing and usage metering vocabulary."""

from __future__ import annotations

# Production Phase 4B/4C auth lifecycle, team invitation, and billing/usage
# vocabulary. These control account recovery, team membership invitations,
# subscription posture, and internal usage metering. They never introduce a
# final engineering decision, approval, certification, or compliance workflow,
# and they never change the review-support boundary. Billing posture is honest:
# a subscription status is an account-state label, not a review outcome.

# Organization invitation lifecycle states. pending invites can be accepted or
# revoked; accepted and revoked are terminal. expired is derived from the expiry
# timestamp at read time and is not stored as a separate row state.
ALLOWED_INVITATION_STATUSES: set[str] = {
    "pending",
    "accepted",
    "revoked",
}

# Subscription plan codes. demo is the default unpaid posture; design_partner is
# the scoped pilot tier; professional and team are paid tiers. No code implies a
# review outcome; a plan only sets usage limits and billing posture.
ALLOWED_PLAN_CODES: set[str] = {
    "demo",
    "design_partner",
    "professional",
    "team",
}

# Organization subscription states. inactive is the default (no active paid
# subscription); trialing and active describe a configured subscription;
# past_due records a configured subscription with a failed payment; canceled
# records a stopped subscription. These are billing-posture labels only and never
# describe a review outcome.
ALLOWED_SUBSCRIPTION_STATUSES: set[str] = {
    "inactive",
    "trialing",
    "active",
    "past_due",
    "canceled",
}

# Internal usage metering categories. Each records a count of a review-support
# action for advisory usage limits. No category records file content, document
# text, or any secret. AI categories are future-only counters and are not wired
# to live AI, which stays disabled by default.
ALLOWED_USAGE_CATEGORIES: set[str] = {
    "project_created",
    "document_uploaded",
    "pdf_indexed",
    "pages_indexed",
    "cad_parsed",
    "review_packet_generated",
    "pilot_request_submitted",
    "ai_call_attempted",
}
