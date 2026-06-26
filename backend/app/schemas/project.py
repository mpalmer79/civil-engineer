"""Pydantic schemas for projects.

ProjectRead and ProjectDetail describe both the seeded Brookside Meadows demo
fixture (source_mode demo_fixture) and real, user-created project records
(source_mode user_created). Project status is review-support only and never a
final engineering outcome.
"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class SiteCondition(BaseModel):
    type: str
    label: str
    description: str


class ProposedImprovement(BaseModel):
    type: str
    label: str
    aliases: list[str]
    description: str


class ProjectRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    project_id: str
    project_name: str
    project_type: str
    location_context: str
    jurisdiction: str
    review_type: str
    review_domain: str
    acreage: float
    disturbed_area: float
    proposed_lots: int
    status: str
    summary: str
    site_conditions: list[SiteCondition]
    proposed_improvements: list[ProposedImprovement]
    known_constraints: list[str]
    # Production foundation metadata. Optional so the seeded demo fixture and
    # existing rows validate without these set.
    source_mode: str = "demo_fixture"
    created_by_name: str | None = None
    created_by_actor_id: str | None = None
    applicant_name: str | None = None
    applicant_organization: str | None = None
    design_engineer_name: str | None = None
    design_firm: str | None = None
    submission_reference: str | None = None
    review_round_current: int = 1
    parcel_ids: list[str] = Field(default_factory=list)
    created_at: datetime | None = None
    updated_at: datetime | None = None


class ProjectDetail(ProjectRead):
    """A project plus aggregate counts of its documents, findings, and events."""

    document_count: int = 0
    finding_count: int = 0
    audit_event_count: int = 0


class ProjectCreate(BaseModel):
    """Request body for creating a real, user-created project record."""

    project_name: str
    project_type: str = "Not specified"
    jurisdiction: str = ""
    review_type: str = "Not specified"
    review_domain: str = "stormwater"
    location_context: str = ""
    acreage: float | None = None
    disturbed_area: float | None = None
    proposed_lots: int | None = None
    summary: str | None = None
    applicant_name: str | None = None
    applicant_organization: str | None = None
    design_engineer_name: str | None = None
    design_firm: str | None = None
    submission_reference: str | None = None
    parcel_ids: list[str] = Field(default_factory=list)
    created_by_name: str = "Demo Reviewer"
