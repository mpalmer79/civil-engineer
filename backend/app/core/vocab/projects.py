"""Real project intake, document intake, and reviewer finding vocabulary."""

from __future__ import annotations

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
