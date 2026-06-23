"""Central safety and status vocabulary for Civil Engineer AI.

Civil Engineer AI is a review-support and evidence-organization system. It must
never present itself as a licensed engineering tool. This module is the single
source of truth for the status values the system may use and for the
final-decision language it must never apply to a status or finding conclusion.

Explanatory prose elsewhere may state that the system does not approve plans.
That is different from applying a prohibited word as a status or conclusion,
which this module exists to prevent.
"""

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

# Final-decision language the system must never use as a status or conclusion.
# Matching is done case insensitively against normalized text.
PROHIBITED_FINAL_DECISION_WORDS: set[str] = {
    "approved",
    "certified",
    "fully compliant",
    "safe",
    "engineer-confirmed",
    "passes review",
    "meets all requirements",
}

# Phase 6 plan sheet status values. None of these implies a final engineering
# decision or approval. "present" and "current" describe inclusion in the
# package, not correctness of the design.
ALLOWED_PLAN_SHEET_STATUSES: set[str] = {
    "present",
    "missing",
    "referenced_not_included",
    "superseded",
    "current",
    "needs_reviewer_confirmation",
}

# Phase 6 plan reference consistency statuses. These record whether a reference
# target was located and whether labels agree, never whether a design is sound.
ALLOWED_PLAN_REFERENCE_STATUSES: set[str] = {
    "consistent",
    "missing_target",
    "conflicting_label",
    "unclear",
    "needs_human_review",
}

# Phase 6 plan consistency finding types. Each describes a review-support gap or
# conflict to surface for a human reviewer.
ALLOWED_PLAN_FINDING_TYPES: set[str] = {
    "missing_sheet",
    "missing_referenced_sheet",
    "conflicting_label",
    "missing_plan_reference",
    "unclear_revision",
    "cad_metadata_gap",
    "requires_human_review",
}

# Phase 6 plan consistency finding statuses. Every plan finding starts under
# human review and never reaches a final approval state.
ALLOWED_PLAN_FINDING_STATUSES: set[str] = {
    "draft",
    "requires_human_review",
    "accepted_by_reviewer",
    "rejected_by_reviewer",
    "escalated",
    "requested_more_information",
}

# Evidence roles a finding source may carry. None of these is a conclusion.
ALLOWED_EVIDENCE_ROLES: set[str] = {
    "supports_finding",
    "shows_missing_evidence",
    "shows_conflict",
    "context_only",
    "requires_reviewer_confirmation",
}

# Standard note attached to retrieval and evidence responses to keep the
# professional boundary explicit in API payloads and the UI.
EVIDENCE_SAFETY_NOTE: str = (
    "This is source evidence for reviewer evaluation, not a final engineering "
    "conclusion."
)

# Sanctioned review-support phrasing, kept here for reference and reuse.
SANCTIONED_REVIEW_LANGUAGE: set[str] = {
    "potential issue",
    "requires reviewer confirmation",
    "missing evidence",
    "conflicting information",
    "based on submitted documents",
    "recommended follow-up",
    "needs human review",
    "review-support finding",
}


def is_allowed_status(status: str) -> bool:
    """Return True if the status is in the allowed review vocabulary."""

    return status in ALLOWED_REVIEW_STATUSES


def is_human_review_status(status: str) -> bool:
    """Return True if the status keeps the finding under human review."""

    return status in HUMAN_REVIEW_STATUSES


def contains_prohibited_language(text: str | None) -> bool:
    """Return True if text contains any prohibited final-decision wording.

    This is intended for validating statuses and short conclusion labels, not
    for scanning long explanatory prose that may legitimately discuss what the
    system does not do.
    """

    if not text:
        return False
    normalized = text.strip().lower()
    return any(word in normalized for word in PROHIBITED_FINAL_DECISION_WORDS)


def find_prohibited_language(text: str | None) -> list[str]:
    """Return the list of prohibited words found in text, if any."""

    if not text:
        return []
    normalized = text.strip().lower()
    return [word for word in PROHIBITED_FINAL_DECISION_WORDS if word in normalized]
