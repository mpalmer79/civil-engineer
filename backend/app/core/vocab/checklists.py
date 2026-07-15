"""Checklist-driven evidence review and rule pack vocabulary."""

from __future__ import annotations

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
