"""Project API routes.

Lists and reads both the seeded Brookside Meadows demo fixture and real,
user-created project records, and creates new user-created project records.
Creating a project is a review-support intake action. It does not approve
plans, certify compliance, verify CAD, validate design, or make any final
engineering decision.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db import models
from app.db.database import get_db
from app.schemas.project import ProjectCreate, ProjectDetail
from app.services import access_control_service, real_intake_service
from app.services.access_control_service import (
    context_for_create,
    get_optional_user,
    require_project_read,
)
from app.services.real_intake_service import IntakeError

router = APIRouter(prefix="/projects", tags=["projects"])


@router.get("", response_model=list[ProjectDetail])
def list_projects(
    source_mode: str | None = Query(
        default=None,
        description="Filter by source mode: all, demo_fixture, or user_created.",
    ),
    user: models.UserAccount | None = Depends(get_optional_user),
    db: Session = Depends(get_db),
) -> list[ProjectDetail]:
    # Unauthenticated callers see public demo projects only when a login is
    # required for real projects; otherwise the demo-mode list keeps the legacy
    # behavior of returning all projects. Signed-in callers see public demo
    # projects plus the projects they have access to. This keeps the Brookside
    # Meadows demo public while protecting real project records under strict mode.
    details = real_intake_service.list_project_details(db, source_mode)
    if user is None:
        if get_settings().AUTH_REQUIRE_LOGIN_FOR_REAL_PROJECTS:
            return [d for d in details if d.get("demo_public")]
        return details
    accessible_ids = {
        p.project_id
        for p in access_control_service.list_user_accessible_projects(db, user)
    }
    return [
        d
        for d in details
        if d.get("demo_public") or d["project_id"] in accessible_ids
    ]


@router.post("", response_model=ProjectDetail, status_code=201)
def create_project(
    body: ProjectCreate,
    user: models.UserAccount | None = Depends(get_optional_user),
    db: Session = Depends(get_db),
) -> ProjectDetail:
    actor = context_for_create(user)
    try:
        return real_intake_service.create_project(
            db,
            project_name=body.project_name,
            project_type=body.project_type,
            jurisdiction=body.jurisdiction,
            review_type=body.review_type,
            review_domain=body.review_domain,
            location_context=body.location_context,
            acreage=body.acreage,
            disturbed_area=body.disturbed_area,
            proposed_lots=body.proposed_lots,
            summary=body.summary,
            applicant_name=body.applicant_name,
            applicant_organization=body.applicant_organization,
            design_engineer_name=body.design_engineer_name,
            design_firm=body.design_firm,
            submission_reference=body.submission_reference,
            parcel_ids=body.parcel_ids,
            created_by_name=actor.display_name,
            created_by_user_id=actor.user_id,
            created_by_email=actor.user_email,
            organization_id=actor.organization_id,
            access_level=actor.access_level,
        )
    except (IntakeError, ValueError) as exc:
        status_code = getattr(exc, "status_code", 422)
        message = getattr(exc, "message", str(exc))
        raise HTTPException(status_code=status_code, detail=message) from exc


@router.get("/{project_id}", response_model=ProjectDetail)
def get_project(
    project_id: str,
    user: models.UserAccount | None = Depends(get_optional_user),
    db: Session = Depends(get_db),
) -> ProjectDetail:
    require_project_read(db, project_id, user)
    detail = real_intake_service.get_project_detail(db, project_id)
    if detail is None:
        raise HTTPException(status_code=404, detail="Project not found")
    return detail
