"""Pydantic schemas for read-only project-wide traceability.

Traceability organizes existing review-support links. It does not determine that
a requirement is satisfied and carries no final-decision wording.
"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class TraceabilitySourceLink(BaseModel):
    type: str
    id: str | None = None


class TraceabilityRow(BaseModel):
    traceability_row_id: str
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


class ProjectTraceabilityResponse(BaseModel):
    project_id: str
    generated_at: datetime
    limitations_note: str
    has_indexed_information: bool
    summary: TraceabilitySummary
    rows: list[TraceabilityRow] = []
