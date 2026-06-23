"""Pydantic schemas for checklist items."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class ChecklistItemRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    checklist_item_id: str
    project_id: str
    review_domain: str
    category: str
    requirement: str
    expected_evidence: str
    supporting_documents: list[str]
    risk_level: str
    applies_when: str
    expected_status_for_brookside_meadows: str
    planted_issue: str | None = None
