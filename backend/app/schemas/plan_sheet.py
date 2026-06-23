"""Pydantic schemas for plan sheets.

A plan sheet record organizes plan set metadata for review. Its status describes
inclusion in the package (present, referenced_not_included, and so on), never a
final engineering decision about the design.
"""

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
    revision: str
    revision_date: str | None
    status: str
    file_name: str | None
    sheet_purpose: str
    related_documents: list[str]
    related_checklist_items: list[str]
    related_findings: list[str]
    created_at: datetime


class PlanSheetSummary(BaseModel):
    """Summary of the plan sheet index for a project."""

    project_id: str
    total_sheets: int
    present_sheets: int
    missing_or_referenced_not_included: int
    needs_reviewer_confirmation: int
    sheets_with_related_findings: int
    cad_metadata_records: int
    sheets_by_discipline: dict[str, int]
    missing_sheet_ids: list[str]
