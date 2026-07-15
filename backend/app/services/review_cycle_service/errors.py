"""Errors and shared constants for the review cycle service.

This module holds the review cycle error type and the module-level constants
used across the review cycle submodules. Everything here is review-support and
evidence-organization only. It does not approve plans, certify compliance,
stamp drawings, verify CAD, validate design, or make final engineering
decisions.
"""

from __future__ import annotations

LIMITATIONS_NOTE = (
    "Revision comparison compares extracted DXF metadata only (layers, "
    "references, blocks, and review findings). It does not verify CAD, validate "
    "geometry or design, certify compliance, approve plans, or replace a "
    "licensed Professional Engineer. All statuses are review-support statuses, "
    "not final engineering decisions."
)

# Reference candidate type to revision source category.
REF_TYPE_TO_CATEGORY: dict[str, str] = {
    "sheet_reference": "sheet_reference",
    "detail_reference": "detail_reference",
    "pipe_label": "pipe_label",
    "basin_label": "basin_label",
    "outfall_label": "outfall_label",
    "wetland_buffer_label": "wetland_buffer_label",
    "revision_note": "text_reference",
    "general_note": "text_reference",
    "unknown": "unknown",
}

# CAD finding type to revision source category.
FINDING_TYPE_TO_CATEGORY: dict[str, str] = {
    "missing_plan_sheet_match": "sheet_reference",
    "missing_sheet_reference": "sheet_reference",
    "unclear_detail_reference": "detail_reference",
    "possible_label_conflict": "basin_label",
    "unknown_layer_category": "layer",
    "parse_warning": "unknown",
}

# Categories whose identity tolerates a value change (so a changed distance or
# number reads as a changed item rather than a remove plus add).
STEM_CATEGORIES = {"basin_label", "wetland_buffer_label", "text_reference"}


class ReviewCycleError(Exception):
    """Raised when a review cycle operation is not allowed."""

    def __init__(self, message: str, *, status_code: int = 400) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code
