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

from app.db.database import get_db
from app.schemas.project import ProjectCreate, ProjectDetail
from app.services import real_intake_service
from app.services.real_intake_service import IntakeError

router = APIRouter(prefix="/projects", tags=["projects"])


@router.get("", response_model=list[ProjectDetail])
def list_projects(
    source_mode: str | None = Query(
        default=None,
        description="Filter by source mode: all, demo_fixture, or user_created.",
    ),
    db: Session = Depends(get_db),
) -> list[ProjectDetail]:
    return real_intake_service.list_project_details(db, source_mode)


@router.post("", response_model=ProjectDetail, status_code=201)
def create_project(
    body: ProjectCreate, db: Session = Depends(get_db)
) -> ProjectDetail:
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
            created_by_name=body.created_by_name,
        )
    except (IntakeError, ValueError) as exc:
        status_code = getattr(exc, "status_code", 422)
        message = getattr(exc, "message", str(exc))
        raise HTTPException(status_code=status_code, detail=message) from exc


@router.get("/{project_id}", response_model=ProjectDetail)
def get_project(project_id: str, db: Session = Depends(get_db)) -> ProjectDetail:
    detail = real_intake_service.get_project_detail(db, project_id)
    if detail is None:
        raise HTTPException(status_code=404, detail="Project not found")
    return detail
