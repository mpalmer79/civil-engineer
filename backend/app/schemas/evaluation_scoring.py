"""Pydantic schemas for AI evaluation scoring results and matches.

Evaluation scoring is a transparent, heuristic comparison of an AI review run's
draft findings against the seeded expected findings. It reports recall,
precision, citation validity, prohibited wording, and validation and safety
failure counts. It does not certify the AI or declare the package compliant.
"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class AIEvaluationMatchRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    evaluation_match_id: str
    evaluation_result_id: str
    expected_finding_id: str | None = None
    draft_finding_id: str | None = None
    match_type: str
    match_confidence: float
    matched_on: str | None = None
    notes: str | None = None
    created_at: datetime


class AIEvaluationResultRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    evaluation_result_id: str
    project_id: str
    review_run_id: str
    expected_findings_count: int
    draft_findings_count: int
    matched_findings_count: int
    unmatched_expected_count: int
    extra_draft_findings_count: int
    citation_validity_rate: float
    human_review_required_rate: float
    prohibited_word_count: int
    validation_failure_count: int
    safety_failure_count: int
    recall: float
    precision: float
    overall_score: float
    created_at: datetime


class AIEvaluationResultDetail(AIEvaluationResultRead):
    """An evaluation result with its match records included."""

    matches: list[AIEvaluationMatchRead] = []
