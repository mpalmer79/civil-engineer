"""Evaluation scoring API routes.

These endpoints run and read heuristic evaluation scoring of AI review runs
against the seeded expected findings. Evaluation is a quality signal for human
reviewers. It does not certify the AI or declare the package compliant.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.schemas.evaluation_scoring import (
    AIEvaluationResultDetail,
    AIEvaluationResultRead,
)
from app.services import (
    ai_review_service,
    evaluation_scoring_service,
    project_service,
)
from app.services.evaluation_scoring_service import EvaluationError

router = APIRouter(tags=["evaluation-scoring"])


def _detail(db: Session, result) -> AIEvaluationResultDetail:
    matches = evaluation_scoring_service.get_matches_for_result(
        db, result.evaluation_result_id
    )
    return AIEvaluationResultDetail(
        **AIEvaluationResultRead.model_validate(result).model_dump(),
        matches=matches,
    )


@router.post(
    "/ai-review-runs/{review_run_id}/evaluate",
    response_model=AIEvaluationResultDetail,
)
def evaluate_review_run(
    review_run_id: str, db: Session = Depends(get_db)
) -> AIEvaluationResultDetail:
    if ai_review_service.get_ai_review_run(db, review_run_id) is None:
        raise HTTPException(status_code=404, detail="AI review run not found")
    try:
        result = evaluation_scoring_service.evaluate_review_run(db, review_run_id)
    except EvaluationError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return _detail(db, result)


@router.get(
    "/ai-review-runs/{review_run_id}/evaluation",
    response_model=AIEvaluationResultDetail,
)
def get_run_evaluation(
    review_run_id: str, db: Session = Depends(get_db)
) -> AIEvaluationResultDetail:
    if ai_review_service.get_ai_review_run(db, review_run_id) is None:
        raise HTTPException(status_code=404, detail="AI review run not found")
    result = evaluation_scoring_service.latest_result_for_run(db, review_run_id)
    if result is None:
        raise HTTPException(
            status_code=404,
            detail="No evaluation result exists yet for this review run.",
        )
    return _detail(db, result)


@router.get(
    "/projects/{project_id}/ai-evaluation-results",
    response_model=list[AIEvaluationResultRead],
)
def list_project_evaluation_results(
    project_id: str, db: Session = Depends(get_db)
) -> list[AIEvaluationResultRead]:
    if project_service.get_project(db, project_id) is None:
        raise HTTPException(status_code=404, detail="Project not found")
    return evaluation_scoring_service.list_results_for_project(db, project_id)


@router.get(
    "/ai-evaluation-results/{evaluation_result_id}",
    response_model=AIEvaluationResultDetail,
)
def get_evaluation_result(
    evaluation_result_id: str, db: Session = Depends(get_db)
) -> AIEvaluationResultDetail:
    result = evaluation_scoring_service.get_evaluation_result(
        db, evaluation_result_id
    )
    if result is None:
        raise HTTPException(status_code=404, detail="Evaluation result not found")
    return _detail(db, result)
