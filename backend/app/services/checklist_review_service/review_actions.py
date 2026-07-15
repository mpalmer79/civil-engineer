"""Reviewer-controlled checklist item status updates and evidence search.

A reviewer can update an item's applicability, evidence, and review status and
add a note, and can search indexed evidence for an item. Checklist status is
review-support only; nothing here makes a final engineering decision.
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.core.safety import (
    ALLOWED_CHECKLIST_APPLICABILITY_STATUSES,
    ALLOWED_CHECKLIST_EVIDENCE_STATUSES,
    ALLOWED_CHECKLIST_REVIEW_STATUSES,
    reject_prohibited_language,
)
from app.db import models
from app.services import evidence_retrieval_service
from app.services.checklist_review_service._common import get_checklist_item
from app.services.checklist_review_service.errors import ChecklistReviewError
from app.services.real_intake_service import (
    DEMO_ACTOR_ID,
    DEMO_ACTOR_NAME,
    _now,
    ensure_demo_actor,
    record_audit_event,
)


def update_project_checklist_item(
    db: Session,
    project_id: str,
    project_checklist_item_id: str,
    payload: dict,
    *,
    actor_name: str = DEMO_ACTOR_NAME,
) -> models.ProjectChecklistItem:
    """Update reviewer-controlled applicability, evidence, review status, note."""

    item = get_checklist_item(db, project_id, project_checklist_item_id)
    ensure_demo_actor(db)
    reject_prohibited_language(payload.get("reviewer_note"), field="reviewer_note")

    applicability = payload.get("applicability_status")
    evidence = payload.get("evidence_status")
    review = payload.get("review_status")
    note = payload.get("reviewer_note")

    if applicability is not None:
        if applicability not in ALLOWED_CHECKLIST_APPLICABILITY_STATUSES:
            raise ChecklistReviewError(
                f"Invalid applicability_status '{applicability}'.",
                status_code=422,
            )
        item.applicability_status = applicability
    if evidence is not None:
        if evidence not in ALLOWED_CHECKLIST_EVIDENCE_STATUSES:
            raise ChecklistReviewError(
                f"Invalid evidence_status '{evidence}'.", status_code=422
            )
        item.evidence_status = evidence
    if review is not None:
        if review not in ALLOWED_CHECKLIST_REVIEW_STATUSES:
            raise ChecklistReviewError(
                f"Invalid review_status '{review}'.", status_code=422
            )
        item.review_status = review
    if note is not None:
        item.reviewer_note = note
        if review is None and item.review_status == "not_started":
            item.review_status = "reviewer_note_added"

    now = _now()
    item.updated_at = now
    item.reviewed_by_actor_id = DEMO_ACTOR_ID
    item.reviewed_by_name = actor_name
    item.reviewed_at = now

    event_type = "checklist_item_status_updated"
    if applicability == "not_applicable_by_reviewer":
        event_type = "checklist_item_marked_not_applicable_by_reviewer"
    elif note is not None and applicability is None and evidence is None and review is None:
        event_type = "checklist_item_note_added"

    record_audit_event(
        db,
        project_id=project_id,
        event_type=event_type,
        related_entity_type="project_checklist_item",
        related_entity_id=project_checklist_item_id,
        description=(
            f"Reviewer updated checklist item {item.item_code}."
        ),
        actor_type="reviewer",
        actor_display_name=actor_name,
        metadata={
            "checklist_item_id": project_checklist_item_id,
            "applicability_status": item.applicability_status,
            "evidence_status": item.evidence_status,
            "review_status": item.review_status,
        },
    )
    db.commit()
    db.refresh(item)
    return item


def search_evidence_for_checklist_item(
    db: Session,
    project_id: str,
    project_checklist_item_id: str,
    payload: dict | None = None,
    *,
    actor_name: str = DEMO_ACTOR_NAME,
) -> dict:
    """Search indexed evidence for a checklist item's expected evidence text."""

    item = get_checklist_item(db, project_id, project_checklist_item_id)
    payload = payload or {}
    query_text = (
        payload.get("query_text")
        or item.expected_evidence
        or item.requirement_text
        or ""
    ).strip()

    search_payload = {
        "query_text": query_text,
        "query_type": "checklist_item",
        "filters": {"checklist_item_id": project_checklist_item_id},
        "limit": payload.get("limit", 10),
    }
    result = evidence_retrieval_service.search_project_evidence(
        db, project_id, search_payload, actor_name=actor_name
    )

    record_audit_event(
        db,
        project_id=project_id,
        event_type="checklist_evidence_search_performed",
        related_entity_type="project_checklist_item",
        related_entity_id=project_checklist_item_id,
        description=(
            f"Reviewer searched evidence for checklist item {item.item_code}; "
            f"{result['result_count']} candidate(s)."
        ),
        actor_type="reviewer",
        actor_display_name=actor_name,
        metadata={
            "checklist_item_id": project_checklist_item_id,
            "result_count": result["result_count"],
            "retrieval_query_id": result.get("retrieval_query_id"),
        },
    )
    if item.review_status == "not_started":
        item.review_status = "evidence_review_needed"
        item.updated_at = _now()
    db.commit()
    return result
