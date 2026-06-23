"""Plan consistency service.

Evaluates the seeded plan sheets, plan references, and CAD-aware metadata for a
project and generates plan-sheet-specific review-support findings: missing
referenced sheets, conflicting labels, missing plan references, CAD metadata
gaps, and unclear revisions. The logic is intentionally simple and explainable.

This is not final design validation and it does not approve, certify, or verify
any CAD drawing. Every generated finding requires human review.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.safety import find_prohibited_language
from app.db import models

# Plan reference consistency statuses that indicate a review-support issue.
_ISSUE_STATUSES = {
    "missing_target",
    "conflicting_label",
    "unclear",
    "needs_human_review",
}


class PlanConsistencyError(Exception):
    """Raised when a plan consistency check cannot be performed."""

    def __init__(self, message: str, *, status_code: int = 400) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code


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
    stmt = (
        select(models.PlanReference)
        .where(models.PlanReference.project_id == project_id)
        .order_by(models.PlanReference.plan_reference_id)
    )
    return list(db.scalars(stmt).all())


def list_inconsistent_references(
    db: Session, project_id: str
) -> list[models.PlanReference]:
    return [
        r
        for r in list_plan_references(db, project_id)
        if r.consistency_status in _ISSUE_STATUSES
    ]


def list_plan_consistency_findings(
    db: Session, project_id: str
) -> list[models.PlanConsistencyFinding]:
    stmt = (
        select(models.PlanConsistencyFinding)
        .where(models.PlanConsistencyFinding.project_id == project_id)
        .order_by(models.PlanConsistencyFinding.plan_finding_id)
    )
    return list(db.scalars(stmt).all())


def get_plan_consistency_finding(
    db: Session, plan_finding_id: str
) -> models.PlanConsistencyFinding | None:
    return db.scalars(
        select(models.PlanConsistencyFinding).where(
            models.PlanConsistencyFinding.plan_finding_id == plan_finding_id
        )
    ).first()


def plan_consistency_summary(db: Session, project_id: str) -> dict:
    findings = list_plan_consistency_findings(db, project_id)
    by_type: dict[str, int] = {}
    for f in findings:
        by_type[f.finding_type] = by_type.get(f.finding_type, 0) + 1
    references = list_plan_references(db, project_id)
    needs_review_refs = [
        r for r in references if r.consistency_status in _ISSUE_STATUSES
    ]
    cad_count = (
        db.query(models.CADMetadata)
        .filter(models.CADMetadata.project_id == project_id)
        .count()
    )
    return {
        "project_id": project_id,
        "total_findings": len(findings),
        "missing_sheet_count": by_type.get("missing_referenced_sheet", 0)
        + by_type.get("missing_sheet", 0),
        "conflicting_label_count": by_type.get("conflicting_label", 0),
        "cad_metadata_records": cad_count,
        "plan_references_requiring_human_review": len(needs_review_refs),
        "findings_by_type": by_type,
    }


def _recommended_action(finding_type: str, label: str) -> str:
    actions = {
        "missing_referenced_sheet": (
            f"Request the referenced sheet {label} or confirm it was submitted "
            "separately."
        ),
        "conflicting_label": (
            "Request consistent basin naming across the plan set and report."
        ),
        "missing_plan_reference": (
            "Request the missing reference or response and confirm the plan "
            "sheet depiction."
        ),
        "cad_metadata_gap": (
            "Confirm the corrective action is shown on a current plan sheet or "
            "request an updated sheet."
        ),
        "unclear_revision": (
            "Request clarified construction sequence notes on the referenced "
            "sheet."
        ),
        "requires_human_review": (
            "Confirm the responsible party and request supporting plan sheet "
            "notes."
        ),
    }
    return actions.get(
        finding_type, "Route to a human reviewer for confirmation."
    )


def _compute_findings(
    project_id: str,
    sheets: list[models.PlanSheet],
    cad: list[models.CADMetadata],
    references: list[models.PlanReference],
) -> list[dict]:
    """Derive plan consistency findings from the seeded data.

    The rules are explainable: missing or referenced-not-included sheets, a
    basin naming conflict across the plan set and report, and each remaining
    inconsistent plan reference become one review-support finding.
    """

    findings: list[dict] = []

    # Rule 1: referenced-not-included or missing sheets.
    for sheet in sheets:
        if sheet.status in {"missing", "referenced_not_included"}:
            findings.append(
                {
                    "finding_type": "missing_referenced_sheet",
                    "title": (
                        f"Referenced plan sheet {sheet.sheet_number} is not "
                        "included"
                    ),
                    "summary": (
                        f"Based on plan sheet metadata, plan sheet "
                        f"{sheet.sheet_number} ({sheet.sheet_title}) is "
                        "referenced but not included in the submitted package. "
                        "This is a potential issue that requires reviewer "
                        "confirmation."
                    ),
                    "risk_level": "high",
                    "related_sheet_ids": [sheet.sheet_id],
                    "related_document_ids": list(sheet.related_documents or []),
                    "related_checklist_items": list(
                        sheet.related_checklist_items or []
                    ),
                    "related_cad_metadata_ids": [],
                    "recommended_human_action": _recommended_action(
                        "missing_referenced_sheet", sheet.sheet_number
                    ),
                }
            )

    # Rule 2: basin naming conflict across the plan set and report.
    basins = [c for c in cad if c.entity_type == "basin"]
    basin_labels = {c.entity_label for c in basins}
    if {"Basin A", "Basin 1"} <= basin_labels:
        conflict = [c for c in basins if c.entity_label in {"Basin A", "Basin 1"}]
        sheet_ids = sorted({c.sheet_id for c in conflict if c.sheet_id})
        doc_ids = sorted(
            {c.related_document_id for c in conflict if c.related_document_id}
        )
        checklist = sorted(
            {
                c.related_checklist_item_id
                for c in conflict
                if c.related_checklist_item_id
            }
        )
        findings.append(
            {
                "finding_type": "conflicting_label",
                "title": "Basin naming conflict between Basin A and Basin 1",
                "summary": (
                    "Based on plan sheet metadata, the same basin is labeled "
                    "Basin A on the grading and drainage plan and Basin 1 in "
                    "the stormwater report. This is conflicting information "
                    "that requires reviewer confirmation."
                ),
                "risk_level": "medium",
                "related_sheet_ids": sheet_ids,
                "related_document_ids": doc_ids,
                "related_checklist_items": checklist,
                "related_cad_metadata_ids": [c.cad_metadata_id for c in conflict],
                "recommended_human_action": _recommended_action(
                    "conflicting_label", ""
                ),
            }
        )

    # Rule 3: each remaining inconsistent plan reference becomes one finding.
    cad_by_id = {c.cad_metadata_id: c for c in cad}
    for ref in references:
        cs = ref.consistency_status
        if cs not in _ISSUE_STATUSES:
            continue
        # Missing sheet targets are handled by Rule 1, basin conflicts by Rule 2.
        if cs == "missing_target" and ref.target_type == "plan_sheet":
            continue
        if cs == "conflicting_label":
            continue

        if cs == "missing_target":
            ftype, risk = "missing_plan_reference", "medium"
        elif cs == "unclear":
            ftype, risk = "unclear_revision", "medium"
        elif cs == "needs_human_review":
            note = (ref.review_note or "").lower()
            if "corrective action" in note:
                ftype, risk = "cad_metadata_gap", "medium"
            else:
                ftype, risk = "requires_human_review", "high"
        else:
            ftype, risk = "requires_human_review", "medium"

        related_sheet_ids: list[str] = []
        related_cad_ids: list[str] = []
        related_doc_ids: list[str] = []
        related_checklist: list[str] = []

        for kind, ident in (
            (ref.source_type, ref.source_id),
            (ref.target_type, ref.target_id),
        ):
            if kind == "plan_sheet":
                related_sheet_ids.append(ident)
            elif kind == "cad_feature":
                related_cad_ids.append(ident)
                meta = cad_by_id.get(ident)
                if meta:
                    if meta.sheet_id:
                        related_sheet_ids.append(meta.sheet_id)
                    if meta.related_checklist_item_id:
                        related_checklist.append(meta.related_checklist_item_id)
            elif kind == "document":
                related_doc_ids.append(ident)

        findings.append(
            {
                "finding_type": ftype,
                "title": ref.reference_label,
                "summary": (
                    "Based on plan sheet metadata, "
                    f"{(ref.review_note or '').rstrip('.')}. "
                    f"{ref.reference_context or ''}".strip()
                ),
                "risk_level": risk,
                "related_sheet_ids": sorted(set(related_sheet_ids)),
                "related_document_ids": sorted(set(related_doc_ids)),
                "related_checklist_items": sorted(set(related_checklist)),
                "related_cad_metadata_ids": sorted(set(related_cad_ids)),
                "recommended_human_action": _recommended_action(
                    ftype, ref.reference_label
                ),
            }
        )

    return findings


def run_consistency_check(
    db: Session, project_id: str
) -> list[models.PlanConsistencyFinding]:
    """Run the plan consistency check and persist the resulting findings.

    Idempotent: existing plan consistency findings for the project are cleared
    and regenerated so the check can be run repeatedly. Writes audit events at
    each step.
    """

    if db.get(models.Project, project_id) is None:
        raise PlanConsistencyError("Project not found.", status_code=404)

    _audit(
        db,
        project_id=project_id,
        event_type="plan_consistency_check_started",
        related_entity_type="project",
        related_entity_id=project_id,
        description="Plan consistency check started over seeded plan metadata.",
    )

    sheets = list(
        db.scalars(
            select(models.PlanSheet).where(
                models.PlanSheet.project_id == project_id
            )
        ).all()
    )
    if not sheets:
        _audit(
            db,
            project_id=project_id,
            event_type="plan_consistency_check_failed",
            related_entity_type="project",
            related_entity_id=project_id,
            description="Plan consistency check could not run: no plan sheets.",
        )
        db.commit()
        raise PlanConsistencyError(
            "No plan sheets exist for this project.", status_code=409
        )

    _audit(
        db,
        project_id=project_id,
        event_type="plan_sheet_index_loaded",
        related_entity_type="project",
        related_entity_id=project_id,
        description=f"Loaded {len(sheets)} plan sheets for the consistency check.",
        metadata={"sheet_count": len(sheets)},
    )

    cad = list(
        db.scalars(
            select(models.CADMetadata).where(
                models.CADMetadata.project_id == project_id
            )
        ).all()
    )
    _audit(
        db,
        project_id=project_id,
        event_type="cad_metadata_loaded",
        related_entity_type="project",
        related_entity_id=project_id,
        description=f"Loaded {len(cad)} CAD-aware metadata records.",
        metadata={"cad_metadata_count": len(cad)},
    )

    references = list_plan_references(db, project_id)
    for ref in references:
        _audit(
            db,
            project_id=project_id,
            event_type="plan_reference_evaluated",
            related_entity_type="plan_reference",
            related_entity_id=ref.plan_reference_id,
            description=(
                f"Evaluated plan reference {ref.reference_label}: "
                f"{ref.consistency_status}."
            ),
            metadata={
                "reference_id": ref.plan_reference_id,
                "consistency_status": ref.consistency_status,
                "source_id": ref.source_id,
                "target_id": ref.target_id,
            },
        )

    # Clear and regenerate findings so the check is idempotent.
    db.query(models.PlanConsistencyFinding).filter(
        models.PlanConsistencyFinding.project_id == project_id
    ).delete()

    computed = _compute_findings(project_id, sheets, cad, references)
    created: list[models.PlanConsistencyFinding] = []
    for spec in computed:
        plan_finding_id = f"planf_{uuid.uuid4().hex[:12]}"
        record = models.PlanConsistencyFinding(
            plan_finding_id=plan_finding_id,
            project_id=project_id,
            finding_type=spec["finding_type"],
            title=spec["title"],
            summary=spec["summary"],
            risk_level=spec["risk_level"],
            status="requires_human_review",
            related_sheet_ids=spec["related_sheet_ids"],
            related_document_ids=spec["related_document_ids"],
            related_checklist_items=spec["related_checklist_items"],
            related_cad_metadata_ids=spec["related_cad_metadata_ids"],
            recommended_human_action=spec["recommended_human_action"],
        )
        db.add(record)
        created.append(record)
        _audit(
            db,
            project_id=project_id,
            event_type="plan_consistency_finding_created",
            related_entity_type="plan_consistency_finding",
            related_entity_id=plan_finding_id,
            description=(
                f"Plan consistency finding created: {spec['finding_type']}."
            ),
            metadata={
                "plan_finding_id": plan_finding_id,
                "finding_type": spec["finding_type"],
                "related_sheet_ids": spec["related_sheet_ids"],
                "related_cad_metadata_ids": spec["related_cad_metadata_ids"],
            },
        )

    _audit(
        db,
        project_id=project_id,
        event_type="plan_consistency_check_completed",
        related_entity_type="project",
        related_entity_id=project_id,
        description=(
            f"Plan consistency check completed: {len(created)} review-support "
            "findings created. All findings require human review."
        ),
        metadata={
            "findings_created": len(created),
            "sheet_count": len(sheets),
            "cad_metadata_count": len(cad),
            "reference_count": len(references),
        },
    )

    db.commit()
    for record in created:
        db.refresh(record)

    # Defensive safety check: no generated finding text may contain prohibited
    # final-decision language.
    for record in created:
        for text in (record.title, record.summary, record.recommended_human_action):
            if find_prohibited_language(text):
                raise PlanConsistencyError(
                    "Generated plan finding contained prohibited wording.",
                    status_code=500,
                )

    return created


def ensure_findings(db: Session, project_id: str) -> None:
    """Generate plan consistency findings once if none exist for the project.

    Used at startup so the read endpoints and frontend have findings without a
    manual check. It is gated on the findings being empty, so it does not write
    duplicate audit events on every restart.
    """

    if db.get(models.Project, project_id) is None:
        return
    existing = (
        db.query(models.PlanConsistencyFinding)
        .filter(models.PlanConsistencyFinding.project_id == project_id)
        .first()
    )
    if existing is None:
        run_consistency_check(db, project_id)
