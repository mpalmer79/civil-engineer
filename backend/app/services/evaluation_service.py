"""Read operations for evaluation cases."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import models


def list_evaluation_cases(
    db: Session, project_id: str | None = None
) -> list[models.EvaluationCase]:
    stmt = select(models.EvaluationCase)
    if project_id is not None:
        stmt = stmt.where(models.EvaluationCase.project_id == project_id)
    stmt = stmt.order_by(models.EvaluationCase.eval_case_id)
    return list(db.scalars(stmt).all())


def get_evaluation_case(
    db: Session, eval_case_id: str
) -> models.EvaluationCase | None:
    return db.get(models.EvaluationCase, eval_case_id)
