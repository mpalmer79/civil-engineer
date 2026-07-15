"""Plan sheet, plan reference, plan finding, and sheet hotspot vocabulary."""

from __future__ import annotations

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
    # Phase 7 plan consistency review action outcomes.
    "needs_follow_up",
    "reviewer_confirmed",
    "not_applicable",
    "needs_more_information",
}

# Phase 7 plan consistency review actions a reviewer may record on a plan
# consistency finding. None of these is a final engineering decision, and there
# is intentionally no action called "approve". Each maps to a review-support
# finding status of the same name.
ALLOWED_PLAN_REVIEW_ACTIONS: set[str] = {
    "needs_follow_up",
    "reviewer_confirmed",
    "not_applicable",
    "needs_more_information",
}

PLAN_REVIEW_ACTION_TO_STATUS: dict[str, str] = {
    "needs_follow_up": "needs_follow_up",
    "reviewer_confirmed": "reviewer_confirmed",
    "not_applicable": "not_applicable",
    "needs_more_information": "needs_more_information",
}

# Phase 7 sheet hotspot types. Each is a descriptive review-support annotation
# category placed over a seeded plan sheet preview. None implies a final
# decision, CAD verification, or design validation.
ALLOWED_SHEET_HOTSPOT_TYPES: set[str] = {
    "missing_referenced_sheet",
    "basin_label_conflict",
    "maintenance_ownership",
    "pipe_reference",
    "unclear_revision",
    "erosion_control_detail",
    "basin_outlet_detail",
    "wetland_buffer_setback",
}

# Phase 7 sheet hotspot severities. These describe review attention, not a
# safety determination.
ALLOWED_SHEET_HOTSPOT_SEVERITIES: set[str] = {"low", "medium", "high"}
