"""Shared constants and helpers for the external review response package service.

Kept private to the package. The public surface is re-exported from the package
__init__.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.db import models

GENERATED_BY = "system"
DEFAULT_AUDIENCE = "design_engineer"

LIMITATIONS_NOTE = (
    "This is a draft external response package. It supports human review and "
    "does not send official correspondence, approve plans, certify compliance, "
    "stamp drawings, verify CAD, validate the design, or replace a licensed "
    "Professional Engineer."
)

EXTERNAL_COMMUNICATION_BOUNDARY = (
    "Civil Engineer AI prepares draft external communication for a human "
    "reviewer. It does not send email or official correspondence, and it does "
    "not approve plans, certify compliance, stamp drawings, verify CAD drawings, "
    "validate the design, or make final engineering decisions. A licensed "
    "Professional Engineer remains responsible for the review and any issued "
    "response."
)

DRAFT_NOTICE = (
    "Draft external response support material. It does not approve, certify, "
    "stamp, verify CAD, validate the design, or constitute final engineering "
    "approval, and it has not been sent."
)

DRAFT_INTRO = (
    "Thank you for the Brookside Meadows submission. The following review-support "
    "items were prepared to help organize a response. Each item is a draft "
    "prepared for human review and does not constitute final engineering "
    "approval."
)

DRAFT_CLOSING = (
    "Please direct questions on these review-support items to the reviewing "
    "office. This draft response is intended to support human review and does "
    "not constitute final engineering approval. A licensed Professional Engineer "
    "remains responsible for the review."
)

# Topical sections, in display order. opening_summary, attachments, and
# limitations_and_review_boundary are always present and informational. The
# demand sections only appear when at least one item maps to them.
SECTION_TITLES: dict[str, str] = {
    "opening_summary": "Opening summary",
    "requested_revisions": "Requested revisions",
    "missing_information": "Missing or incomplete information",
    "plan_sheet_items": "Plan sheet items",
    "stormwater_items": "Stormwater items",
    "erosion_control_items": "Erosion and sediment control items",
    "wetland_buffer_items": "Wetland buffer items",
    "attachments": "Attachments",
    "limitations_and_review_boundary": "Limitations and review boundary",
}
DEMAND_SECTION_ORDER = [
    "requested_revisions",
    "missing_information",
    "plan_sheet_items",
    "stormwater_items",
    "erosion_control_items",
    "wetland_buffer_items",
]


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _short() -> str:
    return uuid.uuid4().hex[:12]


def _audit(
    db: Session,
    *,
    project_id: str,
    event_type: str,
    related_entity_type: str,
    related_entity_id: str,
    description: str,
    actor_type: str = "system",
    metadata: dict | None = None,
) -> None:
    db.add(
        models.AuditEvent(
            audit_event_id=f"audit_resp_{uuid.uuid4().hex[:12]}",
            project_id=project_id,
            event_type=event_type,
            actor_type=actor_type,
            related_entity_type=related_entity_type,
            related_entity_id=related_entity_id,
            description=description,
            timestamp=_now(),
            event_metadata=metadata or {},
        )
    )
