"""Pydantic schemas for AI Review Assistant output.

The AI returns a draft review-support finding, not a final engineering
conclusion. The schema enforces that every draft requires human review and
acknowledges the professional boundary.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

# Finding types the AI may return. None of these implies final approval or
# certification.
FindingType = Literal[
    "supported_with_review",
    "missing_evidence",
    "conflicting_evidence",
    "unclear_evidence",
    "not_applicable",
    "requires_human_review",
]


class AIDraftFindingOutput(BaseModel):
    """Strict schema for a single AI-drafted draft finding."""

    checklist_item_id: str
    finding_type: FindingType
    title: str
    summary: str
    risk_level: Literal["low", "medium", "high"]
    confidence: float = Field(ge=0.0, le=1.0)
    source_chunk_ids: list[str]
    recommended_human_action: str
    requires_human_review: Literal[True]
    safety_boundary_acknowledged: Literal[True]
