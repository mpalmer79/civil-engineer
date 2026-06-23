"""Pydantic schemas for homepage hotspots."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class HotspotRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    hotspot_id: str
    project_id: str
    name: str
    category: str
    short_description: str
    civil_purpose: str
    related_checklist_items: list[str]
    related_planted_issues: list[str]
    future_drilldown: str
    position_x_percent: float
    position_y_percent: float
