"""Pydantic schemas for review-support findings.

Findings are review-support issues that need reviewer confirmation. They are not
final engineering conclusions and never carry approval or compliance language.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class FindingRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    finding_id: str
    project_id: str
    planted_issue: str
    title: str
    category: str
    risk_level: str
    expected_status: str
    evidence_to_find: str
    reason_it_matters: str
    recommended_human_action: str
    human_review_status: str
    related_checklist_items: list[str]
    related_documents: list[str]
