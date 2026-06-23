"""SQLAlchemy models reflecting the Phase 0 domain model.

Phase 2 keeps the schema clean and migration ready. JSON columns are used for
arrays and nested values such as site conditions, supporting documents, and
seeded evaluation results. These are easy to normalize into separate tables in
a later phase if needed.
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import JSON, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base


class Project(Base):
    __tablename__ = "projects"

    project_id: Mapped[str] = mapped_column(String, primary_key=True)
    project_name: Mapped[str] = mapped_column(String, nullable=False)
    project_type: Mapped[str] = mapped_column(String, nullable=False)
    location_context: Mapped[str] = mapped_column(String, nullable=False)
    jurisdiction: Mapped[str] = mapped_column(String, nullable=False)
    review_type: Mapped[str] = mapped_column(String, nullable=False)
    review_domain: Mapped[str] = mapped_column(String, nullable=False)
    acreage: Mapped[float] = mapped_column(Float, nullable=False)
    disturbed_area: Mapped[float] = mapped_column(Float, nullable=False)
    proposed_lots: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(String, nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    site_conditions: Mapped[list] = mapped_column(JSON, default=list)
    proposed_improvements: Mapped[list] = mapped_column(JSON, default=list)
    known_constraints: Mapped[list] = mapped_column(JSON, default=list)

    documents: Mapped[list["Document"]] = relationship(back_populates="project")
    checklist_items: Mapped[list["ChecklistItem"]] = relationship(
        back_populates="project"
    )
    findings: Mapped[list["Finding"]] = relationship(back_populates="project")
    audit_events: Mapped[list["AuditEvent"]] = relationship(back_populates="project")
    evaluation_cases: Mapped[list["EvaluationCase"]] = relationship(
        back_populates="project"
    )
    hotspots: Mapped[list["Hotspot"]] = relationship(back_populates="project")


class Document(Base):
    __tablename__ = "documents"

    document_id: Mapped[str] = mapped_column(String, primary_key=True)
    project_id: Mapped[str] = mapped_column(
        ForeignKey("projects.project_id"), nullable=False
    )
    file_name: Mapped[str] = mapped_column(String, nullable=False)
    document_type: Mapped[str] = mapped_column(String, nullable=False)
    status: Mapped[str] = mapped_column(String, nullable=False)
    purpose: Mapped[str] = mapped_column(Text, nullable=False)
    expected_key_information: Mapped[str] = mapped_column(Text, nullable=False)
    intentionally_missing_or_conflicting_information: Mapped[str | None] = (
        mapped_column(Text, nullable=True)
    )

    project: Mapped["Project"] = relationship(back_populates="documents")


class ChecklistItem(Base):
    __tablename__ = "checklist_items"

    checklist_item_id: Mapped[str] = mapped_column(String, primary_key=True)
    project_id: Mapped[str] = mapped_column(
        ForeignKey("projects.project_id"), nullable=False
    )
    review_domain: Mapped[str] = mapped_column(String, nullable=False)
    category: Mapped[str] = mapped_column(String, nullable=False)
    requirement: Mapped[str] = mapped_column(Text, nullable=False)
    expected_evidence: Mapped[str] = mapped_column(Text, nullable=False)
    supporting_documents: Mapped[list] = mapped_column(JSON, default=list)
    risk_level: Mapped[str] = mapped_column(String, nullable=False)
    applies_when: Mapped[str] = mapped_column(String, nullable=False)
    expected_status_for_brookside_meadows: Mapped[str] = mapped_column(
        String, nullable=False
    )
    planted_issue: Mapped[str | None] = mapped_column(String, nullable=True)

    project: Mapped["Project"] = relationship(back_populates="checklist_items")


class Finding(Base):
    __tablename__ = "findings"

    finding_id: Mapped[str] = mapped_column(String, primary_key=True)
    project_id: Mapped[str] = mapped_column(
        ForeignKey("projects.project_id"), nullable=False
    )
    planted_issue: Mapped[str] = mapped_column(String, nullable=False)
    title: Mapped[str] = mapped_column(String, nullable=False)
    category: Mapped[str] = mapped_column(String, nullable=False)
    risk_level: Mapped[str] = mapped_column(String, nullable=False)
    expected_status: Mapped[str] = mapped_column(String, nullable=False)
    evidence_to_find: Mapped[str] = mapped_column(Text, nullable=False)
    reason_it_matters: Mapped[str] = mapped_column(Text, nullable=False)
    recommended_human_action: Mapped[str] = mapped_column(Text, nullable=False)
    human_review_status: Mapped[str] = mapped_column(String, nullable=False)
    related_checklist_items: Mapped[list] = mapped_column(JSON, default=list)
    related_documents: Mapped[list] = mapped_column(JSON, default=list)

    project: Mapped["Project"] = relationship(back_populates="findings")


class AuditEvent(Base):
    __tablename__ = "audit_events"

    audit_event_id: Mapped[str] = mapped_column(String, primary_key=True)
    project_id: Mapped[str] = mapped_column(
        ForeignKey("projects.project_id"), nullable=False
    )
    event_type: Mapped[str] = mapped_column(String, nullable=False)
    actor_type: Mapped[str] = mapped_column(String, nullable=False)
    related_entity_type: Mapped[str] = mapped_column(String, nullable=False)
    related_entity_id: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    timestamp: Mapped[datetime] = mapped_column(DateTime, nullable=False)

    project: Mapped["Project"] = relationship(back_populates="audit_events")


class EvaluationCase(Base):
    __tablename__ = "evaluation_cases"

    eval_case_id: Mapped[str] = mapped_column(String, primary_key=True)
    project_id: Mapped[str] = mapped_column(
        ForeignKey("projects.project_id"), nullable=False
    )
    name: Mapped[str] = mapped_column(String, nullable=False)
    input_documents: Mapped[list] = mapped_column(JSON, default=list)
    expected_findings: Mapped[list] = mapped_column(JSON, default=list)
    expected_risk_level: Mapped[str] = mapped_column(String, nullable=False)
    evaluation_metric: Mapped[str] = mapped_column(String, nullable=False)
    seeded_result: Mapped[dict] = mapped_column(JSON, default=dict)

    project: Mapped["Project"] = relationship(back_populates="evaluation_cases")


class Hotspot(Base):
    __tablename__ = "hotspots"

    hotspot_id: Mapped[str] = mapped_column(String, primary_key=True)
    project_id: Mapped[str] = mapped_column(
        ForeignKey("projects.project_id"), nullable=False
    )
    name: Mapped[str] = mapped_column(String, nullable=False)
    category: Mapped[str] = mapped_column(String, nullable=False)
    short_description: Mapped[str] = mapped_column(Text, nullable=False)
    civil_purpose: Mapped[str] = mapped_column(Text, nullable=False)
    related_checklist_items: Mapped[list] = mapped_column(JSON, default=list)
    related_planted_issues: Mapped[list] = mapped_column(JSON, default=list)
    future_drilldown: Mapped[str] = mapped_column(Text, nullable=False)
    position_x_percent: Mapped[float] = mapped_column(Float, nullable=False)
    position_y_percent: Mapped[float] = mapped_column(Float, nullable=False)

    project: Mapped["Project"] = relationship(back_populates="hotspots")
