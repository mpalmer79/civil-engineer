"""Pydantic schemas for Phase 8 review packets and evidence traceability.

A review packet is a review-support packet draft assembled from seeded data from
prior phases. It organizes evidence for a human reviewer. It does not approve
plans, certify compliance, stamp drawings, verify CAD, validate a design, or
make final engineering decisions.
"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ReviewPacketEvidenceLinkRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    evidence_link_id: str
    packet_id: str
    item_id: str
    evidence_type: str
    evidence_id: str
    relationship: str
    label: str
    description: str | None


class ReviewPacketItemRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    item_id: str
    packet_id: str
    section_id: str
    item_type: str
    title: str
    description: str
    severity: str
    source_type: str
    source_id: str | None
    reviewer_status: str
    reviewer_note: str | None
    requires_human_review: bool
    display_order: int
    evidence_links: list[ReviewPacketEvidenceLinkRead] = Field(default_factory=list)


class ReviewPacketSectionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    section_id: str
    packet_id: str
    title: str
    section_type: str
    display_order: int
    summary: str
    status: str
    requires_human_review: bool
    items: list[ReviewPacketItemRead] = Field(default_factory=list)


class ReviewPacketRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    packet_id: str
    project_id: str
    title: str
    packet_type: str
    status: str
    summary: str
    generated_from_phase: str
    created_by: str
    limitations_note: str
    created_at: datetime
    updated_at: datetime


class ReviewPacketDetail(ReviewPacketRead):
    sections: list[ReviewPacketSectionRead] = Field(default_factory=list)


class ReviewPacketReviewerActionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    action_id: str
    packet_id: str
    item_id: str
    action_type: str
    reviewer_note: str
    previous_status: str
    new_status: str
    reviewer_name: str
    created_at: datetime


class ReviewPacketReviewerActionCreate(BaseModel):
    """Request body for recording a reviewer action on a packet item."""

    action_type: str
    reviewer_note: str
    reviewer_name: str


class ReviewPacketItemStatusUpdate(BaseModel):
    """Request body for updating a packet item status."""

    new_status: str
    reviewer_note: str | None = None
    reviewer_name: str | None = None


class ReviewPacketReviewerActionResult(BaseModel):
    """The recorded action and the updated packet item."""

    action: ReviewPacketReviewerActionRead
    item: ReviewPacketItemRead


class TraceabilityRow(BaseModel):
    """One row in the evidence traceability matrix."""

    section_type: str
    item_id: str
    item_title: str
    item_type: str
    source_type: str
    source_id: str | None
    evidence_type: str
    evidence_id: str
    relationship: str
    label: str


class ReviewPacketTraceability(BaseModel):
    packet_id: str
    project_id: str
    total_rows: int
    rows: list[TraceabilityRow]
    note: str


class ReviewPacketPrintSection(BaseModel):
    title: str
    section_type: str
    summary: str
    items: list[ReviewPacketItemRead]


class ReviewPacketPrintView(BaseModel):
    packet_id: str
    project_id: str
    title: str
    packet_type: str
    status: str
    summary: str
    generated_from_phase: str
    created_by: str
    created_at: datetime
    limitations_note: str
    professional_limitations: str
    draft_notice: str
    sections: list[ReviewPacketPrintSection]


class ReviewPacketSummary(BaseModel):
    packet_id: str
    project_id: str
    status: str
    total_sections: int
    total_items: int
    total_evidence_links: int
    items_by_section_type: dict[str, int]
    items_by_status: dict[str, int]
    items_by_severity: dict[str, int]
    items_requiring_human_review: int
