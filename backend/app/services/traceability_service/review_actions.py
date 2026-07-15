"""Reviewer-controlled, append-only traceability review actions (Phase 4B)."""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.safety import (
    ALLOWED_TRACEABILITY_REVIEW_ACTIONS,
    find_prohibited_language,
)
from app.db import models
from app.services.traceability_service._common import _now
from app.services.traceability_service.errors import TraceabilityError


def record_traceability_review_action(
    db: Session,
    *,
    project_id: str,
    traceability_row_key: str,
    action_type: str,
    reviewer_note: str | None = None,
    created_by: str | None = None,
    checklist_item_id: str | None = None,
    evidence_citation_id: str | None = None,
    evidence_candidate_id: str | None = None,
    finding_id: str | None = None,
    workflow_item_id: str | None = None,
    review_packet_item_id: str | None = None,
    relationship_type: str | None = None,
) -> models.TraceabilityReviewAction:
    """Record one reviewer review action on a traceability row (append-only).

    Writes a TraceabilityReviewAction row and a matching audit event. It never
    mutates the checklist item, evidence, finding, workflow item, or packet the
    row references, so a link_rejected action discards the link for review without
    deleting any source data.
    """

    if db.get(models.Project, project_id) is None:
        raise TraceabilityError("Project not found.", status_code=404)
    if not traceability_row_key or not traceability_row_key.strip():
        raise TraceabilityError(
            "traceability_row_key is required.", status_code=422
        )
    if action_type not in ALLOWED_TRACEABILITY_REVIEW_ACTIONS:
        raise TraceabilityError(
            f"Unknown traceability review action '{action_type}'.",
            status_code=422,
        )
    note = (reviewer_note or "").strip() or None
    if note and find_prohibited_language(note):
        raise TraceabilityError(
            "reviewer_note contains prohibited final-decision wording.",
            status_code=422,
        )
    author = (created_by or "").strip() or "reviewer"
    row_key = traceability_row_key.strip()

    action_id = f"trace_act_{uuid.uuid4().hex[:12]}"
    record = models.TraceabilityReviewAction(
        action_id=action_id,
        project_id=project_id,
        traceability_row_key=row_key,
        action_type=action_type,
        reviewer_note=note,
        created_by=author,
        checklist_item_id=checklist_item_id,
        evidence_citation_id=evidence_citation_id,
        evidence_candidate_id=evidence_candidate_id,
        finding_id=finding_id,
        workflow_item_id=workflow_item_id,
        review_packet_item_id=review_packet_item_id,
        relationship_type=relationship_type,
    )
    db.add(record)
    db.add(
        models.AuditEvent(
            audit_event_id=f"audit_trace_{uuid.uuid4().hex[:12]}",
            project_id=project_id,
            event_type="traceability_review_action_recorded",
            actor_type="reviewer",
            related_entity_type="traceability_row",
            related_entity_id=row_key,
            description=(
                f"Traceability review action '{action_type}' recorded by "
                f"{author}."
            ),
            timestamp=_now(),
            event_metadata={
                "action_id": action_id,
                "traceability_row_key": row_key,
                "action_type": action_type,
                "checklist_item_id": checklist_item_id,
                "finding_id": finding_id,
                "relationship_type": relationship_type,
            },
        )
    )
    db.commit()
    db.refresh(record)
    return record


def list_traceability_review_actions(
    db: Session, project_id: str, traceability_row_key: str
) -> list[models.TraceabilityReviewAction]:
    """Return the recorded review action history for one traceability row."""

    stmt = (
        select(models.TraceabilityReviewAction)
        .where(
            models.TraceabilityReviewAction.project_id == project_id,
            models.TraceabilityReviewAction.traceability_row_key
            == traceability_row_key,
        )
        .order_by(models.TraceabilityReviewAction.created_at)
    )
    return list(db.scalars(stmt).all())
