"""Pydantic schemas for plan consistency findings and check results.

Plan consistency findings are review-support findings that require human review.
They never carry final approval, certification, or compliance language.
"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict


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


class PlanConsistencyCheckResult(BaseModel):
    """Summary returned when a plan consistency check runs."""

    project_id: str
    total_sheets: int
    missing_sheet_count: int
    cad_metadata_records: int
    total_plan_references: int
    inconsistent_references: int
    plan_consistency_findings: int
    conflicting_label_count: int
    missing_referenced_sheet_count: int
    missing_plan_reference_count: int
    unclear_revision_count: int
    requires_human_review_count: int
    findings_requiring_human_review: int
