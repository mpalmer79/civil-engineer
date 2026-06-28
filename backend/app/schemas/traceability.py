"""Pydantic schemas for read-only project-wide traceability.

Traceability organizes existing review-support links. It does not determine that
a requirement is satisfied and carries no final-decision wording.
"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class TraceabilitySourceLink(BaseModel):
    type: str
    id: str | None = None


class TraceabilityPacketContext(BaseModel):
    """Inline review packet context for a traceability row.

    It records that a row is included in a review packet for human review. It does
    not state the requirement is satisfied or approved.
    """

    review_packet_id: str
    review_packet_title: str | None = None
    review_packet_item_id: str
    review_packet_section_id: str | None = None
    review_packet_section_title: str | None = None
    packet_item_status: str | None = None
    packet_item_source: str | None = None
    packet_traceability_relationship: str | None = None
    packet_source_link: TraceabilitySourceLink | None = None


class TraceabilityLatestReviewAction(BaseModel):
    """The most recent reviewer review action recorded on a traceability row."""

    action_id: str
    action_type: str
    reviewer_note: str | None = None
    created_by: str
    created_at: datetime


class TraceabilityRow(BaseModel):
    traceability_row_id: str
    traceability_row_key: str
    checklist_item_id: str | None = None
    checklist_title: str | None = None
    checklist_requirement: str | None = None
    checklist_status: str | None = None
    evidence_candidate_id: str | None = None
    evidence_citation_id: str | None = None
    document_id: str | None = None
    document_name: str | None = None
    document_page_id: str | None = None
    page_number: int | None = None
    citation_excerpt: str | None = None
    finding_id: str | None = None
    finding_title: str | None = None
    finding_status: str | None = None
    workflow_item_id: str | None = None
    workflow_item_title: str | None = None
    workflow_status: str | None = None
    cad_finding_id: str | None = None
    plan_finding_id: str | None = None
    plan_sheet_id: str | None = None
    review_packet_id: str | None = None
    review_packet_item_id: str | None = None
    relationship_type: str
    relationship_source: str
    reviewer_action_needed: bool
    source_links: list[TraceabilitySourceLink] = []
    packet_contexts: list[TraceabilityPacketContext] = []
    packet_context_count: int = 0
    latest_review_action: TraceabilityLatestReviewAction | None = None
    notes: str | None = None


class TraceabilitySummary(BaseModel):
    total_checklist_items: int
    checklist_items_with_linked_evidence: int
    checklist_items_without_linked_evidence: int
    total_evidence_citations: int
    total_evidence_candidates: int
    total_findings: int
    total_workflow_items: int
    total_packet_items: int
    total_traceability_rows: int
    rows_requiring_reviewer_confirmation: int


class TraceabilityHandoffReadiness(BaseModel):
    """Read-only handoff readiness signals. Not a final engineering decision."""

    total_traceability_rows: int
    rows_with_linked_evidence: int
    rows_without_linked_evidence: int
    rows_with_reviewer_action: int
    rows_needing_more_information: int
    rows_follow_up_needed: int
    rows_not_in_packet: int
    packet_context_count: int
    ready_for_reviewer_handoff_count: int
    note: str


class ProjectTraceabilityResponse(BaseModel):
    project_id: str
    generated_at: datetime
    limitations_note: str
    has_indexed_information: bool
    summary: TraceabilitySummary
    handoff_readiness: TraceabilityHandoffReadiness
    rows: list[TraceabilityRow] = []


class TraceabilityReviewActionCreate(BaseModel):
    """Request body for recording a reviewer review action on a traceability row.

    The component IDs identify the row the action applies to and are stored for
    transparency. action_type must be a review-support action; there is no action
    that approves, certifies, verifies, validates, or marks a requirement
    satisfied.
    """

    action_type: str
    reviewer_note: str | None = None
    created_by: str | None = None
    checklist_item_id: str | None = None
    evidence_citation_id: str | None = None
    evidence_candidate_id: str | None = None
    finding_id: str | None = None
    workflow_item_id: str | None = None
    review_packet_item_id: str | None = None
    relationship_type: str | None = None


class TraceabilityReviewActionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    action_id: str
    project_id: str
    traceability_row_key: str
    action_type: str
    reviewer_note: str | None = None
    created_by: str
    checklist_item_id: str | None = None
    evidence_citation_id: str | None = None
    evidence_candidate_id: str | None = None
    finding_id: str | None = None
    workflow_item_id: str | None = None
    review_packet_item_id: str | None = None
    relationship_type: str | None = None
    created_at: datetime


class TraceabilityReviewActionHistory(BaseModel):
    project_id: str
    traceability_row_key: str
    total_actions: int
    actions: list[TraceabilityReviewActionRead] = []
    note: str
