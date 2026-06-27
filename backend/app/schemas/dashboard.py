"""Pydantic schemas for the reviewer dashboard and operational metrics (Sprint 9).

These response models carry operational review-support indicators only. No field
represents approval, certification, compliance, or issue resolution. Request
models validate reviewer-entered priority and assignment metadata and reject
final-decision language at the service layer.
"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class DashboardMetrics(BaseModel):
    """Flat per-project review-support counts. None implies a final outcome."""

    documents_uploaded: int = 0
    documents_needing_indexing: int = 0
    documents_indexed_with_text: int = 0
    documents_extraction_unavailable: int = 0
    findings_needing_reviewer_confirmation: int = 0
    evidence_candidates_needing_triage: int = 0
    checklist_items_missing_evidence: int = 0
    checklist_items_unclear_evidence: int = 0
    applicant_responses_needing_review: int = 0
    resubmittal_rounds_registered: int = 0
    matrix_items_carried_forward: int = 0
    response_packages_draft: int = 0
    response_packages_ready_for_handoff: int = 0
    packages_issued_by_reviewer: int = 0
    pending_reviewer_action_count: int = 0
    has_pending_reviewer_action: bool = False


class DashboardAggregate(BaseModel):
    """Aggregate counts across a set of accessible projects."""

    documents_uploaded: int = 0
    documents_needing_indexing: int = 0
    documents_indexed_with_text: int = 0
    documents_extraction_unavailable: int = 0
    findings_needing_reviewer_confirmation: int = 0
    evidence_candidates_needing_triage: int = 0
    checklist_items_missing_evidence: int = 0
    checklist_items_unclear_evidence: int = 0
    applicant_responses_needing_review: int = 0
    resubmittal_rounds_registered: int = 0
    matrix_items_carried_forward: int = 0
    response_packages_draft: int = 0
    response_packages_ready_for_handoff: int = 0
    packages_issued_by_reviewer: int = 0
    pending_reviewer_action_count: int = 0


class DashboardProjectSummary(BaseModel):
    """A dashboard project card with safe counts and aging indicators."""

    project_id: str
    project_name: str
    status: str
    source_mode: str
    organization_id: str | None = None
    assigned_reviewer_user_id: str | None = None
    assigned_reviewer_name: str | None = None
    review_priority: str | None = None
    review_due_date: datetime | None = None
    last_reviewer_activity_at: datetime | None = None
    age_bucket: str
    due_date_indicators: list[str] = []
    pending_reviewer_action_count: int = 0
    has_pending_reviewer_action: bool = False
    metrics: DashboardMetrics


class ReviewerQueueItem(BaseModel):
    """A single reviewer queue action across accessible projects."""

    queue_item_id: str
    project_id: str
    project_name: str
    item_type: str
    label: str
    count: int
    status: str
    age_bucket: str
    target_path: str


class ReviewerDashboardResponse(BaseModel):
    scope: str
    generated_at: datetime
    user_id: str
    display_name: str
    accessible_project_count: int
    projects_with_pending_action_count: int
    totals: DashboardAggregate
    projects: list[DashboardProjectSummary] = []
    queue: list[ReviewerQueueItem] = []
    access_note: str


class ReviewerQueueResponse(BaseModel):
    scope: str
    generated_at: datetime
    item_count: int
    items: list[ReviewerQueueItem] = []


class OrganizationDashboardResponse(BaseModel):
    scope: str
    generated_at: datetime
    organization_id: str
    organization_name: str
    viewer_role: str
    project_count: int
    projects_with_pending_action_count: int
    status_counts: dict[str, int] = {}
    priority_counts: dict[str, int] = {}
    totals: DashboardAggregate
    projects: list[DashboardProjectSummary] = []
    access_note: str


class OrganizationWorkloadResponse(BaseModel):
    scope: str
    generated_at: datetime
    organization_id: str
    organization_name: str
    project_count: int
    projects_with_pending_action_count: int
    status_counts: dict[str, int] = {}
    priority_counts: dict[str, int] = {}
    totals: DashboardAggregate
    access_note: str


class OrganizationReviewerWorkload(BaseModel):
    assigned_reviewer_user_id: str | None = None
    assigned_reviewer_name: str
    project_count: int
    pending_reviewer_action_count: int
    projects_with_pending_action_count: int


class OrganizationReviewerWorkloadResponse(BaseModel):
    scope: str
    generated_at: datetime
    organization_id: str
    organization_name: str
    viewer_role: str
    reviewers: list[OrganizationReviewerWorkload] = []
    access_note: str


class ProjectWorkloadSummaryResponse(BaseModel):
    scope: str
    generated_at: datetime
    project_id: str
    project_name: str
    status: str
    source_mode: str
    organization_id: str | None = None
    assigned_reviewer_user_id: str | None = None
    assigned_reviewer_name: str | None = None
    review_priority: str | None = None
    review_due_date: datetime | None = None
    last_reviewer_activity_at: datetime | None = None
    age_bucket: str
    due_date_indicators: list[str] = []
    pending_reviewer_action_count: int = 0
    has_pending_reviewer_action: bool = False
    metrics: DashboardMetrics
    queue: list[ReviewerQueueItem] = []
    access_note: str


class ProjectPendingActionsResponse(BaseModel):
    scope: str
    generated_at: datetime
    project_id: str
    project_name: str
    pending_reviewer_action_count: int
    items: list[ReviewerQueueItem] = []
    access_note: str


class ProjectAssignmentUpdate(BaseModel):
    """Request body to assign a reviewer to a project."""

    assigned_reviewer_user_id: str | None = None
    assigned_reviewer_name: str | None = None
    note: str | None = None


class ProjectPriorityUpdate(BaseModel):
    """Request body to update a project's review priority and due date."""

    review_priority: str | None = None
    review_due_date: datetime | None = None
    note: str | None = None
