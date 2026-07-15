"""External response package, reviewer package, and comment letter vocabulary."""

from __future__ import annotations

# Phase 10 external review response package statuses. These describe where a
# draft external response package sits in the reviewer's preparation workflow.
# None implies a final engineering decision, approval, certification, or
# compliance state. archived means the reviewer set the draft aside.
ALLOWED_RESPONSE_PACKAGE_STATUSES: set[str] = {
    "draft",
    "needs_revision",
    "reviewer_checked",
    "ready_for_handoff",
    "archived",
}

# Phase 10 response item statuses. These describe whether a draft response item
# is part of the draft communication and whether a reviewer has checked it. None
# implies a final engineering decision.
ALLOWED_RESPONSE_ITEM_STATUSES: set[str] = {
    "draft",
    "included",
    "excluded",
    "needs_revision",
    "reviewer_checked",
}

# Phase 10 response action types recorded when a reviewer acts on a response
# package or item. There is intentionally no action called approve, and none
# approves, certifies, verifies, or validates anything.
ALLOWED_RESPONSE_ACTIONS: set[str] = {
    "package_generated",
    "item_included",
    "item_excluded",
    "item_revised",
    "reviewer_checked",
    "note_added",
    "package_marked_ready_for_handoff",
    "package_archived",
}

# Maps a requested response item status transition to the action type it
# records. draft is the seeded initial status and is not a manual transition
# target, so it is intentionally absent: requesting it is rejected.
RESPONSE_ITEM_STATUS_TO_ACTION: dict[str, str] = {
    "included": "item_included",
    "excluded": "item_excluded",
    "needs_revision": "item_revised",
    "reviewer_checked": "reviewer_checked",
}

# Maps a requested response package status transition to the action type it
# records. draft is the seeded initial status and is not a manual transition
# target. needs_revision reuses the item_revised action because the action set
# has a single revision action and the audit metadata records the status pair.
RESPONSE_PACKAGE_STATUS_TO_ACTION: dict[str, str] = {
    "needs_revision": "item_revised",
    "reviewer_checked": "reviewer_checked",
    "ready_for_handoff": "package_marked_ready_for_handoff",
    "archived": "package_archived",
}

# Phase 10 response package audience types. These describe who a draft response
# is addressed to. They are routing labels, not engineering authority.
ALLOWED_RESPONSE_AUDIENCE_TYPES: set[str] = {
    "applicant",
    "design_engineer",
    "municipal_reviewer",
    "internal_review_team",
}


# Production Foundations Sprint 8 reviewer response package and comment letter
# vocabulary. A response package is a reviewer-controlled communication artifact.
# Issuance records that a reviewer issued a communication; it never approves a
# project, certifies compliance, validates design, resolves an issue, or closes an
# issue. A comment letter draft is a deterministic, reviewer-editable template. No
# value here implies a final engineering decision.

# Response package statuses. issued_by_reviewer records a reviewer communication
# only; it is not approval, certification, or issue closure.
ALLOWED_REVIEWER_PACKAGE_STATUSES: set[str] = {
    "package_draft",
    "package_in_review",
    "ready_for_reviewer_handoff",
    "issued_by_reviewer",
    "revision_started",
    "archived_demo",
}

# Response package types. Each describes the kind of reviewer communication being
# assembled, not an engineering outcome.
ALLOWED_REVIEWER_PACKAGE_TYPES: set[str] = {
    "initial_review_comment_letter",
    "resubmittal_review_comment_letter",
    "checklist_review_summary",
    "response_matrix_summary",
    "reviewer_handoff_package",
}

# Source types a package item can be assembled from.
ALLOWED_REVIEWER_PACKAGE_ITEM_SOURCE_TYPES: set[str] = {
    "finding",
    "checklist_item",
    "response_matrix_item",
    "citation",
    "document_reference",
    "resubmittal_summary",
    "manual_reviewer_note",
}

# Package item statuses. All are review-support workflow labels only.
ALLOWED_REVIEWER_PACKAGE_ITEM_STATUSES: set[str] = {
    "item_draft",
    "needs_reviewer_confirmation",
    "ready_for_reviewer_handoff",
    "carried_forward_for_review",
    "reviewer_note_added",
}

# Comment letter draft statuses. issued_by_reviewer records that a reviewer
# issued the communication draft; superseded_by_revision preserves prior issued
# drafts when a revision begins. None implies a final engineering decision.
ALLOWED_COMMENT_LETTER_DRAFT_STATUSES: set[str] = {
    "draft_created",
    "reviewer_editing",
    "ready_for_reviewer_handoff",
    "issued_by_reviewer",
    "superseded_by_revision",
}
