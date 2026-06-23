"""Pydantic schemas for plan references.

A plan reference records where the package points from one place to another and
whether the target was located and labels agree. Its consistency status is
review-support evidence, never a final decision.
"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class PlanReferenceRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    plan_reference_id: str
    project_id: str
    source_type: str
    source_id: str
    target_type: str
    target_id: str
    reference_label: str
    reference_context: str
    consistency_status: str
    review_note: str | None
    created_at: datetime
