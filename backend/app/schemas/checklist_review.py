"""Pydantic schemas for checklist-driven review and rule packs (Sprint 4).

A rule pack is a reusable review-support template, not a legal ordinance and not
a compliance standard. Checklist status is review-support only. None of these
schemas represents a final engineering decision, approval, certification, or
compliance state.
"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class RulePackItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    rule_pack_item_id: str
    rule_pack_id: str
    item_code: str
    category: str
    requirement_text: str
    expected_evidence: str
    applicability_note: str | None = None
    risk_level: str
    review_domain: str
    reference_label: str | None = None
    sort_order: int = 0
    is_active: bool = True


class RulePackResponse(BaseModel):
    rule_pack_id: str
    name: str
    jurisdiction_name: str
    review_domain: str
    description: str | None = None
    version_label: str
    source_mode: str
    is_active: bool = True
    created_by_name: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
    item_count: int = 0


class RulePackDetailResponse(RulePackResponse):
    items: list[RulePackItemResponse] = []


class ProjectChecklistCreateFromRulePack(BaseModel):
    rule_pack_id: str
    name: str | None = None


class ProjectChecklistResponse(BaseModel):
    project_checklist_id: str
    project_id: str
    rule_pack_id: str | None = None
    name: str
    status: str
    source_mode: str
    created_by_name: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
    item_count: int = 0
    evidence_status_summary: dict = {}
    review_status_summary: dict = {}


class ProjectChecklistItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    project_checklist_item_id: str
    project_checklist_id: str
    project_id: str
    rule_pack_item_id: str | None = None
    checklist_item_id: str | None = None
    item_code: str
    category: str
    requirement_text: str
    expected_evidence: str
    applicability_status: str
    evidence_status: str
    review_status: str
    risk_level: str
    reviewer_note: str | None = None
    related_finding_id: str | None = None
    sort_order: int = 0
    reviewed_by_name: str | None = None
    reviewed_at: datetime | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


class ProjectChecklistDetailResponse(ProjectChecklistResponse):
    items: list[ProjectChecklistItemResponse] = []


class ProjectChecklistItemUpdate(BaseModel):
    applicability_status: str | None = None
    evidence_status: str | None = None
    review_status: str | None = None
    reviewer_note: str | None = None


class ChecklistEvidenceSearchRequest(BaseModel):
    query_text: str | None = None
    limit: int = 10


class ChecklistEvidenceLinkCreate(BaseModel):
    document_id: str
    document_page_id: str | None = None
    page_number: int | None = None
    evidence_citation_id: str | None = None
    evidence_candidate_id: str | None = None
    quoted_excerpt: str | None = None
    reviewer_note: str | None = None
    link_status: str = "reviewer_selected"


class ChecklistEvidenceLinkResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    checklist_evidence_link_id: str
    project_id: str
    project_checklist_item_id: str
    document_id: str
    document_page_id: str | None = None
    page_number: int | None = None
    evidence_citation_id: str | None = None
    evidence_candidate_id: str | None = None
    quoted_excerpt: str | None = None
    reviewer_note: str | None = None
    link_status: str
    created_by_name: str | None = None
    created_at: datetime | None = None


class ChecklistDraftFindingCreate(BaseModel):
    """Reviewer-confirmed content for a draft finding from a checklist item.

    Values may be prefilled from the checklist item, but the reviewer can edit
    them. The risk level is reviewer-entered, never a system conclusion.
    """

    title: str | None = None
    category: str | None = None
    risk_level: str | None = None
    evidence_status: str | None = None
    evidence_to_find: str | None = None
    reason_it_matters: str | None = None
    recommended_human_action: str | None = None
    reviewer_note: str | None = None
    human_review_status: str | None = None
    document_id: str | None = None
    document_page_id: str | None = None
    page_number: int | None = None
    citation_excerpt: str | None = None


class FindingSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    finding_id: str
    project_id: str
    title: str
    category: str
    risk_level: str
    evidence_status: str | None = None
    human_review_status: str
    finding_origin: str
    source_mode: str
    related_checklist_items: list[str] = Field(default_factory=list)
    created_by_name: str | None = None


class CitationSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    evidence_citation_id: str
    project_id: str
    finding_id: str
    document_id: str
    document_page_id: str | None = None
    page_number: int | None = None
    citation_type: str
    citation_status: str
    citation_context: str = "finding_citation"


class ChecklistDraftFindingResponse(BaseModel):
    finding: FindingSummary
    citation: CitationSummary | None = None
    checklist_item: ProjectChecklistItemResponse
