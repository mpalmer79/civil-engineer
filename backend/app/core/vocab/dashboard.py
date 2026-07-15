"""Command center, project health, and reviewer workload dashboard vocabulary."""

from __future__ import annotations

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
