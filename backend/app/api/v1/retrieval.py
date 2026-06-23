"""Retrieval and source evidence API routes."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.schemas.evidence import FindingSourceRead, RetrievalResult
from app.services import (
    checklist_service,
    finding_service,
    project_service,
    retrieval_service,
)

router = APIRouter(tags=["retrieval"])


@router.get("/projects/{project_id}/search", response_model=list[RetrievalResult])
def search_project(
    project_id: str,
    query: str = Query(..., min_length=1, description="Keyword search text"),
    document_type: str | None = Query(default=None),
    limit: int = Query(default=10, ge=1, le=50),
    db: Session = Depends(get_db),
) -> list[RetrievalResult]:
    if project_service.get_project(db, project_id) is None:
        raise HTTPException(status_code=404, detail="Project not found")
    return retrieval_service.search(
        db, project_id, query, document_type=document_type, limit=limit
    )


@router.get(
    "/projects/{project_id}/checklist/{checklist_item_id}/evidence",
    response_model=list[RetrievalResult],
)
def checklist_item_evidence(
    project_id: str,
    checklist_item_id: str,
    db: Session = Depends(get_db),
) -> list[RetrievalResult]:
    if project_service.get_project(db, project_id) is None:
        raise HTTPException(status_code=404, detail="Project not found")
    if checklist_service.get_checklist_item(db, checklist_item_id) is None:
        raise HTTPException(status_code=404, detail="Checklist item not found")
    return retrieval_service.evidence_for_checklist_item(
        db, project_id, checklist_item_id
    )


@router.get(
    "/projects/{project_id}/findings/{finding_id}/evidence",
    response_model=list[RetrievalResult],
)
def finding_evidence(
    project_id: str,
    finding_id: str,
    db: Session = Depends(get_db),
) -> list[RetrievalResult]:
    if project_service.get_project(db, project_id) is None:
        raise HTTPException(status_code=404, detail="Project not found")
    if finding_service.get_finding(db, finding_id) is None:
        raise HTTPException(status_code=404, detail="Finding not found")
    return retrieval_service.evidence_for_finding(db, finding_id)


@router.get(
    "/findings/{finding_id}/sources", response_model=list[FindingSourceRead]
)
def finding_sources(
    finding_id: str, db: Session = Depends(get_db)
) -> list[FindingSourceRead]:
    if finding_service.get_finding(db, finding_id) is None:
        raise HTTPException(status_code=404, detail="Finding not found")
    return retrieval_service.list_finding_sources(db, finding_id)
