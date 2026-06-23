"""Pydantic schemas for projects."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict


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
