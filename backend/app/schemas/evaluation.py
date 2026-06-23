"""Pydantic schemas for evaluation cases and evaluation scoring results."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class SeededResult(BaseModel):
    expected_findings_detected: str
    source_citation_accuracy: float
    false_positives: int
    false_negatives: int
    unsupported_claims: int
    prohibited_wording_count: int
    human_review_required: int
    passed: bool


class EvaluationCaseRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    eval_case_id: str
    project_id: str
    name: str
    input_documents: list[str]
    expected_findings: list[str]
    expected_risk_level: str
    evaluation_metric: str
    seeded_result: SeededResult


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
    matches: list[AIEvaluationMatchRead] = []
