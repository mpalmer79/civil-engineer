"""Pydantic schemas for Phase 13 multi-round resubmittal and revision cycle.

These schemas cover review cycles, resubmittal packages and documents, applicant
responses and mappings, DXF metadata revision comparison, issue carry-forward,
response resolution, and next-cycle preparation. Revision comparison compares
extracted DXF metadata only. Nothing here verifies CAD, validates design,
certifies compliance, or makes a final engineering decision.
"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


# Review cycle.


class ReviewCycleCreate(BaseModel):
    cycle_number: int | None = None
    cycle_name: str | None = None
    source_response_package_id: str | None = None
    source_workflow_board_id: str | None = None
    summary: str | None = None


class ReviewCycleRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    review_cycle_id: str
    project_id: str
    cycle_number: int
    cycle_name: str
    status: str
    started_at: datetime
    completed_at: datetime | None = None
    source_response_package_id: str | None = None
    source_workflow_board_id: str | None = None
    summary: str
    requires_human_review: bool
    created_at: datetime
    updated_at: datetime


class ReviewCycleSummary(BaseModel):
    project_id: str
    cycle_count: int
    active_cycle_id: str | None = None
    active_cycle_number: int | None = None
    statuses: dict[str, int] = Field(default_factory=dict)
    note: str


# Resubmittal package and documents.


class ResubmittalPackageCreate(BaseModel):
    review_cycle_id: str | None = None
    package_name: str
    submitted_by: str = "applicant"
    summary: str | None = None


class ResubmittalPackageStatusUpdate(BaseModel):
    status: str
    reviewer_note: str | None = None


class ResubmittalDocumentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    resubmittal_document_id: str
    project_id: str
    review_cycle_id: str
    resubmittal_package_id: str
    document_type: str
    source_type: str
    source_id: str | None = None
    file_name: str | None = None
    description: str
    status: str
    created_at: datetime


class ResubmittalPackageRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    resubmittal_package_id: str
    project_id: str
    review_cycle_id: str
    package_name: str
    submitted_by: str
    submitted_at: datetime | None = None
    received_at: datetime
    status: str
    summary: str
    reviewer_note: str | None = None
    requires_human_review: bool
    created_at: datetime
    updated_at: datetime


class ResubmittalPackageDetail(ResubmittalPackageRead):
    documents: list[ResubmittalDocumentRead] = Field(default_factory=list)
    applicant_responses: list["ApplicantResponseRead"] = Field(
        default_factory=list
    )
    note: str = ""


# Applicant responses and mappings.


class ApplicantResponseCreate(BaseModel):
    response_text: str
    response_topic: str = "general"
    submitted_by: str = "applicant"
    target_response_item_id: str | None = None
    target_workflow_item_id: str | None = None


class ApplicantResponseRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    applicant_response_id: str
    project_id: str
    review_cycle_id: str
    resubmittal_package_id: str
    response_text: str
    response_topic: str
    submitted_by: str
    target_response_item_id: str | None = None
    target_workflow_item_id: str | None = None
    status: str
    reviewer_note: str | None = None
    requires_human_review: bool
    created_at: datetime
    updated_at: datetime


class ApplicantResponseMappingCreate(BaseModel):
    response_package_item_id: str | None = None
    workflow_item_id: str | None = None
    mapping_confidence: str = "medium"
    mapping_reason: str | None = None


class ApplicantResponseMappingRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    mapping_id: str
    project_id: str
    review_cycle_id: str
    applicant_response_id: str
    response_package_item_id: str | None = None
    workflow_item_id: str | None = None
    response_resolution_record_id: str | None = None
    mapping_confidence: str
    mapping_reason: str
    requires_human_review: bool
    created_at: datetime


class ResponseMappingSummary(BaseModel):
    review_cycle_id: str
    project_id: str
    response_count: int
    mapped_count: int
    unmapped_count: int
    suggested_count: int
    confidence_counts: dict[str, int] = Field(default_factory=dict)
    note: str


# Revision comparison.


class RevisionComparisonCreate(BaseModel):
    previous_parse_run_id: str
    current_parse_run_id: str
    resubmittal_package_id: str | None = None


class RevisionChangeRecordRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    change_record_id: str
    project_id: str
    review_cycle_id: str
    comparison_run_id: str
    change_type: str
    source_category: str
    previous_value: str | None = None
    current_value: str | None = None
    normalized_key: str
    layer_name: str | None = None
    reference_type: str | None = None
    severity: str
    linked_cad_review_finding_id: str | None = None
    linked_workflow_item_id: str | None = None
    reviewer_status: str
    reviewer_note: str | None = None
    requires_human_review: bool
    created_at: datetime


class RevisionComparisonRunRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    comparison_run_id: str
    project_id: str
    review_cycle_id: str
    resubmittal_package_id: str | None = None
    previous_parse_run_id: str
    current_parse_run_id: str
    status: str
    started_at: datetime
    completed_at: datetime | None = None
    compared_layer_count: int
    compared_text_count: int
    added_count: int
    removed_count: int
    changed_count: int
    unchanged_count: int
    warning_count: int
    summary: str
    limitations_note: str
    requires_human_review: bool


class RevisionComparisonSummary(BaseModel):
    comparison_run_id: str
    project_id: str
    review_cycle_id: str
    status: str
    added_count: int
    removed_count: int
    changed_count: int
    unchanged_count: int
    carried_forward_count: int
    changes_by_category: dict[str, int] = Field(default_factory=dict)
    changes_by_type: dict[str, int] = Field(default_factory=dict)
    limitations_note: str
    note: str


# Issue carry-forward.


class IssueCarryForwardCreate(BaseModel):
    source_workflow_item_id: str | None = None
    source_response_item_id: str | None = None
    source_cad_finding_id: str | None = None
    source_revision_change_id: str | None = None
    title: str | None = None
    reason: str
    reviewer_name: str = "reviewer"
    reviewer_note: str | None = None


class IssueCarryForwardRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    carry_forward_id: str
    project_id: str
    review_cycle_id: str
    source_workflow_item_id: str | None = None
    source_response_item_id: str | None = None
    source_cad_finding_id: str | None = None
    source_revision_change_id: str | None = None
    title: str
    reason: str
    carried_forward_status: str
    target_workflow_item_id: str | None = None
    created_at: datetime
    reviewer_name: str
    reviewer_note: str | None = None
    requires_human_review: bool


class CarryForwardResult(BaseModel):
    review_cycle_id: str
    project_id: str
    created_count: int
    skipped_count: int
    carry_forward_ids: list[str] = Field(default_factory=list)
    note: str


class CarryForwardSummary(BaseModel):
    review_cycle_id: str
    project_id: str
    total: int
    statuses: dict[str, int] = Field(default_factory=dict)
    note: str


# Response resolution.


class ResponseResolutionCreate(BaseModel):
    response_package_item_id: str | None = None
    workflow_item_id: str | None = None
    applicant_response_id: str | None = None
    revision_change_record_id: str | None = None
    status: str = "still_open"
    reviewer_note: str | None = None
    reviewer_name: str = "reviewer"


class ResponseResolutionStatusUpdate(BaseModel):
    status: str
    reviewer_note: str | None = None
    reviewer_name: str = "reviewer"


class ResponseResolutionRecordRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    resolution_record_id: str
    project_id: str
    review_cycle_id: str
    response_package_item_id: str | None = None
    workflow_item_id: str | None = None
    applicant_response_id: str | None = None
    revision_change_record_id: str | None = None
    status: str
    reviewer_note: str | None = None
    reviewer_name: str
    created_at: datetime
    updated_at: datetime
    requires_human_review: bool


class ResolutionSummary(BaseModel):
    review_cycle_id: str
    project_id: str
    total: int
    statuses: dict[str, int] = Field(default_factory=dict)
    note: str


# Next-cycle preparation.


class NextCyclePreparationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    next_cycle_preparation_id: str
    project_id: str
    review_cycle_id: str
    status: str
    summary: str
    carried_forward_count: int
    needs_more_information_count: int
    reviewer_checked_count: int
    next_response_package_ready: bool
    created_at: datetime
    updated_at: datetime
    requires_human_review: bool


# Dashboard.


class ReviewCycleDashboard(BaseModel):
    project_id: str
    cycle_count: int
    active_cycle_id: str | None = None
    active_cycle_number: int | None = None
    review_cycles: list[ReviewCycleRead] = Field(default_factory=list)
    resubmittal_count: int
    resubmittal_statuses: dict[str, int] = Field(default_factory=dict)
    applicant_response_count: int
    unmapped_response_count: int
    comparison_run_count: int
    revision_change_count: int
    carry_forward_count: int
    resolution_count: int
    resolution_statuses: dict[str, int] = Field(default_factory=dict)
    open_item_count: int
    next_cycle_ready: bool
    limitations_note: str


ResubmittalPackageDetail.model_rebuild()
