"""Project checklists created from rule packs, plus their reads.

A reviewer can attach a rule pack to a project as a working checklist, list a
project's checklists, read a single checklist with status summaries, and list
its items. Checklist status is review-support only.
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import models
from app.services.auth_service import ActorContext, audit_kwargs
from app.services.checklist_review_service._common import (
    _checklist_items,
    _require_project,
)
from app.services.checklist_review_service.errors import ChecklistReviewError
from app.services.checklist_review_service.rule_packs import _rule_pack_items
from app.services.real_intake_service import (
    DEMO_ACTOR_ID,
    DEMO_ACTOR_NAME,
    _now,
    _short,
    ensure_demo_actor,
    record_audit_event,
)


def create_project_checklist_from_rule_pack(
    db: Session,
    project_id: str,
    rule_pack_id: str,
    *,
    name: str | None = None,
    actor_name: str = DEMO_ACTOR_NAME,
    actor: "ActorContext | None" = None,
) -> dict:
    """Attach a rule pack to a project as a working checklist with items."""

    _require_project(db, project_id)
    ensure_demo_actor(db)
    if actor is not None:
        actor_name = actor.display_name
    pack = db.get(models.RulePack, rule_pack_id)
    if pack is None:
        raise ChecklistReviewError("Rule pack not found.", status_code=404)

    now = _now()
    checklist_id = f"pcl_{_short()}"
    checklist = models.ProjectChecklist(
        project_checklist_id=checklist_id,
        project_id=project_id,
        rule_pack_id=rule_pack_id,
        name=(name or pack.name).strip(),
        status="checklist_started",
        source_mode="user_created",
        created_by_actor_id=DEMO_ACTOR_ID,
        created_by_name=actor_name,
        created_at=now,
        updated_at=now,
    )
    db.add(checklist)

    items = _rule_pack_items(db, rule_pack_id)
    for item in items:
        db.add(
            models.ProjectChecklistItem(
                project_checklist_item_id=f"pcli_{_short()}",
                project_checklist_id=checklist_id,
                project_id=project_id,
                rule_pack_item_id=item.rule_pack_item_id,
                item_code=item.item_code,
                category=item.category,
                requirement_text=item.requirement_text,
                expected_evidence=item.expected_evidence,
                applicability_status="needs_reviewer_confirmation",
                evidence_status="not_reviewed",
                review_status="not_started",
                risk_level=item.risk_level,
                sort_order=item.sort_order,
                created_at=now,
                updated_at=now,
            )
        )

    record_audit_event(
        db,
        **audit_kwargs(actor),
        project_id=project_id,
        event_type="project_checklist_created",
        related_entity_type="project_checklist",
        related_entity_id=checklist_id,
        description=(
            f"Reviewer created checklist '{checklist.name}' from rule pack "
            f"'{pack.name}' ({len(items)} item(s))."
        ),
        actor_type="reviewer",
        actor_display_name=actor_name,
        metadata={
            "project_checklist_id": checklist_id,
            "rule_pack_id": rule_pack_id,
            "item_count": len(items),
        },
    )
    db.commit()
    db.refresh(checklist)
    return get_project_checklist(db, project_id, checklist_id)


def list_project_checklists(db: Session, project_id: str) -> list[dict]:
    _require_project(db, project_id)
    checklists = db.scalars(
        select(models.ProjectChecklist)
        .where(models.ProjectChecklist.project_id == project_id)
        .order_by(models.ProjectChecklist.created_at)
    ).all()
    return [_checklist_dict(db, c) for c in checklists]


def get_project_checklist(
    db: Session, project_id: str, project_checklist_id: str
) -> dict:
    checklist = db.get(models.ProjectChecklist, project_checklist_id)
    if checklist is None or checklist.project_id != project_id:
        raise ChecklistReviewError(
            "Project checklist not found.", status_code=404
        )
    return _checklist_dict(db, checklist)


def _checklist_dict(db: Session, checklist: models.ProjectChecklist) -> dict:
    items = _checklist_items(db, checklist.project_checklist_id)
    evidence_summary: dict[str, int] = {}
    review_summary: dict[str, int] = {}
    for item in items:
        evidence_summary[item.evidence_status] = (
            evidence_summary.get(item.evidence_status, 0) + 1
        )
        review_summary[item.review_status] = (
            review_summary.get(item.review_status, 0) + 1
        )
    return {
        "project_checklist_id": checklist.project_checklist_id,
        "project_id": checklist.project_id,
        "rule_pack_id": checklist.rule_pack_id,
        "name": checklist.name,
        "status": checklist.status,
        "source_mode": checklist.source_mode,
        "created_by_name": checklist.created_by_name,
        "created_at": checklist.created_at,
        "updated_at": checklist.updated_at,
        "item_count": len(items),
        "evidence_status_summary": evidence_summary,
        "review_status_summary": review_summary,
    }


def list_project_checklist_items(
    db: Session, project_id: str, project_checklist_id: str
) -> list[models.ProjectChecklistItem]:
    get_project_checklist(db, project_id, project_checklist_id)
    return _checklist_items(db, project_checklist_id)
