"""Pydantic schemas for background processing jobs.

A job resource reports the lifecycle of deferred review-support processing. It
exposes non-sensitive fields only: a job type, project scope, a small payload of
identifiers, status and retry bookkeeping, a safe error reason, and a result
summary. It never carries file bytes, secrets, or a stack trace, and it implies
no final engineering decision.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict


class JobResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    job_id: str
    job_type: str
    project_id: str
    payload: dict[str, Any]
    status: str
    attempts: int
    max_attempts: int
    result: dict[str, Any] | None = None
    error: str | None = None
    request_id: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
    available_at: datetime | None = None
    started_at: datetime | None = None
    finished_at: datetime | None = None
