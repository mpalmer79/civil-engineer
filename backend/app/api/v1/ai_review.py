"""AI Review Assistant API routes.

These endpoints run and read the controlled AI review workflow. All outputs are
draft review-support findings that require human review. No endpoint returns a
final-decision label such as approved, certified, or compliant.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.ai.provider import describe_provider_mode
from app.core.config import get_settings
from app.db.database import get_db
from app.schemas.ai_review import (
    AIDraftFindingRead,
    AIReviewRunRead,
    ProviderMode,
)
from app.services import ai_review_service, project_service

router = APIRouter(tags=["ai-review"])


@router.get("/projects/{project_id}/ai-provider-mode", response_model=ProviderMode)
def get_provider_mode(project_id: str, db: Session = Depends(get_db)) -> ProviderMode:
    if project_service.get_project(db, project_id) is None:
        raise HTTPException(status_code=404, detail="Project not found")
    return describe_provider_mode(get_settings())


@router.post(
    "/projects/{project_id}/ai-review-runs", response_model=AIReviewRunRead
)
def start_ai_review_run(
    project_id: str, db: Session = Depends(get_db)
) -> AIReviewRunRead:
    if project_service.get_project(db, project_id) is None:
        raise HTTPException(status_code=404, detail="Project not found")
    return ai_review_service.start_ai_review_run(db, project_id)


@router.get(
    "/projects/{project_id}/ai-review-runs",
    response_model=list[AIReviewRunRead],
)
def list_ai_review_runs(
    project_id: str, db: Session = Depends(get_db)
) -> list[AIReviewRunRead]:
    if project_service.get_project(db, project_id) is None:
        raise HTTPException(status_code=404, detail="Project not found")
    return ai_review_service.list_ai_review_runs(db, project_id)


@router.get("/ai-review-runs/{review_run_id}", response_model=AIReviewRunRead)
def get_ai_review_run(
    review_run_id: str, db: Session = Depends(get_db)
) -> AIReviewRunRead:
    run = ai_review_service.get_ai_review_run(db, review_run_id)
    if run is None:
        raise HTTPException(status_code=404, detail="AI review run not found")
    return run


@router.get(
    "/ai-review-runs/{review_run_id}/draft-findings",
    response_model=list[AIDraftFindingRead],
)
def list_run_draft_findings(
    review_run_id: str, db: Session = Depends(get_db)
) -> list[AIDraftFindingRead]:
    if ai_review_service.get_ai_review_run(db, review_run_id) is None:
        raise HTTPException(status_code=404, detail="AI review run not found")
    return ai_review_service.list_draft_findings_for_run(db, review_run_id)


@router.get(
    "/projects/{project_id}/draft-findings",
    response_model=list[AIDraftFindingRead],
)
def list_project_draft_findings(
    project_id: str, db: Session = Depends(get_db)
) -> list[AIDraftFindingRead]:
    if project_service.get_project(db, project_id) is None:
        raise HTTPException(status_code=404, detail="Project not found")
    return ai_review_service.list_draft_findings_for_project(db, project_id)


@router.get(
    "/draft-findings/{draft_finding_id}", response_model=AIDraftFindingRead
)
def get_draft_finding(
    draft_finding_id: str, db: Session = Depends(get_db)
) -> AIDraftFindingRead:
    draft = ai_review_service.get_draft_finding(db, draft_finding_id)
    if draft is None:
        raise HTTPException(status_code=404, detail="Draft finding not found")
    return draft
