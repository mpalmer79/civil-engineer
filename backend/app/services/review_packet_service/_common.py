"""Shared helpers and constants for the review packet service package."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.db import models

PACKET_TYPE = "review_support_draft"
GENERATED_BY = "system"
GENERATED_FROM_PHASE = "phase_1_to_7"

LIMITATIONS_NOTE = (
    "This is a draft review-support packet. It organizes evidence for a human "
    "reviewer and does not approve plans, certify compliance, stamp drawings, "
    "verify CAD, validate the design, or replace a licensed Professional "
    "Engineer."
)

PROFESSIONAL_LIMITATIONS = (
    "Civil Engineer AI is a review-support and evidence-organization system. "
    "This packet is a draft that organizes submitted documents, checklist "
    "items, findings, plan sheet metadata, CAD-aware metadata, and review "
    "actions for a human reviewer. It does not approve plans, certify "
    "compliance, stamp drawings, verify CAD drawings, validate the design, or "
    "make final engineering decisions. Every item requires human review, and a "
    "licensed Professional Engineer remains responsible for the review."
)

DRAFT_NOTICE = (
    "Draft review-support material. It does not approve, certify, stamp, "
    "verify CAD, or validate the design, and it does not replace a licensed "
    "Professional Engineer."
)

TRACEABILITY_REVIEW_NOTE = (
    "Traceability review state for rows included in this packet. A reviewer "
    "review action records that the reviewer reviewed the link for review only. "
    "Rows without an action require reviewer confirmation. None of this means a "
    "requirement is satisfied or a plan is approved."
)


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
            audit_event_id=f"audit_pkt_{uuid.uuid4().hex[:12]}",
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
