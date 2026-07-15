"""Workflow board lifecycle: generation, deletion, and startup ensure."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import models
from app.services import review_packet_service

from ._common import (
    DEFAULT_ROLE,
    INITIAL_STATUS,
    SECTION_TO_ROLE,
    _audit,
    _short,
)
from .errors import WorkflowError


def _delete_existing(db: Session, project_id: str) -> None:
    item_ids = [
        i.workflow_item_id
        for i in db.scalars(
            select(models.WorkflowItem).where(
                models.WorkflowItem.project_id == project_id
            )
        ).all()
    ]
    if not item_ids:
        return
    for model in (
        models.WorkflowFollowUpRequest,
        models.WorkflowAction,
    ):
        db.query(model).filter(
            model.workflow_item_id.in_(item_ids)
        ).delete(synchronize_session=False)
    db.query(models.WorkflowItem).filter(
        models.WorkflowItem.project_id == project_id
    ).delete(synchronize_session=False)
    db.commit()


def generate_workflow_items_from_review_packet(
    db: Session, project_id: str
) -> list[models.WorkflowItem]:
    """Generate a fresh workflow board for a project from its latest packet.

    Idempotent: existing workflow items, actions, and follow-up requests for the
    project are removed and a new board is built from the most recent review
    packet. Only packet items that require human review become workflow items,
    since informational summary, traceability, and limitations items do not need
    operational tracking. Writes a workflow_board_generated audit event.
    """

    if db.get(models.Project, project_id) is None:
        raise WorkflowError("Project not found.", status_code=404)

    packets = review_packet_service.list_review_packets(db, project_id)
    if not packets:
        # Ensure a packet exists so the board has source items to promote.
        review_packet_service.generate_review_packet(db, project_id)
        packets = review_packet_service.list_review_packets(db, project_id)
    packet = packets[0]
    detail = review_packet_service.assemble_packet_detail(db, packet)

    _delete_existing(db, project_id)

    created: list[models.WorkflowItem] = []
    for section in detail["sections"]:
        section_type = section["section_type"]
        role = SECTION_TO_ROLE.get(section_type, DEFAULT_ROLE)
        for item in section["items"]:
            if not item["requires_human_review"]:
                continue
            evidence_types = sorted(
                {link.evidence_type for link in item["evidence_links"]}
            )
            workflow_item = models.WorkflowItem(
                workflow_item_id=f"wfi_{_short()}",
                project_id=project_id,
                packet_id=packet.packet_id,
                packet_item_id=item["item_id"],
                title=item["title"],
                description=item["description"],
                source_type=item["source_type"],
                source_id=item["source_id"],
                severity=item["severity"],
                status=INITIAL_STATUS,
                assigned_role=role,
                reviewer_note=None,
                target_date=None,
                section_type=section_type,
                evidence_types=evidence_types,
                requires_human_review=True,
            )
            db.add(workflow_item)
            created.append(workflow_item)

    _audit(
        db,
        project_id=project_id,
        event_type="workflow_board_generated",
        related_entity_type="workflow_board",
        related_entity_id=project_id,
        description=(
            f"Reviewer workflow board generated with {len(created)} items from "
            f"packet {packet.packet_id}."
        ),
        metadata={
            "packet_id": packet.packet_id,
            "item_count": len(created),
        },
    )
    db.commit()
    for item in created:
        db.refresh(item)
    return created


def ensure_workflow_board(db: Session, project_id: str) -> None:
    """Generate a workflow board once if none exists for the project.

    Used at startup so the read endpoints and frontend have a board without a
    manual generate call. Gated on no workflow items existing, so it does not
    regenerate on every restart.
    """

    if db.get(models.Project, project_id) is None:
        return
    existing = (
        db.query(models.WorkflowItem)
        .filter(models.WorkflowItem.project_id == project_id)
        .first()
    )
    if existing is None:
        generate_workflow_items_from_review_packet(db, project_id)
