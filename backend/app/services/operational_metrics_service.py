"""Operational metrics computation for the reviewer dashboard (Sprint 9).

Computes review-support workload counts and safe aging indicators from existing
review records. Every number here is an operational indicator that helps a
reviewer sequence work. None of these counts represents a final engineering
decision, approval, certification, compliance state, or that any issue is
resolved or closed. There is intentionally no approved, closed, resolved,
passed, failed, compliant, verified, certified, safe, or unsafe metric.

Metrics are computed in real time from the database. No persistent metric table
is required. The dashboard service composes these per-project metrics into
reviewer, organization, and project views and enforces access control before any
project is included.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db import models

# Document text extraction statuses that mean extraction could not produce
# usable text. These are normal outcomes for scanned or unsupported files, never
# an error conclusion and never an engineering determination.
EXTRACTION_UNAVAILABLE_STATUSES: set[str] = {
    "no_extractable_text",
    "unsupported_file_type",
    "extraction_failed",
    "parsing_not_available",
}

# Finding human review statuses that still need reviewer confirmation. Each keeps
# the finding under human review. Statuses that record a reviewer already acted
# (accepted, edited, rejected, escalated, not_applicable, ready_for_handoff) are
# intentionally excluded so the count reflects outstanding reviewer work only.
FINDING_NEEDS_CONFIRMATION_STATUSES: set[str] = {
    "not_started",
    "requires_human_review",
    "needs_reviewer_confirmation",
    "requested_more_information",
    "marked_unclear",
    "unclear",
    "unresolved",
    "validation_failed",
    "draft",
    "evidence_missing",
    "evidence_conflicting",
    "evidence_unclear",
    "reviewer_action_needed",
}

# Evidence candidate statuses that still need reviewer triage. promoted_to_draft
# and dismissed_by_reviewer record a reviewer already acted and are excluded.
CANDIDATE_NEEDS_TRIAGE_STATUSES: set[str] = {
    "retrieval_candidate",
    "saved_for_review",
    "needs_reviewer_triage",
    "reviewer_selected",
}

# Applicant response statuses on a matrix item that indicate a response is
# present and waiting for reviewer review.
APPLICANT_RESPONSE_NEEDS_REVIEW_STATUSES: set[str] = {
    "applicant_response_received",
    "response_needs_reviewer_review",
    "response_recorded_for_review",
}

# Reviewer follow-up statuses that mean a reviewer has not yet reviewed the
# applicant response.
FOLLOW_UP_NOT_REVIEWED_STATUSES: set[str] = {
    "not_reviewed",
    "needs_reviewer_confirmation",
}


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _as_aware(value: datetime | None) -> datetime | None:
    """Return a timezone-aware datetime, assuming UTC for naive values.

    SQLite stores naive datetimes. Treating them as UTC keeps aging arithmetic
    consistent across stored and freshly computed timestamps.
    """

    if value is None:
        return None
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value


def _count(db: Session, model, *conditions) -> int:
    stmt = select(func.count()).select_from(model)
    for condition in conditions:
        stmt = stmt.where(condition)
    return int(db.scalar(stmt) or 0)


def aging_bucket(reference: datetime | None, *, now: datetime | None = None) -> str:
    """Return a safe aging bucket label for a reference timestamp.

    The reference is the most recent activity timestamp for a record. Buckets are
    workflow timing helpers, never an overdue or compliance determination.
    """

    now = now or _now()
    reference = _as_aware(reference)
    if reference is None:
        return "waiting_more_than_7_days"
    age_days = (now - reference).total_seconds() / 86400.0
    if age_days < 1:
        return "updated_today"
    if age_days <= 3:
        return "waiting_1_to_3_days"
    if age_days <= 7:
        return "waiting_4_to_7_days"
    return "waiting_more_than_7_days"


def due_date_indicators(
    due_date: datetime | None, *, now: datetime | None = None
) -> list[str]:
    """Return due-date workflow indicators, only when a due date is set.

    past_due_for_reviewer_attention is a workflow timing indicator that the due
    date has passed. It is not an engineering outcome.
    """

    if due_date is None:
        return []
    now = now or _now()
    due_date = _as_aware(due_date)
    indicators = ["due_date_set"]
    delta_days = (due_date - now).total_seconds() / 86400.0
    if delta_days < 0:
        indicators.append("past_due_for_reviewer_attention")
    elif delta_days <= 3:
        indicators.append("due_soon")
    return indicators


def project_reference_timestamp(project: models.Project) -> datetime | None:
    """Pick the most recent activity timestamp for a project for aging."""

    candidates = [
        _as_aware(project.last_reviewer_activity_at),
        _as_aware(project.updated_at),
        _as_aware(project.created_at),
    ]
    present = [c for c in candidates if c is not None]
    return max(present) if present else None


def compute_project_metrics(
    db: Session, project: models.Project, *, now: datetime | None = None
) -> dict:
    """Compute the review-support workload metrics for a single project.

    Returns a flat dict of safe counts plus a pending_reviewer_action_count and a
    has_pending_reviewer_action flag. No count uses final-decision language.
    """

    now = now or _now()
    project_id = project.project_id

    # Document indexing and storage metrics.
    documents_uploaded = _count(
        db, models.Document, models.Document.project_id == project_id
    )
    documents_extraction_unavailable = _count(
        db,
        models.Document,
        models.Document.project_id == project_id,
        models.Document.text_extraction_status.in_(
            EXTRACTION_UNAVAILABLE_STATUSES
        ),
    )
    documents_indexed_with_text = _count(
        db,
        models.Document,
        models.Document.project_id == project_id,
        models.Document.indexed_at.is_not(None),
        models.Document.text_extraction_status.not_in(
            EXTRACTION_UNAVAILABLE_STATUSES
        ),
    )
    documents_needing_indexing = _count(
        db,
        models.Document,
        models.Document.project_id == project_id,
        models.Document.indexed_at.is_(None),
        models.Document.text_extraction_status.not_in(
            EXTRACTION_UNAVAILABLE_STATUSES
        ),
    )

    # Finding metrics.
    findings_needing_reviewer_confirmation = _count(
        db,
        models.Finding,
        models.Finding.project_id == project_id,
        models.Finding.human_review_status.in_(
            FINDING_NEEDS_CONFIRMATION_STATUSES
        ),
    )

    # Evidence candidate queue metrics.
    evidence_candidates_needing_triage = _count(
        db,
        models.EvidenceCandidate,
        models.EvidenceCandidate.project_id == project_id,
        models.EvidenceCandidate.candidate_status.in_(
            CANDIDATE_NEEDS_TRIAGE_STATUSES
        ),
    )

    # Checklist evidence status metrics.
    checklist_items_missing_evidence = _count(
        db,
        models.ProjectChecklistItem,
        models.ProjectChecklistItem.project_id == project_id,
        models.ProjectChecklistItem.evidence_status == "missing_evidence",
    )
    checklist_items_unclear_evidence = _count(
        db,
        models.ProjectChecklistItem,
        models.ProjectChecklistItem.project_id == project_id,
        models.ProjectChecklistItem.evidence_status == "unclear_evidence",
    )

    # Applicant response and resubmittal metrics.
    applicant_responses_needing_review = _count(
        db,
        models.ResponseMatrixItem,
        models.ResponseMatrixItem.project_id == project_id,
        models.ResponseMatrixItem.applicant_response_status.in_(
            APPLICANT_RESPONSE_NEEDS_REVIEW_STATUSES
        ),
        models.ResponseMatrixItem.reviewer_follow_up_status.in_(
            FOLLOW_UP_NOT_REVIEWED_STATUSES
        ),
    )
    matrix_items_carried_forward = _count(
        db,
        models.ResponseMatrixItem,
        models.ResponseMatrixItem.project_id == project_id,
        models.ResponseMatrixItem.carry_forward_status != "not_carried_forward",
    )
    resubmittal_rounds_registered = _count(
        db,
        models.ResubmittalRound,
        models.ResubmittalRound.project_id == project_id,
    )

    # Response package metrics.
    response_packages_draft = _count(
        db,
        models.ReviewerResponsePackage,
        models.ReviewerResponsePackage.project_id == project_id,
        models.ReviewerResponsePackage.status.in_(
            ("package_draft", "package_in_review")
        ),
    )
    response_packages_ready_for_handoff = _count(
        db,
        models.ReviewerResponsePackage,
        models.ReviewerResponsePackage.project_id == project_id,
        models.ReviewerResponsePackage.status == "ready_for_reviewer_handoff",
    )
    packages_issued_by_reviewer = _count(
        db,
        models.ReviewerResponsePackage,
        models.ReviewerResponsePackage.project_id == project_id,
        models.ReviewerResponsePackage.status == "issued_by_reviewer",
    )

    metrics = {
        "documents_uploaded": documents_uploaded,
        "documents_needing_indexing": documents_needing_indexing,
        "documents_indexed_with_text": documents_indexed_with_text,
        "documents_extraction_unavailable": documents_extraction_unavailable,
        "findings_needing_reviewer_confirmation": (
            findings_needing_reviewer_confirmation
        ),
        "evidence_candidates_needing_triage": evidence_candidates_needing_triage,
        "checklist_items_missing_evidence": checklist_items_missing_evidence,
        "checklist_items_unclear_evidence": checklist_items_unclear_evidence,
        "applicant_responses_needing_review": applicant_responses_needing_review,
        "resubmittal_rounds_registered": resubmittal_rounds_registered,
        "matrix_items_carried_forward": matrix_items_carried_forward,
        "response_packages_draft": response_packages_draft,
        "response_packages_ready_for_handoff": (
            response_packages_ready_for_handoff
        ),
        "packages_issued_by_reviewer": packages_issued_by_reviewer,
    }

    # Pending reviewer action is the sum of outstanding reviewer work. Issued and
    # indexed-with-text counts are informational and never counted as pending.
    pending = (
        documents_needing_indexing
        + findings_needing_reviewer_confirmation
        + evidence_candidates_needing_triage
        + checklist_items_missing_evidence
        + checklist_items_unclear_evidence
        + applicant_responses_needing_review
        + matrix_items_carried_forward
        + response_packages_ready_for_handoff
    )
    metrics["pending_reviewer_action_count"] = pending
    metrics["has_pending_reviewer_action"] = pending > 0
    return metrics


# Map each pending-action category to a queue item type and the project workflow
# path where a reviewer continues the action. Order controls queue display order.
QUEUE_CATEGORY_SPECS: list[tuple[str, str, str]] = [
    ("documents_needing_indexing", "document_indexing", "documents"),
    (
        "evidence_candidates_needing_triage",
        "evidence_candidate_triage",
        "evidence-candidates",
    ),
    (
        "checklist_items_missing_evidence",
        "checklist_evidence_review",
        "checklists",
    ),
    (
        "checklist_items_unclear_evidence",
        "checklist_evidence_review",
        "checklists",
    ),
    (
        "applicant_responses_needing_review",
        "applicant_response_review",
        "response-matrix",
    ),
    (
        "matrix_items_carried_forward",
        "carried_forward_matrix_item",
        "response-matrix",
    ),
    (
        "response_packages_ready_for_handoff",
        "response_package_handoff",
        "response-packages",
    ),
]

# Human-friendly status labels for each queue item type. All are review-support
# labels; none uses final-decision language.
QUEUE_TYPE_LABELS: dict[str, str] = {
    "document_indexing": "Documents needing indexing",
    "evidence_candidate_triage": "Evidence candidates needing triage",
    "checklist_evidence_review": "Checklist evidence review needed",
    "applicant_response_review": "Applicant response needs reviewer review",
    "carried_forward_matrix_item": "Carried forward for review",
    "response_package_handoff": "Package ready for reviewer handoff",
}


def build_project_queue_items(
    project: models.Project, metrics: dict, *, now: datetime | None = None
) -> list[dict]:
    """Build reviewer queue items for one project from its computed metrics.

    Emits one queue item per pending-action category that has a positive count.
    Each item references the project workflow page where the reviewer continues
    the action. No full record text, storage key, or path is included.
    """

    now = now or _now()
    bucket = aging_bucket(project_reference_timestamp(project), now=now)
    items: list[dict] = []
    for metric_key, item_type, sub_path in QUEUE_CATEGORY_SPECS:
        count = int(metrics.get(metric_key, 0) or 0)
        if count <= 0:
            continue
        items.append(
            {
                "queue_item_id": f"{project.project_id}:{metric_key}",
                "project_id": project.project_id,
                "project_name": project.project_name,
                "item_type": item_type,
                "label": QUEUE_TYPE_LABELS[item_type],
                "count": count,
                "status": "pending_reviewer_action",
                "age_bucket": bucket,
                "target_path": f"/projects/{project.project_id}/{sub_path}",
            }
        )
    return items
