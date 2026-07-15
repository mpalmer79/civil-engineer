"""Projects bounded context: the project record at the center of review support."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import JSON, DateTime, Float, Integer, String, Text
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

    # Production foundation fields (Sprint 1). All carry safe defaults or are
    # nullable so the seeded Brookside Meadows demo fixture and existing rows
    # keep working without a migration. source_mode distinguishes the seeded
    # demo fixture from a user-created real project record.
    source_mode: Mapped[str] = mapped_column(String, default="demo_fixture")
    created_by_name: Mapped[str | None] = mapped_column(String, nullable=True)
    created_by_actor_id: Mapped[str | None] = mapped_column(String, nullable=True)
    applicant_name: Mapped[str | None] = mapped_column(String, nullable=True)
    applicant_organization: Mapped[str | None] = mapped_column(
        String, nullable=True
    )
    design_engineer_name: Mapped[str | None] = mapped_column(
        String, nullable=True
    )
    design_firm: Mapped[str | None] = mapped_column(String, nullable=True)
    submission_reference: Mapped[str | None] = mapped_column(
        String, nullable=True
    )
    review_round_current: Mapped[int] = mapped_column(Integer, default=1)
    parcel_ids: Mapped[list] = mapped_column(JSON, default=list)
    created_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    updated_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    # Production foundation fields (Sprint 5) for authentication and access
    # control. organization_id and created_by_user_id attribute a real project to
    # an organization and a signed-in user. visibility_mode and demo_public
    # control read access: demo_public projects (the seeded demo) may be read
    # without a login when AUTH_ALLOW_PUBLIC_DEMO is true. All are nullable or
    # defaulted so seeded and Sprint 1 through 4 projects keep working.
    organization_id: Mapped[str | None] = mapped_column(String, nullable=True)
    created_by_user_id: Mapped[str | None] = mapped_column(
        String, nullable=True
    )
    visibility_mode: Mapped[str] = mapped_column(String, default="controlled")
    demo_public: Mapped[bool] = mapped_column(default=False)

    # Production foundation fields (Sprint 9) for reviewer dashboard workload
    # management. These attribute a project to an assigned reviewer and record a
    # workflow sequencing priority and optional review due date. All are nullable
    # so the seeded demo fixture and Sprint 1 through 8 projects keep working
    # without a migration. review_priority is a sequencing label, not an
    # engineering judgment. last_reviewer_activity_at supports safe aging
    # indicators. None of these implies a final engineering decision.
    assigned_reviewer_user_id: Mapped[str | None] = mapped_column(
        String, nullable=True
    )
    assigned_reviewer_name: Mapped[str | None] = mapped_column(
        String, nullable=True
    )
    review_priority: Mapped[str | None] = mapped_column(String, nullable=True)
    review_due_date: Mapped[datetime | None] = mapped_column(
        DateTime, nullable=True
    )
    last_reviewer_activity_at: Mapped[datetime | None] = mapped_column(
        DateTime, nullable=True
    )

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
    plan_sheets: Mapped[list["PlanSheet"]] = relationship(back_populates="project")
