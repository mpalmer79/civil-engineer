"""Pydantic schemas for Phase 7 plan sheet hotspots and the sheet viewer.

Sheet hotspots are seeded review-support annotations over a synthetic plan sheet
preview. They are not extracted CAD geometry or verified plan locations. The
sheet viewer context bundles a sheet with its hotspots and related evidence.
Plan consistency review actions record a reviewer decision on a plan consistency
finding and never use final-decision language.
"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.schemas.cad_metadata import CadMetadataRead
from app.schemas.plan_consistency import PlanConsistencyFindingRead
from app.schemas.plan_reference import PlanReferenceRead
from app.schemas.plan_sheet import PlanSheetRead


class PlanSheetHotspotRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    hotspot_id: str
    project_id: str
    sheet_id: str
    hotspot_type: str
    label: str
    description: str
    x_percent: float
    y_percent: float
    width_percent: float
    height_percent: float
    severity: str
    related_plan_reference_ids: list[str]
    related_cad_metadata_ids: list[str]
    related_plan_finding_ids: list[str]
    related_document_ids: list[str]
    related_checklist_item_ids: list[str]
    review_note: str | None
    requires_human_review: bool
    created_at: datetime


class SheetHotspotSummary(BaseModel):
    """Counts of seeded sheet hotspots for a project."""

    project_id: str
    total_hotspots: int
    sheets_with_hotspots: int
    hotspots_by_type: dict[str, int]
    hotspots_by_severity: dict[str, int]
    hotspots_requiring_human_review: int


class SheetViewerContext(BaseModel):
    """A sheet plus the hotspots and related evidence for the viewer."""

    sheet: PlanSheetRead
    hotspots: list[PlanSheetHotspotRead]
    cad_metadata: list[CadMetadataRead]
    plan_references: list[PlanReferenceRead]
    plan_consistency_findings: list[PlanConsistencyFindingRead]
    preview_note: str


class PlanConsistencyReviewActionCreate(BaseModel):
    """Request body for recording a review action on a plan consistency finding.

    The action must be one of the allowed plan review actions. There is no
    action called approve.
    """

    action: str
    reviewer_name: str
    reviewer_note: str


class PlanConsistencyReviewActionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    review_action_id: str
    plan_finding_id: str
    project_id: str
    reviewer_name: str
    action: str
    reviewer_note: str
    previous_status: str
    new_status: str
    created_at: datetime


class PlanConsistencyReviewActionResult(BaseModel):
    """The recorded action and the updated plan consistency finding."""

    action: PlanConsistencyReviewActionRead
    finding: PlanConsistencyFindingRead
