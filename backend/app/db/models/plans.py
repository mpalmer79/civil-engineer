"""Plans bounded context: plan sheets, CAD-aware metadata, plan references, and plan consistency review."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import JSON, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base
from app.db.models.shared import _utcnow

class PlanSheet(Base):
    """A civil plan sheet record in the Brookside Meadows plan set.

    Phase 6 models the plan sheet index rather than parsing real CAD or PDF
    files. Each record carries sheet metadata (number, title, discipline,
    revision, status) and connects to related documents, checklist items, and
    findings. A sheet status is never a final engineering decision; values such
    as referenced_not_included and needs_reviewer_confirmation keep the work
    under human review.
    """

    __tablename__ = "plan_sheets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    sheet_id: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    project_id: Mapped[str] = mapped_column(
        ForeignKey("projects.project_id"), nullable=False
    )
    sheet_number: Mapped[str] = mapped_column(String, nullable=False)
    sheet_title: Mapped[str] = mapped_column(String, nullable=False)
    discipline: Mapped[str] = mapped_column(String, nullable=False)
    revision: Mapped[str] = mapped_column(String, nullable=False)
    revision_date: Mapped[str | None] = mapped_column(String, nullable=True)
    status: Mapped[str] = mapped_column(String, nullable=False)
    file_name: Mapped[str | None] = mapped_column(String, nullable=True)
    sheet_purpose: Mapped[str] = mapped_column(Text, nullable=False)
    related_documents: Mapped[list] = mapped_column(JSON, default=list)
    related_checklist_items: Mapped[list] = mapped_column(JSON, default=list)
    related_findings: Mapped[list] = mapped_column(JSON, default=list)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=_utcnow
    )

    project: Mapped["Project"] = relationship(back_populates="plan_sheets")


class CadMetadata(Base):
    """CAD-aware metadata for a civil feature referenced in the plan set.

    Phase 6 seeds synthetic CAD-aware metadata rather than extracting it from
    real DWG or DXF files. Each record describes a civil feature (basin, pipe,
    road, lot, utility, and so on), the sheet and layer it relates to, and the
    documents, checklist items, or findings it connects to. This is a future
    ready abstraction for CAD-derived metadata, not verified CAD geometry.
    """

    __tablename__ = "cad_metadata"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    cad_metadata_id: Mapped[str] = mapped_column(
        String, unique=True, nullable=False
    )
    project_id: Mapped[str] = mapped_column(
        ForeignKey("projects.project_id"), nullable=False
    )
    sheet_id: Mapped[str | None] = mapped_column(String, nullable=True)
    source_type: Mapped[str] = mapped_column(String, nullable=False)
    entity_type: Mapped[str] = mapped_column(String, nullable=False)
    entity_label: Mapped[str] = mapped_column(String, nullable=False)
    layer_name: Mapped[str | None] = mapped_column(String, nullable=True)
    discipline: Mapped[str] = mapped_column(String, nullable=False)
    related_document_id: Mapped[str | None] = mapped_column(String, nullable=True)
    related_checklist_item_id: Mapped[str | None] = mapped_column(
        String, nullable=True
    )
    related_finding_id: Mapped[str | None] = mapped_column(String, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=_utcnow
    )


class PlanReference(Base):
    """A reference linking a document, sheet, or civil feature to another.

    Plan references record where the submitted package points from one place to
    another (for example, a report citing a sheet, or an RFI citing a pipe). The
    consistency_status records whether the reference target was located and
    whether labels agree. It is review-support evidence, never a final decision.
    """

    __tablename__ = "plan_references"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    plan_reference_id: Mapped[str] = mapped_column(
        String, unique=True, nullable=False
    )
    project_id: Mapped[str] = mapped_column(
        ForeignKey("projects.project_id"), nullable=False
    )
    source_type: Mapped[str] = mapped_column(String, nullable=False)
    source_id: Mapped[str] = mapped_column(String, nullable=False)
    target_type: Mapped[str] = mapped_column(String, nullable=False)
    target_id: Mapped[str] = mapped_column(String, nullable=False)
    reference_label: Mapped[str] = mapped_column(String, nullable=False)
    reference_context: Mapped[str] = mapped_column(Text, nullable=False)
    consistency_status: Mapped[str] = mapped_column(String, nullable=False)
    review_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=_utcnow
    )


class PlanConsistencyFinding(Base):
    """A plan-sheet-specific review-support finding.

    These findings are produced by evaluating the seeded plan sheets and plan
    references for missing sheets, missing reference targets, conflicting
    labels, and unclear revisions. Like every finding in the system, each one
    requires human review and never carries final approval or certification
    language.
    """

    __tablename__ = "plan_consistency_findings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    plan_finding_id: Mapped[str] = mapped_column(
        String, unique=True, nullable=False
    )
    project_id: Mapped[str] = mapped_column(
        ForeignKey("projects.project_id"), nullable=False
    )
    finding_type: Mapped[str] = mapped_column(String, nullable=False)
    title: Mapped[str] = mapped_column(String, nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    risk_level: Mapped[str] = mapped_column(String, nullable=False)
    status: Mapped[str] = mapped_column(String, nullable=False)
    related_sheet_ids: Mapped[list] = mapped_column(JSON, default=list)
    related_document_ids: Mapped[list] = mapped_column(JSON, default=list)
    related_checklist_items: Mapped[list] = mapped_column(JSON, default=list)
    related_cad_metadata_ids: Mapped[list] = mapped_column(JSON, default=list)
    recommended_human_action: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=_utcnow
    )


class PlanSheetHotspot(Base):
    """A seeded review-support annotation placed over a plan sheet preview.

    Phase 7 adds a reviewer-facing plan sheet viewer. A hotspot is a seeded
    rectangular annotation (percentage coordinates) over a synthetic plan sheet
    preview that points a reviewer at a civil feature, plan reference, or plan
    consistency finding. Hotspots are seeded review-support metadata, not
    extracted CAD geometry or verified plan locations. They never carry final
    approval, certification, or CAD verification language.
    """

    __tablename__ = "plan_sheet_hotspots"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    hotspot_id: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    project_id: Mapped[str] = mapped_column(
        ForeignKey("projects.project_id"), nullable=False
    )
    sheet_id: Mapped[str] = mapped_column(
        ForeignKey("plan_sheets.sheet_id"), nullable=False
    )
    hotspot_type: Mapped[str] = mapped_column(String, nullable=False)
    label: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    x_percent: Mapped[float] = mapped_column(Float, nullable=False)
    y_percent: Mapped[float] = mapped_column(Float, nullable=False)
    width_percent: Mapped[float] = mapped_column(Float, nullable=False)
    height_percent: Mapped[float] = mapped_column(Float, nullable=False)
    severity: Mapped[str] = mapped_column(String, nullable=False)
    related_plan_reference_ids: Mapped[list] = mapped_column(JSON, default=list)
    related_cad_metadata_ids: Mapped[list] = mapped_column(JSON, default=list)
    related_plan_finding_ids: Mapped[list] = mapped_column(JSON, default=list)
    related_document_ids: Mapped[list] = mapped_column(JSON, default=list)
    related_checklist_item_ids: Mapped[list] = mapped_column(JSON, default=list)
    review_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    requires_human_review: Mapped[bool] = mapped_column(default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=_utcnow
    )


class PlanConsistencyReviewAction(Base):
    """A persisted human review action on a plan consistency finding.

    Phase 7 lets a reviewer record an action on a plan consistency finding:
    needs_follow_up, reviewer_confirmed, not_applicable, or
    needs_more_information. There is intentionally no action called approve, and
    no action approves a plan, certifies compliance, verifies CAD, or validates
    a design. Every action keeps the finding a review-support finding under
    human control.
    """

    __tablename__ = "plan_consistency_review_actions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    review_action_id: Mapped[str] = mapped_column(
        String, unique=True, nullable=False
    )
    plan_finding_id: Mapped[str] = mapped_column(
        ForeignKey("plan_consistency_findings.plan_finding_id"), nullable=False
    )
    project_id: Mapped[str] = mapped_column(
        ForeignKey("projects.project_id"), nullable=False
    )
    reviewer_name: Mapped[str] = mapped_column(String, nullable=False)
    action: Mapped[str] = mapped_column(String, nullable=False)
    reviewer_note: Mapped[str] = mapped_column(Text, nullable=False)
    previous_status: Mapped[str] = mapped_column(String, nullable=False)
    new_status: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=_utcnow
    )
