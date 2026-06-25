"""Pydantic schemas for the Phase 14 reviewer command center and dashboard.

These schemas cover the project command center snapshot, health metrics, reviewer
attention items, project timeline events, review readiness checks, reviewer
notes, next steps, module links, and the health summary. The command center
aggregates existing review-support data. It does not approve plans, certify
compliance, verify CAD, validate design, or close or resolve issues.
"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ProjectCommandCenterSnapshotRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    snapshot_id: str
    project_id: str
    current_review_cycle_id: str | None = None
    generated_at: datetime
    overall_status: str
    summary: str
    attention_count: int
    ready_for_handoff_count: int
    carry_forward_count: int
    needs_more_information_count: int
    cad_findings_count: int
    resubmittal_count: int
    open_follow_up_count: int
    response_mapping_gap_count: int
    revision_change_count: int
    requires_human_review: bool


class ProjectHealthMetricRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    metric_id: str
    snapshot_id: str
    project_id: str
    metric_type: str
    label: str
    value: str
    severity: str
    source_module: str
    source_route: str
    requires_human_review: bool


class ReviewerAttentionItemRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    attention_item_id: str
    snapshot_id: str
    project_id: str
    title: str
    description: str
    attention_type: str
    severity: str
    source_module: str
    source_type: str
    source_id: str | None = None
    target_route: str
    recommended_next_step: str
    status: str
    created_at: datetime
    requires_human_review: bool


class AttentionItemStatusUpdate(BaseModel):
    status: str
    reviewer_note: str | None = None
    reviewer_name: str = "reviewer"


class ProjectTimelineEventRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    timeline_event_id: str
    project_id: str
    event_type: str
    event_title: str
    event_description: str
    source_module: str
    source_type: str
    source_id: str | None = None
    event_time: datetime
    target_route: str
    requires_human_review: bool


class ReviewReadinessCheckRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    readiness_check_id: str
    snapshot_id: str
    project_id: str
    check_type: str
    label: str
    description: str
    status: str
    source_module: str
    source_count: int
    blocker_count: int
    recommended_next_step: str
    requires_human_review: bool


class DashboardReviewerNoteCreate(BaseModel):
    note_text: str
    reviewer_name: str = "reviewer"
    snapshot_id: str | None = None
    source_context: str | None = None


class DashboardReviewerNoteRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    note_id: str
    project_id: str
    snapshot_id: str | None = None
    note_text: str
    reviewer_name: str
    created_at: datetime
    source_context: str | None = None
    requires_human_review: bool


class ReviewerNextStep(BaseModel):
    title: str
    detail: str
    severity: str
    target_route: str
    source_module: str


class ReviewerNextSteps(BaseModel):
    project_id: str
    snapshot_id: str | None = None
    steps: list[ReviewerNextStep] = Field(default_factory=list)
    note: str


class ProjectModuleLink(BaseModel):
    module: str
    label: str
    route: str
    description: str
    count: int
    severity: str


class ProjectModuleLinks(BaseModel):
    project_id: str
    links: list[ProjectModuleLink] = Field(default_factory=list)
    note: str


class ProjectHealthSummary(BaseModel):
    project_id: str
    snapshot_id: str | None = None
    overall_status: str
    current_review_cycle_id: str | None = None
    attention_count: int
    ready_for_handoff_count: int
    carry_forward_count: int
    needs_more_information_count: int
    cad_findings_count: int
    resubmittal_count: int
    open_follow_up_count: int
    response_mapping_gap_count: int
    revision_change_count: int
    readiness_ready_count: int
    summary: str
    limitations_note: str


class ProjectCommandCenterPayload(BaseModel):
    snapshot: ProjectCommandCenterSnapshotRead
    health_metrics: list[ProjectHealthMetricRead] = Field(default_factory=list)
    attention_items: list[ReviewerAttentionItemRead] = Field(default_factory=list)
    timeline: list[ProjectTimelineEventRead] = Field(default_factory=list)
    readiness_checks: list[ReviewReadinessCheckRead] = Field(default_factory=list)
    next_steps: ReviewerNextSteps
    module_links: ProjectModuleLinks
    reviewer_notes: list[DashboardReviewerNoteRead] = Field(default_factory=list)
    limitations_note: str
