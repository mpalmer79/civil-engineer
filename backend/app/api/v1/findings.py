"""Finding API routes."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.schemas.finding import FindingRead
from app.services import finding_service, project_service

router = APIRouter(tags=["findings"])


@router.get(
    "/projects/{project_id}/findings", response_model=list[FindingRead]
)
def list_findings(
    project_id: str, db: Session = Depends(get_db)
) -> list[FindingRead]:
    if project_service.get_project(db, project_id) is None:
        raise HTTPException(status_code=404, detail="Project not found")
    return finding_service.list_findings(db, project_id)


@router.get("/findings/{finding_id}", response_model=FindingRead)
def get_finding(finding_id: str, db: Session = Depends(get_db)) -> FindingRead:
    finding = finding_service.get_finding(db, finding_id)
    if finding is None:
        raise HTTPException(status_code=404, detail="Finding not found")
    return finding
