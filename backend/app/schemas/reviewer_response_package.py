"""Pydantic schemas for reviewer response packages and comment letters (Sprint 8).

These represent reviewer-controlled communication artifacts. A response package
and a comment letter draft are review-support outputs. Issuance records a reviewer
communication only. Nothing here approves a project, certifies compliance,
validates design, resolves an issue, or closes an issue. Responses never include
storage keys, raw paths, signed URLs, secrets, or full extracted page text.
"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class ResponsePackageCreate(BaseModel):
    package_title: str | None = None
    package_type: str | None = None
    response_matrix_id: str | None = None
    resubmittal_round_id: str | None = None


class ResponsePackageResponse(BaseModel):
    response_package_id: str
    project_id: str
    response_matrix_id: str | None = None
    resubmittal_round_id: str | None = None
    package_title: str
    package_number: int
    revision_number: int
    status: str
    package_type: str
    source_mode: str
    prepared_by_name: str | None = None
    issued_by_name: str | None = None
    organization_id: str | None = None
    issued_at: datetime | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
    item_count: int = 0
    included_item_count: int = 0


class ResponsePackageItemResponse(BaseModel):
    response_package_item_id: str
    response_package_id: str
    project_id: str
    source_type: str
    source_finding_id: str | None = None
    source_checklist_item_id: str | None = None
    source_matrix_item_id: str | None = None
    source_citation_id: str | None = None
    source_document_id: str | None = None
    item_number: str | None = None
    category: str | None = None
    reviewer_comment_text: str
    applicant_response_summary: str | None = None
    reviewer_follow_up_text: str | None = None
    requested_evidence: str | None = None
    citation_reference: str | None = None
    include_in_letter: bool = True
    sort_order: int = 0
    item_status: str
    created_by_name: str | None = None
    updated_by_name: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


class ResponsePackageDetailResponse(ResponsePackageResponse):
    items: list[ResponsePackageItemResponse] = []


class AddMatrixItemsToPackageRequest(BaseModel):
    matrix_item_ids: list[str]


class AddFindingsToPackageRequest(BaseModel):
    finding_ids: list[str]


class AddChecklistItemsToPackageRequest(BaseModel):
    checklist_item_ids: list[str]


class AddCitationsToPackageRequest(BaseModel):
    citation_ids: list[str]


class ManualPackageItemCreate(BaseModel):
    reviewer_comment_text: str
    category: str | None = None
    requested_evidence: str | None = None


class ResponsePackageItemUpdate(BaseModel):
    reviewer_comment_text: str | None = None
    reviewer_follow_up_text: str | None = None
    requested_evidence: str | None = None
    include_in_letter: bool | None = None
    sort_order: int | None = None
    item_status: str | None = None


class ResponsePackagePreviewItem(BaseModel):
    item_number: str | None = None
    category: str | None = None
    reviewer_comment_text: str
    requested_evidence: str | None = None
    applicant_response_summary: str | None = None
    reviewer_follow_up_text: str | None = None
    citation_reference: str | None = None
    item_status: str


class ResponsePackagePreviewResponse(BaseModel):
    response_package_id: str
    project_id: str
    project_name: str
    package_title: str
    package_type: str
    package_number: int
    revision_number: int
    status: str
    issued_by_name: str | None = None
    issued_at: datetime | None = None
    boundary_statement: str
    item_count: int
    items: list[ResponsePackagePreviewItem] = []


class IssueResponsePackageRequest(BaseModel):
    reviewer_note: str | None = None


class CreatePackageRevisionRequest(BaseModel):
    revision_reason: str | None = None


class CommentLetterDraftCreate(BaseModel):
    recipient_name: str | None = None
    recipient_organization: str | None = None


class CommentLetterDraftResponse(BaseModel):
    comment_letter_draft_id: str
    response_package_id: str
    project_id: str
    title: str
    recipient_name: str | None = None
    recipient_organization: str | None = None
    subject_line: str
    introduction_text: str
    project_summary_text: str | None = None
    review_scope_text: str | None = None
    comment_items_text: str
    resubmittal_summary_text: str | None = None
    closing_text: str
    status: str
    revision_number: int
    boundary_statement: str
    created_by_name: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


class CommentLetterDraftUpdate(BaseModel):
    title: str | None = None
    recipient_name: str | None = None
    recipient_organization: str | None = None
    subject_line: str | None = None
    introduction_text: str | None = None
    project_summary_text: str | None = None
    review_scope_text: str | None = None
    comment_items_text: str | None = None
    resubmittal_summary_text: str | None = None
    closing_text: str | None = None
    status: str | None = None


class CommentLetterPreviewSection(BaseModel):
    heading: str
    body: str


class CommentLetterPreviewResponse(BaseModel):
    comment_letter_draft_id: str
    response_package_id: str
    project_id: str
    title: str
    recipient_name: str | None = None
    recipient_organization: str | None = None
    status: str
    revision_number: int
    boundary_statement: str
    sections: list[CommentLetterPreviewSection] = []
