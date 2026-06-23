"""Pydantic schemas for plan sheets, CAD-aware metadata, plan references, and
plan consistency findings (Phase 6)."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class PlanSheetRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    sheet_id: str
    project_id: str
    sheet_number: str
    sheet_title: str
    discipline: str
    revision: str | None = None
    revision_date: str | None = None
    status: str
    file_name: str | None = None
    sheet_purpose: str
    related_documents: list[str]
    related_checklist_items: list[str]
    related_findings: list[str]
    created_at: datetime


class PlanSheetSummary(BaseModel):
    project_id: str
    total_sheets: int
    present_sheets: int
    missing_or_referenced_not_included_sheets: int
    sheets_with_related_findings: int
    cad_metadata_records: int
    disciplines: dict[str, int]
    missing_sheet_numbers: list[str]


class CADMetadataRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    cad_metadata_id: str
    project_id: str
    sheet_id: str | None = None
    source_type: str
    entity_type: str
    entity_label: str
    layer_name: str | None = None
    discipline: str | None = None
    related_document_id: str | None = None
    related_checklist_item_id: str | None = None
    related_finding_id: str | None = None
    notes: str | None = None
    created_at: datetime


class PlanReferenceRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    plan_reference_id: str
    project_id: str
    source_type: str
    source_id: str
    target_type: str
    target_id: str
    reference_label: str
    reference_context: str | None = None
    consistency_status: str
    review_note: str | None = None
    created_at: datetime


class PlanConsistencyFindingRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    plan_finding_id: str
    project_id: str
    finding_type: str
    title: str
    summary: str
    risk_level: str
    status: str
    related_sheet_ids: list[str]
    related_document_ids: list[str]
    related_checklist_items: list[str]
    related_cad_metadata_ids: list[str]
    recommended_human_action: str
    created_at: datetime


class PlanConsistencySummary(BaseModel):
    project_id: str
    total_findings: int
    missing_sheet_count: int
    conflicting_label_count: int
    cad_metadata_records: int
    plan_references_requiring_human_review: int
    findings_by_type: dict[str, int]
