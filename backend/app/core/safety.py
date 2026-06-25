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

# Phase 8 review packet statuses. These apply to packets, sections, and items.
# None implies a final engineering decision, approval, or certification.
ALLOWED_REVIEW_PACKET_STATUSES: set[str] = {
    "draft",
    "needs_follow_up",
    "reviewer_checked",
    "excluded_from_packet",
    "needs_more_information",
}

# Phase 8 review packet reviewer actions a reviewer may record on a packet item.
# There is intentionally no action called approve. Each action type is the
# target status it sets, so a stored action_type is always one of the allowed
# packet statuses (there is no synthetic status_update action type).
ALLOWED_REVIEW_PACKET_ACTIONS: set[str] = {
    "draft",
    "needs_follow_up",
    "reviewer_checked",
    "excluded_from_packet",
    "needs_more_information",
}

PACKET_ACTION_TO_STATUS: dict[str, str] = {
    "draft": "draft",
    "needs_follow_up": "needs_follow_up",
    "reviewer_checked": "reviewer_checked",
    "excluded_from_packet": "excluded_from_packet",
    "needs_more_information": "needs_more_information",
}

# Phase 9 reviewer workflow board statuses. These describe where a
# review-support item sits in the operational review workflow. None implies a
# final engineering decision, approval, certification, or compliance state.
ALLOWED_WORKFLOW_STATUSES: set[str] = {
    "draft",
    "needs_triage",
    "needs_follow_up",
    "needs_more_information",
    "reviewer_checked",
    "excluded_from_packet",
    "ready_for_handoff",
}

# Phase 9 workflow action types recorded when a reviewer acts on a workflow
# item. There is intentionally no action called approve.
ALLOWED_WORKFLOW_ACTIONS: set[str] = {
    "triage_started",
    "follow_up_requested",
    "more_information_requested",
    "reviewer_checked",
    "excluded_from_packet",
    "ready_for_handoff",
    "note_added",
    "target_date_updated",
}

# Maps a requested workflow status transition to the action type it records.
# draft is the initial seeded status and is not a manual transition target, so
# it is intentionally absent: requesting it is rejected as an invalid status.
WORKFLOW_STATUS_TO_ACTION: dict[str, str] = {
    "needs_triage": "triage_started",
    "needs_follow_up": "follow_up_requested",
    "needs_more_information": "more_information_requested",
    "reviewer_checked": "reviewer_checked",
    "excluded_from_packet": "excluded_from_packet",
    "ready_for_handoff": "ready_for_handoff",
}

# Phase 9 follow-up request statuses. None uses final-decision language.
ALLOWED_FOLLOW_UP_STATUSES: set[str] = {
    "open",
    "response_needed",
    "reviewer_checked",
    "closed_without_decision",
}

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

# Evidence roles a finding source may carry. None of these is a conclusion.
ALLOWED_EVIDENCE_ROLES: set[str] = {
    "supports_finding",
    "shows_missing_evidence",
    "shows_conflict",
    "context_only",
    "requires_reviewer_confirmation",
}

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
