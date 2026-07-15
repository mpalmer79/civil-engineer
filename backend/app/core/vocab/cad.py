"""Real CAD (DXF) intake, parsing, and CAD review finding vocabulary."""

from __future__ import annotations

# Phase 11 real CAD (DXF) intake vocabulary. Parsing extracts review-support
# metadata from a real DXF file. It never verifies CAD, validates geometry or
# design, certifies compliance, or makes a final engineering decision. None of
# these values uses final-decision language.

# Supported CAD file types for intake. DXF only in this phase. DWG parsing is
# documented as future work and is intentionally absent.
ALLOWED_CAD_FILE_TYPES: set[str] = {"dxf"}

# Upload lifecycle states for a CAD file record.
ALLOWED_CAD_UPLOAD_STATUSES: set[str] = {
    "uploaded",
    "parsed",
    "parse_failed",
    "needs_human_review",
}

# Phase 12 browser upload validation statuses. These record whether a browser
# DXF upload passed intake validation (extension, size, content type, and
# readability), never whether a design is sound. needs_human_review means the
# file was stored but a reviewer should confirm it before relying on it.
ALLOWED_CAD_VALIDATION_STATUSES: set[str] = {
    "accepted",
    "rejected",
    "needs_human_review",
}

# Phase 12 parse queue statuses. These describe where an uploaded DXF file sits
# in the manual parse queue. "failed" here means the parser could not read the
# file (a technical parse failure), not an engineering failure or a final
# decision about the plan. None of these values uses final-decision language.
ALLOWED_CAD_QUEUE_STATUSES: set[str] = {
    "queued",
    "parsing",
    "completed",
    "completed_with_warnings",
    "failed",
    "needs_human_review",
}

# DXF parse run states. completed_with_warnings records a successful parse that
# surfaced review-support warnings, never a pass or fail determination.
ALLOWED_CAD_PARSE_STATUSES: set[str] = {
    "started",
    "completed",
    "completed_with_warnings",
    "failed",
    "needs_human_review",
}

# Review categories a layer, entity, block, or text extract may be sorted into.
# These are descriptive routing categories, not conclusions. unknown means the
# category needs human review.
ALLOWED_CAD_REVIEW_CATEGORIES: set[str] = {
    "stormwater",
    "grading",
    "erosion_control",
    "utilities",
    "wetland_buffer",
    "titleblock",
    "notes",
    "unknown",
    # Data-driven taxonomy categories (app.services.cad.layer_taxonomy).
    "property_boundary",
    "road_alignment",
    "lots_parcels",
    "annotation",
    "landscape",
    "existing_conditions",
    "survey_control",
    "structures",
}

# Reference types detected in extracted text. unknown means it needs human
# review.
ALLOWED_CAD_REFERENCE_TYPES: set[str] = {
    "sheet_reference",
    "detail_reference",
    "pipe_label",
    "basin_label",
    "outfall_label",
    "wetland_buffer_label",
    "revision_note",
    "general_note",
    "unknown",
}

# Confidence labels for a reference match candidate. There is intentionally no
# "verified" label: matching is review-support, not verification.
ALLOWED_CAD_CONFIDENCE_LABELS: set[str] = {
    "high",
    "medium",
    "low",
    "needs_human_review",
}

# CAD review finding types. Each describes a review-support gap, conflict, or
# uncertainty for a human reviewer to confirm.
ALLOWED_CAD_FINDING_TYPES: set[str] = {
    "missing_sheet_reference",
    "unclear_detail_reference",
    "possible_label_conflict",
    "missing_plan_sheet_match",
    "unknown_layer_category",
    "parse_warning",
    "needs_human_review",
}

# CAD review finding statuses. Every finding starts as a draft under human
# review and never reaches an approval or compliance state.
ALLOWED_CAD_FINDING_STATUSES: set[str] = {
    "draft",
    "needs_follow_up",
    "needs_more_information",
    "reviewer_checked",
    "excluded_from_packet",
}
