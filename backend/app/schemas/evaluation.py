"""Pydantic schemas for evaluation cases."""

from __future__ import annotations

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
