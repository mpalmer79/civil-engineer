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

# Phase 14 reviewer command center and project health dashboard vocabulary. The
# dashboard aggregates existing review-support data into one operational view. It
# organizes review-support work and never approves plans, certifies compliance,
# verifies CAD, validates design, closes or resolves issues, or makes final
# engineering decisions.

# Overall command center status. None implies a final engineering decision,
# approval, compliance state, or that any issue is resolved or closed.
ALLOWED_COMMAND_CENTER_STATUSES: set[str] = {
    "draft",
    "active_review",
    "needs_attention",
    "ready_for_handoff",
    "needs_more_information",
    "reviewer_checked",
}

# Severity labels for health metrics and attention items. These describe review
# attention, not a safety determination.
ALLOWED_DASHBOARD_SEVERITIES: set[str] = {
    "info",
    "low",
    "medium",
    "high",
    "needs_human_review",
}

# Reviewer attention item statuses. A reviewer may mark an attention item
# reviewer_checked, deferred, or not_applicable. None of these closes, resolves,
# or approves anything.
ALLOWED_ATTENTION_ITEM_STATUSES: set[str] = {
    "open",
    "reviewer_checked",
    "deferred",
    "not_applicable",
}

# Review readiness statuses. ready_for_human_review means an area is organized
# enough for human review, never that it is complete, passed, or approved. There
# is intentionally no complete, completed, passed, failed, approved, certified,
# verified, compliant, safe, resolved, or closed value.
ALLOWED_READINESS_STATUSES: set[str] = {
    "not_started",
    "needs_attention",
    "in_review",
    "ready_for_human_review",
    "reviewer_checked",
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


# Production Foundations Sprint 1 real project intake vocabulary. These describe
# where a real, user-created project record sits in the review-support intake
# workflow. None implies a final engineering decision, approval, certification,
# compliance state, or that a project is safe. archived_demo retires a record.
ALLOWED_PROJECT_STATUSES: set[str] = {
    "intake_started",
    "documents_registered",
    "reviewer_triage",
    "under_review_support",
    "response_draft_ready",
    "awaiting_applicant_response",
    "resubmittal_received",
    "archived_demo",
}

# source_mode values for a project record. demo_fixture is the seeded Brookside
# Meadows demo; user_created is a real reviewer-created project record.
ALLOWED_PROJECT_SOURCE_MODES: set[str] = {"demo_fixture", "user_created"}

# Document processing statuses for registered or uploaded documents. None of
# these implies document approval; they track intake handling only.
ALLOWED_DOCUMENT_PROCESSING_STATUSES: set[str] = {
    "registered",
    "uploaded",
    "intake_pending",
    "metadata_recorded",
    "parsing_pending",
    "parsed_with_warnings",
    "parsing_not_available",
    "needs_reviewer_review",
}

# source_mode values for a document record.
ALLOWED_DOCUMENT_SOURCE_MODES: set[str] = {
    "demo_fixture",
    "user_registered",
    "user_uploaded",
}

# Reviewer-created finding statuses (the human_review_status of a real finding).
# Every value keeps the finding under human review. There is intentionally no
# resolved, closed, approved, failed, passed, verified, or certified value.
ALLOWED_REVIEWER_FINDING_STATUSES: set[str] = {
    "draft",
    "needs_reviewer_confirmation",
    "evidence_missing",
    "evidence_conflicting",
    "evidence_unclear",
    "reviewer_action_needed",
    "ready_for_handoff",
    "applicant_response_received",
    "carried_forward_for_review",
}

# Evidence status labels a reviewer may assign to a finding. These describe the
# state of the evidence for review, never a final engineering conclusion.
ALLOWED_EVIDENCE_STATUSES: set[str] = {
    "potential_issue",
    "missing_evidence",
    "conflicting_evidence",
    "unclear_evidence",
    "needs_reviewer_confirmation",
}

# How a finding entered the system. reviewer_created is a real reviewer-owned
# finding; seeded_demo is a planted Brookside Meadows demo finding.
ALLOWED_FINDING_ORIGINS: set[str] = {
    "seeded_demo",
    "reviewer_created",
    "ai_draft",
    "imported",
}

# Actor types for real-action attribution. demo_seed marks seeded demo activity;
# reviewer is a real reviewer identity placeholder until real auth exists.
ALLOWED_ACTOR_TYPES: set[str] = {
    "demo_seed",
    "reviewer",
    "system",
    "applicant_placeholder",
    "admin_placeholder",
}


# Production Foundations Sprint 2 PDF page indexing and evidence citation
# vocabulary. Indexing extracts text from digital PDFs only (no OCR) and is
# deterministic. None of these values implies a final engineering decision,
# approval, certification, compliance state, or that a design is safe.

# Per-page text extraction statuses. no_extractable_text records a page with no
# embedded text layer (for example a scanned image), which is a normal outcome,
# not an error and not a conclusion.
ALLOWED_TEXT_EXTRACTION_STATUSES: set[str] = {
    "not_indexed",
    "indexing_started",
    "text_extracted",
    "no_extractable_text",
    "extraction_failed",
    "unsupported_file_type",
    "needs_reviewer_review",
}

# Document-level processing statuses including Sprint 2 indexing states. These
# track intake and indexing handling only; none implies document approval.
ALLOWED_DOCUMENT_PROCESSING_STATUSES_V2: set[str] = {
    "registered",
    "uploaded",
    "intake_pending",
    "metadata_recorded",
    "indexing_pending",
    "indexing_started",
    "indexed_with_text",
    "indexed_without_text",
    "indexed_with_warnings",
    "indexing_failed",
    "parsing_not_available",
    "needs_reviewer_review",
}

# How an evidence citation was created. reviewer_selected and manual_reference
# are reviewer-driven; extracted_text_reference cites indexed text; there is
# intentionally no verified or approved citation type.
ALLOWED_CITATION_TYPES: set[str] = {
    "reviewer_selected",
    "manual_reference",
    "extracted_text_reference",
    "seeded_demo_reference",
}

# Evidence citation statuses. page_reference_only records a citation to a page
# whose text could not be extracted. extraction_unavailable records that no
# indexed text backs the citation. None implies a final decision; there is
# intentionally no verified or approved citation status.
ALLOWED_CITATION_STATUSES: set[str] = {
    "draft",
    "needs_reviewer_confirmation",
    "reviewer_selected",
    "extraction_unavailable",
    "page_reference_only",
}


class ProhibitedLanguageError(ValueError):
    """Raised when user-provided text contains final-decision wording."""


def reject_prohibited_language(text: str | None, *, field: str) -> None:
    """Raise ProhibitedLanguageError if text uses final-decision wording.

    Used to keep reviewer-provided titles, categories, and notes within the
    review-support boundary. Long explanatory prose is not the target here; the
    short, labelled fields of a project, document, or finding are.
    """

    found = find_prohibited_language(text)
    if found:
        raise ProhibitedLanguageError(
            f"The {field} contains prohibited final-decision wording: "
            f"{', '.join(sorted(found))}. Use review-support language."
        )


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


# Production Foundations Sprint 3 evidence retrieval and reviewer draft finding
# queue vocabulary. Retrieval is deterministic and local over indexed PDF page
# text. A retrieval result is a candidate for reviewer evaluation, never a
# conclusion. None of these values implies a final engineering decision,
# approval, certification, compliance state, or that a design is safe.

# Retrieval query types a reviewer may run against indexed page text. combined
# allows a keyword query that also carries metadata filters.
ALLOWED_RETRIEVAL_QUERY_TYPES: set[str] = {
    "keyword",
    "phrase",
    "checklist_item",
    "finding_context",
    "document_filter",
    "combined",
    # Keyword search over real-derived DocumentChunk rows (chunks built from
    # indexed PDF page text). Distinct from the page-text "keyword" search.
    "chunk_keyword",
}

# Evidence candidate statuses. Every value keeps the candidate under reviewer
# control. promoted_to_draft records that a reviewer promoted the candidate into
# a draft finding; it is not a final outcome. There is intentionally no
# approved, verified, passed, failed, resolved, or closed value.
ALLOWED_CANDIDATE_STATUSES: set[str] = {
    "retrieval_candidate",
    "saved_for_review",
    "needs_reviewer_triage",
    "reviewer_selected",
    "promoted_to_draft",
    "dismissed_by_reviewer",
}

# How an evidence candidate entered the queue. manual_save records a candidate a
# reviewer saved directly; the search origins record which retrieval mode
# surfaced it.
ALLOWED_CANDIDATE_ORIGINS: set[str] = {
    "keyword_search",
    "phrase_search",
    "checklist_search",
    "finding_context_search",
    "manual_save",
    # A candidate surfaced by searching real-derived DocumentChunk rows.
    "chunk_search",
}

# Maximum number of retrieval results returned in a single search. Keeps result
# lists small and review-friendly and bounds audit metadata counts.
MAX_RETRIEVAL_RESULTS: int = 50

# Minimum length of a retrieval query string. Shorter queries are rejected as a
# validation error rather than scanning every page for one or two characters.
MIN_RETRIEVAL_QUERY_LENGTH: int = 2


# Production Foundations Sprint 4 checklist-driven evidence review and rule pack
# vocabulary. A rule pack is a reusable review-support template, not a legal
# ordinance and not a compliance standard. Checklist status is review-support
# only. None of these values implies a final engineering decision, approval,
# certification, compliance state, or that a design is safe. There is
# intentionally no compliant, noncompliant, approved, verified, passed, failed,
# resolved, or closed value anywhere in this vocabulary.

# How a rule pack or its items entered the system. seeded_demo marks the seeded
# starter pack; user_created and imported_template mark reviewer-provided packs.
ALLOWED_RULE_PACK_SOURCE_MODES: set[str] = {
    "seeded_demo",
    "user_created",
    "imported_template",
}

# Project checklist statuses. Each value keeps the checklist under reviewer
# control. archived_demo retires a checklist record.
ALLOWED_PROJECT_CHECKLIST_STATUSES: set[str] = {
    "checklist_started",
    "checklist_in_progress",
    "needs_reviewer_review",
    "ready_for_reviewer_handoff",
    "archived_demo",
}

# Whether a checklist item applies to a project, as judged by a reviewer. The
# system never decides applicability on its own.
ALLOWED_CHECKLIST_APPLICABILITY_STATUSES: set[str] = {
    "applies",
    "not_applicable_by_reviewer",
    "applicability_unclear",
    "needs_reviewer_confirmation",
}

# Evidence status a reviewer may assign to a checklist item. These describe the
# state of the evidence for review, never a final engineering conclusion.
# evidence_found records that a reviewer located relevant evidence; it does not
# certify or validate the design.
ALLOWED_CHECKLIST_EVIDENCE_STATUSES: set[str] = {
    "not_reviewed",
    "evidence_found",
    "missing_evidence",
    "conflicting_evidence",
    "unclear_evidence",
    "extraction_unavailable",
    "needs_reviewer_confirmation",
}

# Review progress status for a checklist item. draft_finding_created records that
# a reviewer promoted the item into a draft finding; it is not a final outcome.
ALLOWED_CHECKLIST_REVIEW_STATUSES: set[str] = {
    "not_started",
    "evidence_review_needed",
    "reviewer_note_added",
    "citation_added",
    "draft_finding_created",
    "ready_for_reviewer_handoff",
}

# Status of a checklist evidence link. page_reference_only records a link to a
# page whose text could not be extracted; extraction_unavailable records that no
# indexed text backs the link.
ALLOWED_CHECKLIST_LINK_STATUSES: set[str] = {
    "reviewer_selected",
    "citation_candidate",
    "needs_reviewer_confirmation",
    "extraction_unavailable",
    "page_reference_only",
}

# Context an EvidenceCitation serves. checklist_evidence marks a citation linked
# to a checklist item; finding_citation marks a finding citation; candidate_source
# marks a citation produced from a retrieval candidate.
ALLOWED_CITATION_CONTEXTS: set[str] = {
    "finding_citation",
    "checklist_evidence",
    "candidate_source",
}


# Production Foundations Sprint 5 authentication and access control vocabulary.
# Roles and access levels control who may view or act on review records and
# improve audit attribution. They never introduce final engineering decision
# workflows and never imply approval, certification, or compliance.

# Organization account types. internal_demo and demo_organization mark seeded
# demo organizations; the others describe real organization accounts.
ALLOWED_ORGANIZATION_TYPES: set[str] = {
    "municipality",
    "consulting_engineer",
    "developer_applicant",
    "county_agency",
    "demo_organization",
    "internal_demo",
}

# Organization membership roles. demo_reviewer behaves as a reviewer for the
# local demo; applicant_placeholder is intentionally limited and holds no
# reviewer actions yet.
ALLOWED_MEMBERSHIP_ROLES: set[str] = {
    "org_admin",
    "senior_reviewer",
    "reviewer",
    "read_only",
    "applicant_placeholder",
    "demo_reviewer",
}

# Per-project access levels. project_admin can manage project access; reviewer
# and senior_reviewer can take reviewer actions; read_only can view only;
# applicant_placeholder is limited and holds no reviewer actions yet.
ALLOWED_PROJECT_ACCESS_LEVELS: set[str] = {
    "project_admin",
    "reviewer",
    "senior_reviewer",
    "read_only",
    "applicant_placeholder",
}

# Roles and access levels that may take reviewer (write) actions on a project.
REVIEWER_ACCESS_LEVELS: set[str] = {
    "project_admin",
    "senior_reviewer",
    "reviewer",
}
REVIEWER_MEMBERSHIP_ROLES: set[str] = {
    "org_admin",
    "senior_reviewer",
    "reviewer",
    "demo_reviewer",
}

# Project visibility modes. demo_public projects may be read without a login when
# AUTH_ALLOW_PUBLIC_DEMO is true; controlled projects require explicit access.
ALLOWED_PROJECT_VISIBILITY_MODES: set[str] = {
    "controlled",
    "organization_visible",
    "demo_public",
}

# Actor types for authenticated audit attribution, extending the Sprint 1 set.
ALLOWED_AUTH_ACTOR_TYPES: set[str] = {
    "user",
    "org_admin",
    "reviewer",
    "senior_reviewer",
    "read_only",
    "applicant_placeholder",
    "demo_reviewer",
    "system",
}


# Production Foundations Sprint 6 durable file storage vocabulary. Storage tracks
# where an uploaded review-support record is stored and whether it is available.
# It never implies a final engineering decision, approval, certification, or
# compliance, and it never changes the review-support boundary.

# Storage provider names. local stores files on the service file system for
# development; s3 uses S3-compatible object storage for deployment.
ALLOWED_STORAGE_PROVIDERS: set[str] = {"local", "s3"}

# Document upload handling statuses for stored files. None implies approval; they
# track storage handling only. storage_failed records that a file could not be
# stored, not an engineering determination.
ALLOWED_STORAGE_UPLOAD_STATUSES: set[str] = {
    "not_uploaded",
    "upload_started",
    "stored",
    "storage_failed",
    "file_unavailable",
}


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


# Production Foundations Sprint 9 reviewer dashboard, workload management, and
# operational metrics vocabulary. The dashboard aggregates existing
# review-support data into cross-project operational indicators. Counts describe
# pending reviewer work, not engineering outcomes. None of these values implies a
# final engineering decision, approval, certification, compliance state, or that
# any issue is resolved or closed. There is intentionally no approved, closed,
# resolved, passed, failed, compliant, verified, certified, safe, or unsafe value
# anywhere in this vocabulary.

# Review priority a reviewer or admin may set on a project to help sequence
# workload. These are workflow sequencing labels, not engineering judgments.
# urgent is intentionally absent; time_sensitive is the strongest label.
ALLOWED_REVIEW_PRIORITIES: set[str] = {
    "low",
    "standard",
    "elevated",
    "time_sensitive",
}

# Aging buckets for pending reviewer actions. These describe how long an item has
# been waiting for reviewer attention, computed from record timestamps. They are
# workflow timing helpers, never an overdue or compliance determination.
ALLOWED_AGING_BUCKETS: set[str] = {
    "updated_today",
    "waiting_1_to_3_days",
    "waiting_4_to_7_days",
    "waiting_more_than_7_days",
}

# Due date indicators, used only when a project has an explicit review_due_date.
# past_due_for_reviewer_attention is a workflow timing indicator that the due
# date has passed, never an engineering outcome.
ALLOWED_DUE_DATE_INDICATORS: set[str] = {
    "due_date_set",
    "due_soon",
    "past_due_for_reviewer_attention",
}

# Reviewer workload snapshot scopes, if a snapshot is computed or stored.
ALLOWED_WORKLOAD_SNAPSHOT_SCOPES: set[str] = {
    "reviewer",
    "organization",
    "project",
}

# Reviewer queue item types. Each names an operational reviewer action surfaced
# on the dashboard queue. None implies a final decision; each points a reviewer
# to a project workflow page where human review continues.
ALLOWED_QUEUE_ITEM_TYPES: set[str] = {
    "document_indexing",
    "evidence_candidate_triage",
    "checklist_evidence_review",
    "applicant_response_review",
    "carried_forward_matrix_item",
    "response_package_handoff",
}


# Production Foundations Sprint 10 deployment hardening, environment validation,
# and observability vocabulary. Diagnostics describe operational readiness only.
# A status, severity, or category never approves a project, certifies compliance,
# verifies CAD, validates design, declares safety, resolves an issue, or closes an
# issue. There is intentionally no approved, certified, verified, passed, failed,
# compliant, noncompliant, safe, or unsafe value anywhere in this vocabulary.

# Diagnostic categories an environment validation item may belong to. These group
# configuration checks for operator review only.
ALLOWED_DIAGNOSTIC_CATEGORIES: set[str] = {
    "application",
    "database",
    "authentication",
    "storage",
    "object_storage",
    "public_demo",
    "cors",
    "deployment",
    "frontend_integration",
}

# Diagnostic status values for environment, readiness, and storage checks. Each
# describes a configuration or connectivity state, never an engineering outcome.
# needs_operator_review asks a human operator to look at a setting; it is not a
# failure determination.
ALLOWED_DIAGNOSTIC_STATUSES: set[str] = {
    "ready",
    "configured",
    "missing_required",
    "missing_optional",
    "warning",
    "disabled",
    "unavailable",
    "needs_operator_review",
}

# Diagnostic severity levels. These rank operator attention only.
ALLOWED_DIAGNOSTIC_SEVERITIES: set[str] = {
    "info",
    "notice",
    "warning",
    "critical",
}
