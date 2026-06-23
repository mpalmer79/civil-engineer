"""Plan consistency service for the Phase 6 foundation.

This service evaluates the seeded plan references and plan sheets to surface
review-support gaps: referenced sheets that are not included, references whose
target cannot be located, conflicting civil feature labels, and unclear sheet
revisions. From those signals it generates plan consistency findings, each of
which requires human review.

These checks are review-support and evidence-organization only. They do not
perform final design review, verify CAD drawings, certify compliance, or make
any final engineering decision. The wording mirrors the rest of the system:
potential issue, missing target, conflicting label, unclear revision, needs
human review.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import models

# A reference whose status is anything other than "consistent" is treated as an
# inconsistency that generates a plan consistency finding.
CONSISTENT_STATUS = "consistent"

# Map a reference consistency status (and target type) to a plan finding type.
_FINDING_TYPE_BY_STATUS = {
    "conflicting_label": "conflicting_label",
    "unclear": "unclear_revision",
    "needs_human_review": "requires_human_review",
}

# Concise titles and recommended human actions per plan finding type. The
# specific detail for each finding comes from the reference context and review
# note, so these stay short and consistent.
_TITLE_BY_TYPE = {
    "missing_referenced_sheet": "Referenced sheet is not included in the package",
    "missing_plan_reference": "Referenced item is not located on a current plan sheet",
    "conflicting_label": "Conflicting civil feature label across documents",
    "unclear_revision": "Plan sheet reference is unclear and needs confirmation",
    "requires_human_review": "Plan reference needs human review",
}

_ACTION_BY_TYPE = {
    "missing_referenced_sheet": (
        "Request the missing referenced sheet so the cited revision can be "
        "reviewed."
    ),
    "missing_plan_reference": (
        "Confirm where the referenced item is shown, or request that it be "
        "added to a current plan sheet."
    ),
    "conflicting_label": (
        "Request a consistent label for the feature across the plan set and "
        "report."
    ),
    "unclear_revision": (
        "Request a clarified sheet revision or complete sequence notes for "
        "reviewer confirmation."
    ),
    "requires_human_review": (
        "Have a reviewer confirm the reference and the responsible party before "
        "any follow-up."
    ),
}

_RISK_BY_TYPE = {
    "missing_referenced_sheet": "medium",
    "missing_plan_reference": "medium",
    "conflicting_label": "medium",
    "unclear_revision": "medium",
    "requires_human_review": "high",
}


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _audit(
    db: Session,
    *,
    project_id: str,
    event_type: str,
    related_entity_type: str,
    related_entity_id: str,
    description: str,
    metadata: dict | None = None,
) -> None:
    db.add(
        models.AuditEvent(
            audit_event_id=f"audit_plan_{uuid.uuid4().hex[:12]}",
            project_id=project_id,
            event_type=event_type,
            actor_type="system",
            related_entity_type=related_entity_type,
            related_entity_id=related_entity_id,
            description=description,
            timestamp=_now(),
            event_metadata=metadata or {},
        )
    )


def list_plan_references(
    db: Session, project_id: str
) -> list[models.PlanReference]:
    """Return all plan references for a project."""

    stmt = (
        select(models.PlanReference)
        .where(models.PlanReference.project_id == project_id)
        .order_by(models.PlanReference.plan_reference_id)
    )
    return list(db.scalars(stmt).all())


def list_inconsistencies(
    db: Session, project_id: str
) -> list[models.PlanReference]:
    """Return references whose target is missing, conflicting, or unclear."""

    return [
        ref
        for ref in list_plan_references(db, project_id)
        if ref.consistency_status != CONSISTENT_STATUS
    ]


def list_plan_consistency_findings(
    db: Session, project_id: str
) -> list[models.PlanConsistencyFinding]:
    """Return all plan consistency findings for a project."""

    stmt = (
        select(models.PlanConsistencyFinding)
        .where(models.PlanConsistencyFinding.project_id == project_id)
        .order_by(models.PlanConsistencyFinding.plan_finding_id)
    )
    return list(db.scalars(stmt).all())


def get_plan_consistency_finding(
    db: Session, plan_finding_id: str
) -> models.PlanConsistencyFinding | None:
    """Return one plan consistency finding by id."""

    stmt = select(models.PlanConsistencyFinding).where(
        models.PlanConsistencyFinding.plan_finding_id == plan_finding_id
    )
    return db.scalars(stmt).first()


def _finding_type_for(ref: models.PlanReference) -> str:
    """Resolve the plan finding type for a non-consistent reference."""

    if ref.consistency_status == "missing_target":
        return (
            "missing_referenced_sheet"
            if ref.target_type == "plan_sheet"
            else "missing_plan_reference"
        )
    return _FINDING_TYPE_BY_STATUS.get(
        ref.consistency_status, "requires_human_review"
    )


def _resolve_related(db: Session, ref: models.PlanReference) -> dict:
    """Resolve related sheets, documents, CAD records, and checklist items.

    The related entities are derived from the reference source and target plus
    the metadata on any linked plan sheet or CAD feature, so each finding links
    back to concrete evidence for the reviewer.
    """

    sheet_ids: list[str] = []
    document_ids: list[str] = []
    cad_metadata_ids: list[str] = []
    checklist_items: list[str] = []

    def _add(items: list[str], value: str | None) -> None:
        if value and value not in items:
            items.append(value)

    for entity_type, entity_id in (
        (ref.source_type, ref.source_id),
        (ref.target_type, ref.target_id),
    ):
        if entity_type == "plan_sheet":
            _add(sheet_ids, entity_id)
            sheet = db.scalars(
                select(models.PlanSheet).where(
                    models.PlanSheet.sheet_id == entity_id
                )
            ).first()
            if sheet is not None:
                for item in sheet.related_checklist_items:
                    _add(checklist_items, item)
        elif entity_type == "document":
            _add(document_ids, entity_id)
        elif entity_type == "cad_feature":
            _add(cad_metadata_ids, entity_id)
            cad = db.scalars(
                select(models.CadMetadata).where(
                    models.CadMetadata.cad_metadata_id == entity_id
                )
            ).first()
            if cad is not None:
                _add(sheet_ids, cad.sheet_id)
                _add(document_ids, cad.related_document_id)
                _add(checklist_items, cad.related_checklist_item_id)

    return {
        "related_sheet_ids": sheet_ids,
        "related_document_ids": document_ids,
        "related_cad_metadata_ids": cad_metadata_ids,
        "related_checklist_items": checklist_items,
    }


def _build_finding(
    db: Session, ref: models.PlanReference
) -> models.PlanConsistencyFinding:
    """Build a plan consistency finding from a non-consistent reference."""

    finding_type = _finding_type_for(ref)
    related = _resolve_related(db, ref)
    summary = ref.reference_context
    if ref.review_note:
        summary = f"{summary} {ref.review_note}"

    return models.PlanConsistencyFinding(
        plan_finding_id=f"plan_find_{ref.plan_reference_id}",
        project_id=ref.project_id,
        finding_type=finding_type,
        title=_TITLE_BY_TYPE[finding_type],
        summary=summary,
        risk_level=_RISK_BY_TYPE[finding_type],
        status="requires_human_review",
        recommended_human_action=_ACTION_BY_TYPE[finding_type],
        **related,
    )


def run_consistency_check(db: Session, project_id: str) -> dict:
    """Evaluate plan references and sheets and generate consistency findings.

    The check is idempotent: existing plan consistency findings for the project
    are removed and regenerated from the current references and sheets. Audit
    events are written for the start, the sheet index load, the CAD metadata
    load, each reference evaluated, each finding created, and completion.
    """

    _audit(
        db,
        project_id=project_id,
        event_type="plan_consistency_check_started",
        related_entity_type="project",
        related_entity_id=project_id,
        description="Plan consistency check started over seeded references and sheets.",
    )

    sheets = db.scalars(
        select(models.PlanSheet).where(models.PlanSheet.project_id == project_id)
    ).all()
    missing_sheet_ids = [
        s.sheet_id
        for s in sheets
        if s.status in {"missing", "referenced_not_included"}
    ]
    _audit(
        db,
        project_id=project_id,
        event_type="plan_sheet_index_loaded",
        related_entity_type="plan_sheet_index",
        related_entity_id=project_id,
        description=f"Loaded {len(sheets)} plan sheets for the project.",
        metadata={
            "total_sheets": len(sheets),
            "missing_sheet_ids": missing_sheet_ids,
        },
    )

    cad_records = db.scalars(
        select(models.CadMetadata).where(
            models.CadMetadata.project_id == project_id
        )
    ).all()
    _audit(
        db,
        project_id=project_id,
        event_type="cad_metadata_loaded",
        related_entity_type="cad_metadata",
        related_entity_id=project_id,
        description=f"Loaded {len(cad_records)} CAD-aware metadata records.",
        metadata={"cad_metadata_records": len(cad_records)},
    )

    references = list_plan_references(db, project_id)
    inconsistent: list[models.PlanReference] = []
    for ref in references:
        is_consistent = ref.consistency_status == CONSISTENT_STATUS
        if not is_consistent:
            inconsistent.append(ref)
        _audit(
            db,
            project_id=project_id,
            event_type="plan_reference_evaluated",
            related_entity_type="plan_reference",
            related_entity_id=ref.plan_reference_id,
            description=(
                f"Evaluated plan reference {ref.plan_reference_id}: "
                f"{ref.consistency_status}."
            ),
            metadata={
                "reference_id": ref.plan_reference_id,
                "consistency_status": ref.consistency_status,
                "reference_label": ref.reference_label,
            },
        )

    # Regenerate findings from the current evaluation so the check is idempotent.
    db.query(models.PlanConsistencyFinding).filter_by(
        project_id=project_id
    ).delete()

    counts_by_type: dict[str, int] = {}
    for ref in inconsistent:
        finding = _build_finding(db, ref)
        db.add(finding)
        counts_by_type[finding.finding_type] = (
            counts_by_type.get(finding.finding_type, 0) + 1
        )
        _audit(
            db,
            project_id=project_id,
            event_type="plan_consistency_finding_created",
            related_entity_type="plan_consistency_finding",
            related_entity_id=finding.plan_finding_id,
            description=(
                f"Plan consistency finding created: {finding.title} "
                f"({finding.finding_type}). Requires human review."
            ),
            metadata={
                "plan_finding_id": finding.plan_finding_id,
                "finding_type": finding.finding_type,
                "reference_id": ref.plan_reference_id,
                "consistency_status": ref.consistency_status,
                "related_sheet_ids": finding.related_sheet_ids,
                "related_cad_metadata_ids": finding.related_cad_metadata_ids,
            },
        )

    summary = {
        "project_id": project_id,
        "total_sheets": len(sheets),
        "missing_sheet_count": len(missing_sheet_ids),
        "cad_metadata_records": len(cad_records),
        "total_plan_references": len(references),
        "inconsistent_references": len(inconsistent),
        "plan_consistency_findings": len(inconsistent),
        "conflicting_label_count": counts_by_type.get("conflicting_label", 0),
        "missing_referenced_sheet_count": counts_by_type.get(
            "missing_referenced_sheet", 0
        ),
        "missing_plan_reference_count": counts_by_type.get(
            "missing_plan_reference", 0
        ),
        "unclear_revision_count": counts_by_type.get("unclear_revision", 0),
        "requires_human_review_count": counts_by_type.get(
            "requires_human_review", 0
        ),
        "findings_requiring_human_review": len(inconsistent),
    }

    _audit(
        db,
        project_id=project_id,
        event_type="plan_consistency_check_completed",
        related_entity_type="project",
        related_entity_id=project_id,
        description=(
            f"Plan consistency check completed: {len(inconsistent)} findings "
            "created. All findings require human review."
        ),
        metadata=summary,
    )

    db.commit()
    return summary


def plan_consistency_summary(db: Session, project_id: str) -> dict:
    """Return a summary of current plan consistency findings without re-running.

    This reads the stored findings and references so frontend summary panels can
    display counts without triggering a new check or writing audit events.
    """

    sheets = db.scalars(
        select(models.PlanSheet).where(models.PlanSheet.project_id == project_id)
    ).all()
    cad_records = db.scalars(
        select(models.CadMetadata).where(
            models.CadMetadata.project_id == project_id
        )
    ).all()
    references = list_plan_references(db, project_id)
    findings = list_plan_consistency_findings(db, project_id)

    counts_by_type: dict[str, int] = {}
    for finding in findings:
        counts_by_type[finding.finding_type] = (
            counts_by_type.get(finding.finding_type, 0) + 1
        )

    missing_sheet_count = len(
        [s for s in sheets if s.status in {"missing", "referenced_not_included"}]
    )
    inconsistent = [
        r for r in references if r.consistency_status != CONSISTENT_STATUS
    ]

    return {
        "project_id": project_id,
        "total_sheets": len(sheets),
        "missing_sheet_count": missing_sheet_count,
        "cad_metadata_records": len(cad_records),
        "total_plan_references": len(references),
        "inconsistent_references": len(inconsistent),
        "plan_consistency_findings": len(findings),
        "conflicting_label_count": counts_by_type.get("conflicting_label", 0),
        "missing_referenced_sheet_count": counts_by_type.get(
            "missing_referenced_sheet", 0
        ),
        "missing_plan_reference_count": counts_by_type.get(
            "missing_plan_reference", 0
        ),
        "unclear_revision_count": counts_by_type.get("unclear_revision", 0),
        "requires_human_review_count": counts_by_type.get(
            "requires_human_review", 0
        ),
        "findings_requiring_human_review": len(
            [f for f in findings if f.status == "requires_human_review"]
        ),
    }
