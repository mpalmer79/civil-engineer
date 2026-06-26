"""Finding API routes.

Lists seeded demo findings and real reviewer-created findings, creates
reviewer-owned review-support findings, and attaches basic manual evidence
references. Every finding stays under human review. No route approves,
certifies, verifies, validates, resolves, or closes anything, and there is no
action called approve.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.schemas.evidence import EvidenceReferenceCreate, FindingSourceRead
from app.schemas.finding import FindingCreate, FindingRead
from app.services import finding_service, project_service, real_intake_service
from app.services.real_intake_service import IntakeError

router = APIRouter(tags=["findings"])


@router.get(
    "/projects/{project_id}/findings", response_model=list[FindingRead]
)
def list_findings(
    project_id: str, db: Session = Depends(get_db)
) -> list[FindingRead]:
    if project_service.get_project(db, project_id) is None:
        raise HTTPException(status_code=404, detail="Project not found")
    return finding_service.list_findings(db, project_id)


@router.post(
    "/projects/{project_id}/findings",
    response_model=FindingRead,
    status_code=201,
)
def create_finding(
    project_id: str,
    body: FindingCreate,
    db: Session = Depends(get_db),
) -> FindingRead:
    try:
        return real_intake_service.create_finding(
            db,
            project_id=project_id,
            title=body.title,
            category=body.category,
            risk_level=body.risk_level,
            evidence_status=body.evidence_status,
            evidence_to_find=body.evidence_to_find,
            reason_it_matters=body.reason_it_matters,
            recommended_human_action=body.recommended_human_action,
            related_documents=body.related_documents,
            related_checklist_items=body.related_checklist_items,
            reviewer_notes=body.reviewer_notes,
            human_review_status=body.human_review_status,
            created_by_name=body.created_by_name,
        )
    except (IntakeError, ValueError) as exc:
        status_code = getattr(exc, "status_code", 422)
        message = getattr(exc, "message", str(exc))
        raise HTTPException(status_code=status_code, detail=message) from exc


@router.get("/findings/{finding_id}", response_model=FindingRead)
def get_finding(finding_id: str, db: Session = Depends(get_db)) -> FindingRead:
    finding = finding_service.get_finding(db, finding_id)
    if finding is None:
        raise HTTPException(status_code=404, detail="Finding not found")
    return finding


@router.get(
    "/findings/{finding_id}/evidence-references",
    response_model=list[FindingSourceRead],
)
def list_evidence_references(
    finding_id: str, db: Session = Depends(get_db)
) -> list[FindingSourceRead]:
    if finding_service.get_finding(db, finding_id) is None:
        raise HTTPException(status_code=404, detail="Finding not found")
    return real_intake_service.list_evidence_references(db, finding_id)


@router.post(
    "/findings/{finding_id}/evidence-references",
    response_model=FindingSourceRead,
    status_code=201,
)
def create_evidence_reference(
    finding_id: str,
    body: EvidenceReferenceCreate,
    db: Session = Depends(get_db),
) -> FindingSourceRead:
    try:
        return real_intake_service.create_evidence_reference(
            db,
            finding_id=finding_id,
            document_id=body.document_id,
            reviewer_note=body.reviewer_note,
            page_number=body.page_number,
            sheet_number=body.sheet_number,
            section_label=body.section_label,
            created_by_name=body.created_by_name,
        )
    except (IntakeError, ValueError) as exc:
        status_code = getattr(exc, "status_code", 422)
        message = getattr(exc, "message", str(exc))
        raise HTTPException(status_code=status_code, detail=message) from exc
