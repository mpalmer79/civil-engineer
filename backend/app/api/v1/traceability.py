"""Read-only project-wide traceability API route (Phase 4A).

GET /projects/{project_id}/traceability aggregates existing review-support links
between checklist items, evidence, findings, workflow items, and review packets.
It is read-only: it mutates nothing, runs no analysis engine, and makes no final
engineering decision.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.schemas.traceability import ProjectTraceabilityResponse
from app.services import traceability_service

router = APIRouter(tags=["traceability"])


@router.get(
    "/projects/{project_id}/traceability",
    response_model=ProjectTraceabilityResponse,
)
def get_project_traceability(
    project_id: str, db: Session = Depends(get_db)
) -> ProjectTraceabilityResponse:
    result = traceability_service.build_project_traceability(db, project_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Project not found")
    return ProjectTraceabilityResponse.model_validate(result)
