"""Pydantic schemas for AI review runs and draft findings."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class AIReviewRunRead(BaseModel):
    model_config = ConfigDict(from_attributes=True, protected_namespaces=())

    review_run_id: str
    project_id: str
    run_type: str
    provider: str
    model_name: str
    status: str
    prompt_version: str
    checklist_item_count: int
    draft_findings_created: int
    safety_failures: int
    started_at: datetime
    completed_at: datetime | None = None


class AIDraftFindingRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    draft_finding_id: str
    review_run_id: str
    project_id: str
    checklist_item_id: str
    finding_type: str
    title: str
    summary: str
    risk_level: str
    confidence: float
    status: str
    recommended_human_action: str
    source_chunk_ids: list[str]
    validation_status: str
    safety_check_status: str
    validation_errors: list[str]


class ProviderMode(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    provider: str
    mode: str
    model_name: str
    live_calls_enabled: bool
    detail: str
