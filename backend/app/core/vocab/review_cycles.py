"""Multi-round review cycle, resubmittal, and revision comparison vocabulary."""

from __future__ import annotations

# Phase 13 multi-round resubmittal, revision comparison, and applicant response
# cycle vocabulary. These describe where a review-support item sits in a
# multi-round review workflow. None implies a final engineering decision,
# approval, certification, compliance state, or CAD verification. Revision
# comparison compares extracted DXF metadata only; it never validates design.

# Review cycle (one round of review for a project).
ALLOWED_REVIEW_CYCLE_STATUSES: set[str] = {
    "draft",
    "active",
    "reviewer_checked",
    "ready_for_next_cycle",
    "archived",
}

# Resubmittal package lifecycle states.
ALLOWED_RESUBMITTAL_STATUSES: set[str] = {
    "received",
    "intake_review",
    "needs_more_information",
    "ready_for_comparison",
    "comparison_complete",
    "reviewer_checked",
    "archived",
}

# Resubmittal document types attached to a resubmittal package.
ALLOWED_RESUBMITTAL_DOCUMENT_TYPES: set[str] = {
    "dxf_cad_file",
    "applicant_response_note",
    "revised_plan_reference",
    "supplemental_document",
    "other",
}

# Resubmittal document lifecycle states.
ALLOWED_RESUBMITTAL_DOCUMENT_STATUSES: set[str] = {
    "received",
    "linked",
    "needs_human_review",
    "excluded_from_review_cycle",
}

# Applicant response lifecycle states.
ALLOWED_APPLICANT_RESPONSE_STATUSES: set[str] = {
    "received",
    "mapped_to_issue",
    "needs_clarification",
    "reviewer_checked",
    "carried_forward",
}

# Confidence labels for an applicant response mapping suggestion. There is
# intentionally no "verified" label: mapping is review-support, not verification.
ALLOWED_MAPPING_CONFIDENCE_LABELS: set[str] = {
    "high",
    "medium",
    "low",
    "needs_human_review",
}

# Revision comparison run statuses. completed_with_warnings records a successful
# comparison that surfaced review-support warnings, never a pass or fail.
ALLOWED_REVISION_COMPARISON_STATUSES: set[str] = {
    "draft",
    "completed",
    "completed_with_warnings",
    "needs_human_review",
    "archived",
}

# Revision change types describing how a piece of extracted DXF metadata differs
# between two parse rounds. None implies an engineering judgment.
ALLOWED_REVISION_CHANGE_TYPES: set[str] = {
    "added",
    "removed",
    "changed",
    "unchanged",
    "carried_forward",
}

# Source categories a revision change record may describe.
ALLOWED_REVISION_SOURCE_CATEGORIES: set[str] = {
    "layer",
    "text_reference",
    "sheet_reference",
    "detail_reference",
    "pipe_label",
    "basin_label",
    "outfall_label",
    "wetland_buffer_label",
    "block",
    "unknown",
}

# Reviewer statuses on a revision change record.
ALLOWED_REVISION_REVIEWER_STATUSES: set[str] = {
    "draft",
    "needs_follow_up",
    "needs_more_information",
    "reviewer_checked",
    "carried_forward",
    "excluded_from_cycle",
}

# Issue carry-forward statuses.
ALLOWED_CARRY_FORWARD_STATUSES: set[str] = {
    "carried_forward",
    "needs_more_information",
    "needs_follow_up",
    "reviewer_checked",
}

# Response resolution statuses. addressed_for_review means the item appears
# addressed in the reviewer's judgment and is ready for human review, never that
# it is resolved, closed, approved, or certified. There is intentionally no
# resolved, closed, fixed, passed, approved, verified, compliant, or final value.
ALLOWED_RESOLUTION_STATUSES: set[str] = {
    "addressed_for_review",
    "still_open",
    "needs_more_information",
    "carried_forward",
    "reviewer_checked",
    "excluded_from_cycle",
}

# Next-cycle preparation statuses.
ALLOWED_NEXT_CYCLE_STATUSES: set[str] = {
    "draft",
    "ready_for_next_cycle",
    "needs_human_review",
    "archived",
}
