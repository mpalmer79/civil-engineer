"""Pydantic schemas for the applicant response matrix and resubmittals (Sprint 7).

These represent reviewer-controlled response tracking across resubmittal rounds.
An applicant response is recorded for reviewer review, never as proof and never as
a final outcome. Carry-forward means continued review, not resolution. Nothing
here implies approval, certification, compliance, or that an issue is resolved or
closed. Responses never include storage keys, raw paths, secrets, or full
extracted page text.
"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ResponseMatrixCreate(BaseModel):
    name: str | None = None


class ResponseMatrixResponse(BaseModel):
    response_matrix_id: str
    project_id: str
    name: str
    current_round_number: int
    status: str
    source_mode: str
    organization_id: str | None = None
    created_by_name: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
    item_count: int = 0
    applicant_response_summary: dict = {}
    reviewer_follow_up_summary: dict = {}
    carry_forward_summary: dict = {}


class ResponseMatrixItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    response_matrix_item_id: str
    response_matrix_id: str
    project_id: str
    source_finding_id: str | None = None
    source_checklist_item_id: str | None = None
    source_citation_id: str | None = None
    item_number: str | None = None
    category: str
    reviewer_comment_draft: str
    requested_evidence: str | None = None
    applicant_response_text: str | None = None
    applicant_response_status: str
    reviewer_follow_up_status: str
    carry_forward_status: str
    current_round_number: int
    carried_from_round_number: int | None = None
    carried_to_round_number: int | None = None
    related_document_ids: list[str] = []
    related_citation_ids: list[str] = []
    reviewer_note: str | None = None
    created_by_name: str | None = None
    updated_by_name: str | None = None
    sort_order: int = 0
    created_at: datetime | None = None
    updated_at: datetime | None = None


class ResponseMatrixDetailResponse(ResponseMatrixResponse):
    items: list[ResponseMatrixItemResponse] = []


class ResponseMatrixItemCreateFromFinding(BaseModel):
    reviewer_comment_draft: str | None = None
    category: str | None = None
    requested_evidence: str | None = None


class ResponseMatrixItemCreateFromChecklist(BaseModel):
    reviewer_comment_draft: str | None = None
    category: str | None = None
    requested_evidence: str | None = None


class ResponseMatrixItemUpdate(BaseModel):
    reviewer_comment_draft: str | None = None
    requested_evidence: str | None = None
    reviewer_note: str | None = None
    applicant_response_status: str | None = None
    reviewer_follow_up_status: str | None = None


class ApplicantResponseRecord(BaseModel):
    applicant_response_text: str
    applicant_response_status: str | None = None


class MatrixItemDocumentLinkCreate(BaseModel):
    link_type: str = "applicant_response_document"
    resubmittal_round_id: str | None = None
    reviewer_note: str | None = None


class MatrixItemDocumentLinkResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    matrix_item_document_link_id: str
    project_id: str
    response_matrix_item_id: str
    document_id: str
    resubmittal_round_id: str | None = None
    link_type: str
    reviewer_note: str | None = None
    created_by_name: str | None = None
    created_at: datetime | None = None


class CarryForwardMatrixItemRequest(BaseModel):
    carry_forward_status: str | None = None
    carried_to_round_number: int | None = None
    reviewer_note: str | None = None


class ResubmittalRoundCreate(BaseModel):
    round_label: str | None = None
    round_number: int | None = None
    submitted_by_name: str | None = None
    submitted_by_organization: str | None = None
    response_matrix_id: str | None = None
    summary: str | None = None
    status: str | None = None


class ResubmittalRoundResponse(BaseModel):
    resubmittal_round_id: str
    project_id: str
    response_matrix_id: str | None = None
    round_number: int
    round_label: str
    received_at: datetime | None = None
    submitted_by_name: str | None = None
    submitted_by_organization: str | None = None
    status: str
    summary: str | None = None
    document_ids: list[str] = []
    carried_forward_item_ids: list[str] = []
    document_count: int = 0
    carried_forward_item_count: int = 0
    created_by_name: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


class ResubmittalDocumentLinkRequest(BaseModel):
    reviewer_note: str | None = None


class CarryForwardItemsToRoundRequest(BaseModel):
    matrix_item_ids: list[str] = []
    carry_forward_status: str | None = None


class ResubmittalRoundSummaryResponse(BaseModel):
    resubmittal_round_id: str
    project_id: str
    round_number: int
    status: str
    document_count: int = 0
    carried_forward_item_count: int = 0
    matrix_item_count: int = 0
    applicant_response_summary: dict = {}
    carry_forward_summary: dict = {}
