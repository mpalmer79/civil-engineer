"""Applicant response mapping: create, auto-suggest, and summary.

Maps applicant responses to prior response package or workflow items. Matching
uses shared keywords between the applicant response and prior items. No live AI
calls and no vector search are used. Every mapping is a review-support
suggestion, not a verified match, and requires human review.
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.safety import ALLOWED_MAPPING_CONFIDENCE_LABELS
from app.db import models
from app.services import workflow_service
from app.services.review_cycle_service._common import (
    _audit,
    _keywords,
    _now,
    _response_package_items,
    _short,
)
from app.services.review_cycle_service.errors import ReviewCycleError
from app.services.review_cycle_service.lifecycle import _require_cycle


def list_applicant_responses(
    db: Session, project_id: str
) -> list[models.ApplicantResponse]:
    return list(
        db.scalars(
            select(models.ApplicantResponse)
            .where(models.ApplicantResponse.project_id == project_id)
            .order_by(models.ApplicantResponse.created_at)
        ).all()
    )


def _get_applicant_response(
    db: Session, applicant_response_id: str
) -> models.ApplicantResponse | None:
    return db.scalars(
        select(models.ApplicantResponse).where(
            models.ApplicantResponse.applicant_response_id == applicant_response_id
        )
    ).first()


def list_response_mappings_for_cycle(
    db: Session, review_cycle_id: str
) -> list[models.ApplicantResponseMapping]:
    return list(
        db.scalars(
            select(models.ApplicantResponseMapping)
            .where(
                models.ApplicantResponseMapping.review_cycle_id == review_cycle_id
            )
            .order_by(models.ApplicantResponseMapping.created_at)
        ).all()
    )


def create_applicant_response_mapping(
    db: Session,
    applicant_response_id: str,
    *,
    response_package_item_id: str | None = None,
    workflow_item_id: str | None = None,
    mapping_confidence: str = "medium",
    mapping_reason: str | None = None,
    commit: bool = True,
) -> models.ApplicantResponseMapping:
    response = _get_applicant_response(db, applicant_response_id)
    if response is None:
        raise ReviewCycleError("Applicant response not found.", status_code=404)
    if mapping_confidence not in ALLOWED_MAPPING_CONFIDENCE_LABELS:
        raise ReviewCycleError(
            f"Invalid mapping confidence '{mapping_confidence}'.", status_code=422
        )

    mapping = models.ApplicantResponseMapping(
        mapping_id=f"map_{_short()}",
        project_id=response.project_id,
        review_cycle_id=response.review_cycle_id,
        applicant_response_id=applicant_response_id,
        response_package_item_id=response_package_item_id,
        workflow_item_id=workflow_item_id,
        mapping_confidence=mapping_confidence,
        mapping_reason=mapping_reason
        or "Reviewer mapping between an applicant response and a prior item.",
        requires_human_review=True,
    )
    db.add(mapping)
    response.status = "mapped_to_issue"
    response.target_response_item_id = (
        response_package_item_id or response.target_response_item_id
    )
    response.target_workflow_item_id = (
        workflow_item_id or response.target_workflow_item_id
    )
    response.updated_at = _now()
    _audit(
        db,
        project_id=response.project_id,
        event_type="applicant_response_mapping_created",
        related_entity_type="applicant_response_mapping",
        related_entity_id=mapping.mapping_id,
        description="Applicant response mapping created.",
        metadata={
            "applicant_response_id": applicant_response_id,
            "mapping_id": mapping.mapping_id,
            "mapping_confidence": mapping_confidence,
        },
    )
    if commit:
        db.commit()
        db.refresh(mapping)
    return mapping


def auto_suggest_response_mappings(
    db: Session, review_cycle_id: str
) -> list[models.ApplicantResponseMapping]:
    """Create deterministic mapping suggestions for unmapped applicant responses.

    Matching uses shared keywords between the applicant response and prior
    response package items and workflow items. No live AI calls and no vector
    search are used. Every suggestion carries a confidence label and a reason and
    requires human review.
    """

    cycle = _require_cycle(db, review_cycle_id)
    project_id = cycle.project_id
    responses = [
        r
        for r in list_applicant_responses(db, project_id)
        if r.review_cycle_id == review_cycle_id and r.status == "received"
    ]
    existing_response_ids = {
        m.applicant_response_id
        for m in list_response_mappings_for_cycle(db, review_cycle_id)
    }

    response_items = _response_package_items(db, project_id)
    workflow_items = workflow_service.list_workflow_items(db, project_id)

    candidates: list[tuple[str, str, str, set[str]]] = []
    for item in response_items:
        candidates.append(
            (
                "response_package_item",
                item.item_id,
                item.title,
                _keywords(f"{item.title} {item.draft_text or ''}"),
            )
        )
    for item in workflow_items:
        candidates.append(
            (
                "workflow_item",
                item.workflow_item_id,
                item.title,
                _keywords(f"{item.title} {item.description or ''}"),
            )
        )

    created: list[models.ApplicantResponseMapping] = []
    for response in responses:
        if response.applicant_response_id in existing_response_ids:
            continue
        response_keywords = _keywords(
            f"{response.response_text} {response.response_topic}"
        )
        best = None
        best_overlap: set[str] = set()
        for kind, item_id, title, item_keywords in candidates:
            overlap = response_keywords & item_keywords
            # An explicit applicant target is a strong signal.
            explicit = item_id in {
                response.target_response_item_id,
                response.target_workflow_item_id,
            }
            score = len(overlap) + (5 if explicit else 0)
            if best is None or score > best[0]:
                best = (score, kind, item_id, title, explicit)
                best_overlap = overlap

        if best is None or best[0] == 0:
            # No prior item to map to; flag for human review.
            mapping = create_applicant_response_mapping(
                db,
                response.applicant_response_id,
                mapping_confidence="needs_human_review",
                mapping_reason=(
                    "No prior response or workflow item matched this response by "
                    "keyword. Reviewer should map it manually."
                ),
                commit=False,
            )
            created.append(mapping)
            continue

        _score, kind, item_id, title, explicit = best
        if explicit or _score >= 4:
            confidence = "high"
        elif _score >= 2:
            confidence = "medium"
        else:
            confidence = "low"
        shared = ", ".join(sorted(best_overlap)[:5]) or "topic"
        reason = (
            f"Suggested mapping to {kind.replace('_', ' ')} '{title}' based on "
            f"shared terms ({shared})."
        )
        mapping = create_applicant_response_mapping(
            db,
            response.applicant_response_id,
            response_package_item_id=(
                item_id if kind == "response_package_item" else None
            ),
            workflow_item_id=item_id if kind == "workflow_item" else None,
            mapping_confidence=confidence,
            mapping_reason=reason,
            commit=False,
        )
        created.append(mapping)

    _audit(
        db,
        project_id=project_id,
        event_type="response_mappings_suggested",
        related_entity_type="review_cycle",
        related_entity_id=review_cycle_id,
        description=f"{len(created)} response mapping suggestion(s) created.",
        metadata={"review_cycle_id": review_cycle_id, "suggested": len(created)},
    )
    db.commit()
    for mapping in created:
        db.refresh(mapping)
    return created


def get_response_mapping_summary(db: Session, review_cycle_id: str) -> dict:
    cycle = _require_cycle(db, review_cycle_id)
    responses = [
        r
        for r in list_applicant_responses(db, cycle.project_id)
        if r.review_cycle_id == review_cycle_id
    ]
    mappings = list_response_mappings_for_cycle(db, review_cycle_id)
    mapped_ids = {m.applicant_response_id for m in mappings}
    confidence_counts: dict[str, int] = {}
    for mapping in mappings:
        confidence_counts[mapping.mapping_confidence] = (
            confidence_counts.get(mapping.mapping_confidence, 0) + 1
        )
    _audit(
        db,
        project_id=cycle.project_id,
        event_type="response_mapping_summary_viewed",
        related_entity_type="review_cycle",
        related_entity_id=review_cycle_id,
        description="Response mapping summary viewed.",
        metadata={"review_cycle_id": review_cycle_id},
    )
    db.commit()
    return {
        "review_cycle_id": review_cycle_id,
        "project_id": cycle.project_id,
        "response_count": len(responses),
        "mapped_count": len(mapped_ids),
        "unmapped_count": len([r for r in responses if r.applicant_response_id not in mapped_ids]),
        "suggested_count": len(mappings),
        "confidence_counts": confidence_counts,
        "note": (
            "Mappings are review-support suggestions, not verified matches. Every "
            "mapping needs human review."
        ),
    }
