"""Evaluation bounded context: evaluation cases, AI evaluation results, and match records."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import JSON, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base
from app.db.models.shared import _utcnow

class EvaluationCase(Base):
    __tablename__ = "evaluation_cases"

    eval_case_id: Mapped[str] = mapped_column(String, primary_key=True)
    project_id: Mapped[str] = mapped_column(
        ForeignKey("projects.project_id"), nullable=False
    )
    name: Mapped[str] = mapped_column(String, nullable=False)
    input_documents: Mapped[list] = mapped_column(JSON, default=list)
    expected_findings: Mapped[list] = mapped_column(JSON, default=list)
    expected_risk_level: Mapped[str] = mapped_column(String, nullable=False)
    evaluation_metric: Mapped[str] = mapped_column(String, nullable=False)
    seeded_result: Mapped[dict] = mapped_column(JSON, default=dict)

    project: Mapped["Project"] = relationship(back_populates="evaluation_cases")


class AIEvaluationResult(Base):
    """A scored evaluation of one AI review run against expected findings.

    Evaluation is heuristic and explainable, not a mathematically perfect
    measure. It compares the draft findings from a review run against the
    expected Brookside Meadows findings and records recall, precision, citation
    validity, and quality signals so the workflow stays auditable.
    """

    __tablename__ = "ai_evaluation_results"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    evaluation_result_id: Mapped[str] = mapped_column(
        String, unique=True, nullable=False
    )
    project_id: Mapped[str] = mapped_column(
        ForeignKey("projects.project_id"), nullable=False
    )
    review_run_id: Mapped[str] = mapped_column(
        ForeignKey("ai_review_runs.review_run_id"), nullable=False
    )
    expected_findings_count: Mapped[int] = mapped_column(Integer, default=0)
    draft_findings_count: Mapped[int] = mapped_column(Integer, default=0)
    matched_findings_count: Mapped[int] = mapped_column(Integer, default=0)
    unmatched_expected_count: Mapped[int] = mapped_column(Integer, default=0)
    extra_draft_findings_count: Mapped[int] = mapped_column(Integer, default=0)
    citation_validity_rate: Mapped[float] = mapped_column(Float, default=0.0)
    human_review_required_rate: Mapped[float] = mapped_column(Float, default=0.0)
    prohibited_word_count: Mapped[int] = mapped_column(Integer, default=0)
    validation_failure_count: Mapped[int] = mapped_column(Integer, default=0)
    safety_failure_count: Mapped[int] = mapped_column(Integer, default=0)
    recall: Mapped[float] = mapped_column(Float, default=0.0)
    precision: Mapped[float] = mapped_column(Float, default=0.0)
    overall_score: Mapped[float] = mapped_column(Float, default=0.0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=_utcnow
    )


class AIEvaluationMatch(Base):
    """A single explainable match record produced during evaluation scoring.

    Each record links an expected finding and/or a draft finding and records how
    the match was made (related checklist item, category, or title similarity)
    or that an item was unmatched or extra.
    """

    __tablename__ = "ai_evaluation_matches"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    evaluation_match_id: Mapped[str] = mapped_column(
        String, unique=True, nullable=False
    )
    evaluation_result_id: Mapped[str] = mapped_column(
        ForeignKey("ai_evaluation_results.evaluation_result_id"), nullable=False
    )
    expected_finding_id: Mapped[str | None] = mapped_column(String, nullable=True)
    draft_finding_id: Mapped[str | None] = mapped_column(String, nullable=True)
    match_type: Mapped[str] = mapped_column(String, nullable=False)
    match_confidence: Mapped[float] = mapped_column(Float, default=0.0)
    matched_on: Mapped[str | None] = mapped_column(String, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=_utcnow
    )
