"""Pydantic schemas for review-support findings.

Findings are review-support issues that need reviewer confirmation. They are not
final engineering conclusions and never carry approval or compliance language.
"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


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
    # Production foundation metadata. finding_origin distinguishes a seeded demo
    # finding from a reviewer-created one. Optional so seeded findings validate.
    source_mode: str = "demo_fixture"
    finding_origin: str = "seeded_demo"
    evidence_status: str | None = None
    reviewer_notes: str | None = None
    applicant_response_summary: str | None = None
    carry_forward_status: str | None = None
    created_by_name: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


class FindingCreate(BaseModel):
    """Request body for a reviewer-created review-support finding.

    Every reviewer finding stays under human review. evidence_status and
    human_review_status are validated against the review-support vocabulary and
    never accept final-decision wording.
    """

    title: str
    category: str = "general"
    risk_level: str = "medium"
    evidence_status: str = "needs_reviewer_confirmation"
    evidence_to_find: str = ""
    reason_it_matters: str = ""
    recommended_human_action: str = ""
    related_documents: list[str] = Field(default_factory=list)
    related_checklist_items: list[str] = Field(default_factory=list)
    reviewer_notes: str | None = None
    human_review_status: str = "needs_reviewer_confirmation"
    created_by_name: str = "Demo Reviewer"
