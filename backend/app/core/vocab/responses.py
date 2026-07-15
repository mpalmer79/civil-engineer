"""Applicant response matrix and resubmittal collaboration vocabulary."""

from __future__ import annotations

# Production Foundations Sprint 7 applicant response matrix and resubmittal
# collaboration vocabulary. These track applicant responses and resubmittal
# rounds for reviewer review. None implies a final engineering decision,
# approval, certification, compliance, or that an issue is resolved or closed.
# There is intentionally no resolved, closed, approved, verified, passed, failed,
# compliant, noncompliant, safe, or unsafe value anywhere in this vocabulary.

# Response matrix statuses. Each value keeps the matrix under reviewer control.
ALLOWED_RESPONSE_MATRIX_STATUSES: set[str] = {
    "matrix_started",
    "matrix_in_progress",
    "awaiting_applicant_response",
    "applicant_response_received",
    "needs_reviewer_follow_up",
    "ready_for_reviewer_handoff",
    "archived_demo",
}

# Applicant response statuses for a matrix item. An applicant response is
# recorded as submitted content for reviewer review; it is never treated as
# proof and never marks an item satisfied.
ALLOWED_APPLICANT_RESPONSE_STATUSES_V2: set[str] = {
    "response_not_requested",
    "awaiting_applicant_response",
    "applicant_response_received",
    "applicant_response_incomplete",
    "response_needs_reviewer_review",
    "response_recorded_for_review",
}

# Reviewer follow-up statuses for a matrix item. All are review-support only.
ALLOWED_REVIEWER_FOLLOW_UP_STATUSES: set[str] = {
    "not_reviewed",
    "needs_reviewer_confirmation",
    "needs_applicant_follow_up",
    "evidence_updated",
    "reviewer_note_added",
    "ready_for_reviewer_handoff",
}

# Carry-forward statuses for a matrix item. carried_forward means the item
# remains under review; it is never a final resolution.
ALLOWED_CARRY_FORWARD_STATUSES_V2: set[str] = {
    "not_carried_forward",
    "carried_forward_for_review",
    "carried_forward_with_updated_evidence",
    "carried_forward_needs_applicant_response",
}

# Resubmittal round statuses. Each value tracks round handling for reviewer
# review; none implies a final outcome.
ALLOWED_RESUBMITTAL_ROUND_STATUSES: set[str] = {
    "round_registered",
    "documents_received",
    "indexing_needed",
    "evidence_review_needed",
    "response_review_in_progress",
    "ready_for_reviewer_handoff",
    "archived_demo",
}

# Link types for a document linked to a matrix item or a resubmittal round.
ALLOWED_MATRIX_LINK_TYPES: set[str] = {
    "applicant_response_document",
    "revised_plan_reference",
    "revised_report_reference",
    "supporting_response_evidence",
    "reviewer_reference",
}
