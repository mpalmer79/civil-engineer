"""Evaluation case API routes."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.schemas.evaluation import EvaluationCaseRead
from app.services import evaluation_service, project_service

router = APIRouter(tags=["evaluation"])


@router.get("/evaluation-cases", response_model=list[EvaluationCaseRead])
def list_evaluation_cases(
    db: Session = Depends(get_db),
) -> list[EvaluationCaseRead]:
    return evaluation_service.list_evaluation_cases(db)


@router.get(
    "/projects/{project_id}/evaluation-cases",
    response_model=list[EvaluationCaseRead],
)
def list_project_evaluation_cases(
    project_id: str, db: Session = Depends(get_db)
) -> list[EvaluationCaseRead]:
    if project_service.get_project(db, project_id) is None:
        raise HTTPException(status_code=404, detail="Project not found")
    return evaluation_service.list_evaluation_cases(db, project_id)
