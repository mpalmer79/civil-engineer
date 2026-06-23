"""Evaluation API routes.

These endpoints read the seeded evaluation cases and run and read Phase 5
evaluation scoring of AI review runs. Evaluation produces heuristic
review-support metrics, not a final engineering determination.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.schemas.evaluation import (
    AIEvaluationResultDetail,
    AIEvaluationResultRead,
    EvaluationCaseRead,
)
from app.services import (
    ai_review_service,
    evaluation_scoring_service,
    evaluation_service,
    project_service,
)
from app.services.evaluation_scoring_service import EvaluationError

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


@router.post(
    "/ai-review-runs/{review_run_id}/evaluate",
    response_model=AIEvaluationResultDetail,
)
def evaluate_ai_review_run(
    review_run_id: str, db: Session = Depends(get_db)
) -> AIEvaluationResultDetail:
    if ai_review_service.get_ai_review_run(db, review_run_id) is None:
        raise HTTPException(status_code=404, detail="AI review run not found")
    try:
        result = evaluation_scoring_service.evaluate_review_run(db, review_run_id)
    except EvaluationError as exc:
        raise HTTPException(
            status_code=exc.status_code, detail=exc.message
        ) from exc
    matches = evaluation_scoring_service.get_matches_for_result(
        db, result.evaluation_result_id
    )
    detail = AIEvaluationResultDetail.model_validate(result)
    detail.matches = matches
    return detail


@router.get(
    "/ai-review-runs/{review_run_id}/evaluation",
    response_model=AIEvaluationResultDetail,
)
def get_ai_review_run_evaluation(
    review_run_id: str, db: Session = Depends(get_db)
) -> AIEvaluationResultDetail:
    if ai_review_service.get_ai_review_run(db, review_run_id) is None:
        raise HTTPException(status_code=404, detail="AI review run not found")
    result = evaluation_scoring_service.get_latest_evaluation_for_run(
        db, review_run_id
    )
    if result is None:
        raise HTTPException(
            status_code=404,
            detail="No evaluation result exists for this review run.",
        )
    matches = evaluation_scoring_service.get_matches_for_result(
        db, result.evaluation_result_id
    )
    detail = AIEvaluationResultDetail.model_validate(result)
    detail.matches = matches
    return detail


@router.get(
    "/projects/{project_id}/ai-evaluation-results",
    response_model=list[AIEvaluationResultRead],
)
def list_project_evaluation_results(
    project_id: str, db: Session = Depends(get_db)
) -> list[AIEvaluationResultRead]:
    if project_service.get_project(db, project_id) is None:
        raise HTTPException(status_code=404, detail="Project not found")
    return evaluation_scoring_service.list_evaluation_results_for_project(
        db, project_id
    )


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
        raise HTTPException(
            status_code=404, detail="Evaluation result not found"
        )
    matches = evaluation_scoring_service.get_matches_for_result(
        db, evaluation_result_id
    )
    detail = AIEvaluationResultDetail.model_validate(result)
    detail.matches = matches
    return detail
