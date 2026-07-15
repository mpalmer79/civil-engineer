"""Promotion of CAD review findings into workflow board items.

Creates workflow board items from CAD review findings so a reviewer can track
follow-up. Promotion is idempotent per finding, so a finding already linked to a
workflow item is never promoted twice. Each created item needs human review and
does not approve, certify, or validate anything.
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import models
from app.services import workflow_service
from app.services.cad_intake_service._common import _audit, _short
from app.services.cad_intake_service.errors import CadIntakeError
from app.services.cad_intake_service.reads import list_cad_review_findings


def create_workflow_items_from_cad_findings(
    db: Session, project_id: str
) -> dict:
    """Create workflow board items from CAD review findings that need tracking.

    Idempotent per finding: a finding already linked to a workflow item is
    skipped. Writes a cad_workflow_items_created audit event.
    """

    if db.get(models.Project, project_id) is None:
        raise CadIntakeError("Project not found.", status_code=404)

    workflow_service.ensure_workflow_board(db, project_id)
    findings = [
        f
        for f in list_cad_review_findings(db, project_id)
        if f.linked_workflow_item_id is None
        and f.status not in {"excluded_from_packet"}
    ]
    created_ids: list[str] = []
    for finding in findings:
        item = models.WorkflowItem(
            workflow_item_id=f"wfi_{_short()}",
            project_id=project_id,
            packet_id=None,
            packet_item_id=None,
            title=finding.title,
            description=finding.description,
            source_type="cad_review_finding",
            source_id=finding.cad_review_finding_id,
            severity=finding.severity,
            status="draft",
            assigned_role="plan_reviewer",
            reviewer_note=None,
            target_date=None,
            section_type="plan_sheet_cad",
            evidence_types=["cad_file"],
            requires_human_review=True,
        )
        db.add(item)
        finding.linked_workflow_item_id = item.workflow_item_id
        finding.promoted_to_workflow = True
        finding.promoted_workflow_item_id = item.workflow_item_id
        created_ids.append(item.workflow_item_id)

    _audit(
        db,
        project_id=project_id,
        event_type="cad_workflow_items_created",
        related_entity_type="workflow_board",
        related_entity_id=project_id,
        description=f"{len(created_ids)} workflow items created from CAD findings.",
        metadata={"created_count": len(created_ids)},
    )
    db.commit()
    return {
        "created_count": len(created_ids),
        "workflow_item_ids": created_ids,
        "note": (
            "Workflow items created from CAD review findings. Each needs human "
            "review and does not approve, certify, or validate anything."
        ),
    }


def _build_workflow_item_from_finding(
    finding: models.CadReviewFinding, reviewer_note: str | None
) -> models.WorkflowItem:
    return models.WorkflowItem(
        workflow_item_id=f"wfi_{_short()}",
        project_id=finding.project_id,
        packet_id=None,
        packet_item_id=None,
        title=finding.title,
        description=finding.description,
        source_type="cad_review_finding",
        source_id=finding.cad_review_finding_id,
        severity=finding.severity,
        status="draft",
        assigned_role="plan_reviewer",
        reviewer_note=reviewer_note or None,
        target_date=None,
        section_type="plan_sheet_cad",
        evidence_types=["cad_file"],
        requires_human_review=True,
    )


def promote_cad_finding_to_workflow(
    db: Session,
    cad_review_finding_id: str,
    *,
    reviewer_name: str = "reviewer",
    reviewer_note: str | None = None,
    commit: bool = True,
) -> dict:
    """Promote a single CAD review finding into a workflow board item.

    Idempotent: a finding already linked to a workflow item is not promoted
    again, which prevents duplicate workflow items from the same CAD finding.
    Writes a cad_finding_promoted audit event when a new item is created.
    """

    finding = db.scalars(
        select(models.CadReviewFinding).where(
            models.CadReviewFinding.cad_review_finding_id == cad_review_finding_id
        )
    ).first()
    if finding is None:
        raise CadIntakeError("CAD review finding not found.", status_code=404)

    workflow_service.ensure_workflow_board(db, finding.project_id)

    if finding.linked_workflow_item_id is not None or finding.promoted_to_workflow:
        return {
            "cad_review_finding_id": cad_review_finding_id,
            "workflow_item_id": finding.linked_workflow_item_id
            or finding.promoted_workflow_item_id,
            "created": False,
            "already_promoted": True,
            "note": (
                "This CAD finding is already promoted to a workflow item. No "
                "duplicate workflow item was created."
            ),
        }

    item = _build_workflow_item_from_finding(finding, reviewer_note)
    db.add(item)
    finding.linked_workflow_item_id = item.workflow_item_id
    finding.promoted_to_workflow = True
    finding.promoted_workflow_item_id = item.workflow_item_id
    _audit(
        db,
        project_id=finding.project_id,
        event_type="cad_finding_promoted",
        related_entity_type="cad_review_finding",
        related_entity_id=cad_review_finding_id,
        description=(
            f"CAD finding promoted to workflow item by {reviewer_name}."
        ),
        actor_type="reviewer",
        metadata={
            "cad_review_finding_id": cad_review_finding_id,
            "workflow_item_id": item.workflow_item_id,
        },
    )
    if commit:
        db.commit()
    return {
        "cad_review_finding_id": cad_review_finding_id,
        "workflow_item_id": item.workflow_item_id,
        "created": True,
        "already_promoted": False,
        "note": (
            "Workflow item created from CAD review finding. It needs human "
            "review and does not approve, certify, or validate anything."
        ),
    }


def promote_selected_cad_findings_to_workflow(
    db: Session,
    project_id: str,
    cad_review_finding_ids: list[str],
    *,
    reviewer_name: str = "reviewer",
    reviewer_note: str | None = None,
) -> dict:
    """Promote selected CAD review findings into workflow items.

    Each finding is promoted at most once, so re-promoting an already promoted
    finding does not create a duplicate workflow item. Writes a
    cad_findings_promoted_selected audit event.
    """

    if db.get(models.Project, project_id) is None:
        raise CadIntakeError("Project not found.", status_code=404)

    results: list[dict] = []
    created_ids: list[str] = []
    created_count = 0
    already_promoted_count = 0
    not_found_count = 0
    for finding_id in cad_review_finding_ids:
        try:
            result = promote_cad_finding_to_workflow(
                db,
                finding_id,
                reviewer_name=reviewer_name,
                reviewer_note=reviewer_note,
                commit=False,
            )
        except CadIntakeError:
            not_found_count += 1
            results.append(
                {
                    "cad_review_finding_id": finding_id,
                    "workflow_item_id": None,
                    "created": False,
                    "already_promoted": False,
                    "note": "CAD review finding not found.",
                }
            )
            continue
        results.append(result)
        if result["created"]:
            created_count += 1
            if result["workflow_item_id"]:
                created_ids.append(result["workflow_item_id"])
        elif result["already_promoted"]:
            already_promoted_count += 1

    _audit(
        db,
        project_id=project_id,
        event_type="cad_findings_promoted_selected",
        related_entity_type="workflow_board",
        related_entity_id=project_id,
        description=(
            f"{created_count} workflow item(s) created from selected CAD "
            f"findings by {reviewer_name}."
        ),
        actor_type="reviewer",
        metadata={
            "requested_count": len(cad_review_finding_ids),
            "created_count": created_count,
            "already_promoted_count": already_promoted_count,
            "not_found_count": not_found_count,
        },
    )
    db.commit()
    return {
        "project_id": project_id,
        "requested_count": len(cad_review_finding_ids),
        "created_count": created_count,
        "already_promoted_count": already_promoted_count,
        "not_found_count": not_found_count,
        "workflow_item_ids": created_ids,
        "results": results,
        "note": (
            "Selected CAD findings promoted to workflow items. Each needs human "
            "review and does not approve, certify, or validate anything."
        ),
    }
