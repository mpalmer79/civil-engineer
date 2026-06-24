"""Pydantic schemas for the Phase 9 reviewer workflow board.

The workflow board is an operational layer that tracks review-support items
from packet generation through triage, follow-up, and handoff to a human
reviewer. It does not approve plans, certify compliance, stamp drawings, verify
CAD, validate a design, or make final engineering decisions. Every item stays
under human control, and handoff means handing the organized evidence to a
licensed Professional Engineer, not a final decision.
"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class WorkflowItemEvidenceLinkRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    evidence_link_id: str
    item_id: str
    evidence_type: str
    evidence_id: str
    relationship: str
    label: str
    description: str | None = None


class WorkflowActionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    action_id: str
    workflow_item_id: str
    project_id: str
    action_type: str
    previous_status: str
    new_status: str
    reviewer_note: str
    reviewer_name: str
    created_at: datetime


class WorkflowFollowUpRequestRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    follow_up_id: str
    workflow_item_id: str
    project_id: str
    requested_from: str
    request_reason: str
    requested_information: str
    target_date: str | None = None
    status: str
    reviewer_name: str
    created_at: datetime
    updated_at: datetime


class WorkflowItemRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    workflow_item_id: str
    project_id: str
    packet_id: str | None = None
    packet_item_id: str | None = None
    title: str
    description: str
    source_type: str
    source_id: str | None = None
    severity: str
    status: str
    assigned_role: str
    reviewer_note: str | None = None
    target_date: str | None = None
    section_type: str
    evidence_types: list[str] = Field(default_factory=list)
    requires_human_review: bool
    created_at: datetime
    updated_at: datetime


class WorkflowItemDetail(WorkflowItemRead):
    evidence_links: list[WorkflowItemEvidenceLinkRead] = Field(default_factory=list)
    follow_ups: list[WorkflowFollowUpRequestRead] = Field(default_factory=list)
    actions: list[WorkflowActionRead] = Field(default_factory=list)


class WorkflowItemStatusUpdate(BaseModel):
    """Request body for moving a workflow item to a new board status."""

    new_status: str
    reviewer_note: str | None = None
    reviewer_name: str | None = None
    target_date: str | None = None


class WorkflowNoteCreate(BaseModel):
    """Request body for adding a reviewer note to a workflow item."""

    reviewer_note: str
    reviewer_name: str


class WorkflowFollowUpRequestCreate(BaseModel):
    """Request body for opening a follow-up request on a workflow item."""

    requested_from: str
    request_reason: str
    requested_information: str
    reviewer_name: str
    target_date: str | None = None


class WorkflowItemHistory(BaseModel):
    """The full recorded history for a single workflow item."""

    workflow_item_id: str
    project_id: str
    actions: list[WorkflowActionRead] = Field(default_factory=list)
    follow_ups: list[WorkflowFollowUpRequestRead] = Field(default_factory=list)
    note: str


class WorkflowBoardSummary(BaseModel):
    project_id: str
    total_items: int
    items_by_status: dict[str, int]
    items_by_severity: dict[str, int]
    items_by_section_type: dict[str, int]
    items_by_assigned_role: dict[str, int]
    items_requiring_human_review: int
    open_follow_up_count: int
    ready_for_handoff_count: int
    note: str


class ReadyForHandoffSummary(BaseModel):
    project_id: str
    total_items: int
    ready_count: int
    outstanding_follow_up_count: int
    items: list[WorkflowItemRead] = Field(default_factory=list)
    note: str
