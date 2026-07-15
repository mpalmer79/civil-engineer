"""Core finding and checklist review status and action vocabulary."""

from __future__ import annotations

# Status values the system is allowed to assign to checklist items, findings,
# and human review outcomes. None of these imply a final engineering decision.
ALLOWED_REVIEW_STATUSES: set[str] = {
    "not_started",
    "supported",
    "missing",
    "conflicting",
    "unclear",
    "unresolved",
    "not_applicable",
    "requires_human_review",
    "validation_failed",
    "accepted_by_reviewer",
    "edited_by_reviewer",
    "rejected_by_reviewer",
    "escalated",
    "marked_unclear",
    "requested_more_information",
}

# Human review states that satisfy the requirement that every finding stays
# under human control. A finding is never final without one of these.
HUMAN_REVIEW_STATUSES: set[str] = {
    "requires_human_review",
    "accepted_by_reviewer",
    "edited_by_reviewer",
    "rejected_by_reviewer",
    "escalated",
    "marked_unclear",
    "requested_more_information",
}

# Human review actions a reviewer may take on an AI draft finding. None of these
# is a final engineering decision, and none uses approval or certification
# language. There is intentionally no action called "approve".
ALLOWED_REVIEW_ACTIONS: set[str] = {
    "accepted",
    "edited",
    "rejected",
    "escalated",
    "marked_unclear",
    "requested_more_information",
}

# The resulting draft finding status for each allowed review action. These map
# review-support actions to review-support statuses and never to a final
# decision.
REVIEW_ACTION_TO_STATUS: dict[str, str] = {
    "accepted": "accepted_by_reviewer",
    "edited": "edited_by_reviewer",
    "rejected": "rejected_by_reviewer",
    "escalated": "escalated",
    "marked_unclear": "marked_unclear",
    "requested_more_information": "requested_more_information",
}

# Actions that establish or affirm a usable review-support finding. A failed
# draft finding may not be accepted or edited; it can only be rejected,
# escalated, or marked unclear pending regeneration.
ACTIONS_REQUIRING_VALID_DRAFT: set[str] = {"accepted", "edited"}


# Phase 4B traceability row review actions. A reviewer records how they reviewed
# one traceability link. reviewer_confirmed_link means the reviewer confirmed the
# relationship is useful for review; it never means the requirement is satisfied,
# approved, certified, verified, validated, or compliant. link_rejected discards
# the link relationship for review without deleting any source record. There is
# intentionally no action called approve.
ALLOWED_TRACEABILITY_REVIEW_ACTIONS: set[str] = {
    "needs_review",
    "reviewer_confirmed_link",
    "needs_more_information",
    "not_applicable",
    "link_rejected",
    "follow_up_needed",
}
