"""Pydantic schemas for the Phase 10 external review response package.

A response package turns ready-for-handoff workflow items into a structured
draft external response a human reviewer can prepare for an applicant, design
engineer, municipal reviewer, or internal review team. It supports drafting
external communication. It does not send email, approve plans, certify
compliance, stamp drawings, verify CAD, validate the design, or make final
engineering decisions.
"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ResponsePackageEvidenceLinkRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    evidence_link_id: str
    response_package_id: str
    response_item_id: str
    evidence_type: str
    evidence_id: str
    relationship: str
    label: str
    description: str | None = None


class ResponsePackageItemRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    item_id: str
    response_package_id: str
    section_id: str
    workflow_item_id: str | None = None
    packet_item_id: str | None = None
    title: str
    draft_text: str
    reviewer_note: str | None = None
    severity: str
    status: str
    source_type: str
    source_id: str | None = None
    assigned_role: str
    requires_human_review: bool
    display_order: int
    evidence_links: list[ResponsePackageEvidenceLinkRead] = Field(
        default_factory=list
    )


class ResponsePackageSectionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    section_id: str
    response_package_id: str
    title: str
    section_type: str
    display_order: int
    summary: str
    status: str
    requires_human_review: bool
    items: list[ResponsePackageItemRead] = Field(default_factory=list)


class ResponsePackageAttachmentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    attachment_id: str
    response_package_id: str
    label: str
    attachment_type: str
    source_type: str
    source_id: str | None = None
    included: bool
    description: str | None = None


class ResponsePackageRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    response_package_id: str
    project_id: str
    source_packet_id: str | None = None
    title: str
    audience_type: str
    status: str
    summary: str
    draft_intro: str
    draft_closing: str
    limitations_note: str
    created_by: str
    created_at: datetime
    updated_at: datetime


class ResponsePackageDetail(ResponsePackageRead):
    sections: list[ResponsePackageSectionRead] = Field(default_factory=list)
    attachments: list[ResponsePackageAttachmentRead] = Field(default_factory=list)


class ResponsePackageActionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    action_id: str
    response_package_id: str
    response_item_id: str | None = None
    action_type: str
    previous_status: str
    new_status: str
    reviewer_note: str
    reviewer_name: str
    created_at: datetime


class ResponsePackageStatusUpdate(BaseModel):
    """Request body for updating a response package status."""

    new_status: str
    reviewer_note: str | None = None
    reviewer_name: str | None = None


class ResponseItemStatusUpdate(BaseModel):
    """Request body for updating a response item status."""

    new_status: str
    reviewer_note: str | None = None
    reviewer_name: str | None = None


class ResponseItemDraftTextUpdate(BaseModel):
    """Request body for editing a response item draft text."""

    draft_text: str
    reviewer_note: str | None = None
    reviewer_name: str | None = None


class ResponsePackageNoteCreate(BaseModel):
    """Request body for adding a reviewer note to a package or item."""

    reviewer_note: str
    reviewer_name: str
    response_item_id: str | None = None


class ResponsePackagePrintSection(BaseModel):
    title: str
    section_type: str
    summary: str
    items: list[ResponsePackageItemRead]


class ResponsePackageSignoffCheckItem(BaseModel):
    label: str
    detail: str
    confirmed: bool


class ResponsePackagePrintView(BaseModel):
    response_package_id: str
    project_id: str
    title: str
    audience_type: str
    status: str
    summary: str
    draft_intro: str
    draft_closing: str
    created_by: str
    created_at: datetime
    limitations_note: str
    external_communication_boundary: str
    draft_notice: str
    sections: list[ResponsePackagePrintSection]
    attachments: list[ResponsePackageAttachmentRead]
    signoff_checklist: list[ResponsePackageSignoffCheckItem]


class ResponsePackageSummary(BaseModel):
    response_package_id: str
    project_id: str
    status: str
    audience_type: str
    total_sections: int
    total_items: int
    total_attachments: int
    total_evidence_links: int
    items_by_section_type: dict[str, int]
    items_by_status: dict[str, int]
    items_by_severity: dict[str, int]
    items_requiring_human_review: int


class ResponsePackageHistory(BaseModel):
    response_package_id: str
    project_id: str
    actions: list[ResponsePackageActionRead] = Field(default_factory=list)
    note: str
