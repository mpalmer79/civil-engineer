"""PDF page indexing and evidence citation API routes (Sprint 2).

These endpoints index an uploaded PDF into page-level review records, read those
pages, and let a human reviewer create page-level evidence citations for a
finding. Indexing is deterministic and local; it does not OCR, call external
services, approve plans, certify compliance, verify CAD, validate design, or
make a final engineering decision. A citation is a reviewer-selected source
reference, not proof of correctness, and never changes a finding to a final
outcome.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db import models
from app.db.database import get_db
from app.schemas.pdf_evidence import (
    DocumentIndexingSummary,
    DocumentPageResponse,
    EvidenceCitationCreate,
    EvidenceCitationResponse,
    EvidenceCitationUpdate,
)
from app.services import pdf_indexing_service
from app.services.access_control_service import (
    get_optional_user,
    require_project_read,
    require_project_reviewer,
)
from app.services.pdf_indexing_service import PdfIndexingError

router = APIRouter(tags=["pdf-evidence"])


def _handle(exc: Exception) -> HTTPException:
    status_code = getattr(exc, "status_code", 422)
    message = getattr(exc, "message", str(exc))
    return HTTPException(status_code=status_code, detail=message)


@router.post(
    "/projects/{project_id}/documents/{document_id}/index-pdf",
    response_model=DocumentIndexingSummary,
)
def index_pdf(
    project_id: str,
    document_id: str,
    user: models.UserAccount | None = Depends(get_optional_user),
    db: Session = Depends(get_db),
) -> DocumentIndexingSummary:
    actor = require_project_reviewer(db, project_id, user)
    try:
        result = pdf_indexing_service.index_pdf_document(
            db,
            project_id=project_id,
            document_id=document_id,
            actor_name=actor.display_name,
        )
    except (PdfIndexingError, ValueError) as exc:
        raise _handle(exc) from exc
    return DocumentIndexingSummary.model_validate(result)


@router.get(
    "/projects/{project_id}/documents/{document_id}/pages",
    response_model=list[DocumentPageResponse],
)
def list_pages(
    project_id: str,
    document_id: str,
    user: models.UserAccount | None = Depends(get_optional_user),
    db: Session = Depends(get_db),
) -> list[DocumentPageResponse]:
    require_project_read(db, project_id, user)
    try:
        return pdf_indexing_service.list_document_pages(
            db, project_id, document_id
        )
    except (PdfIndexingError, ValueError) as exc:
        raise _handle(exc) from exc


@router.get(
    "/projects/{project_id}/documents/{document_id}/pages/{page_number}",
    response_model=DocumentPageResponse,
)
def get_page(
    project_id: str,
    document_id: str,
    page_number: int,
    user: models.UserAccount | None = Depends(get_optional_user),
    db: Session = Depends(get_db),
) -> DocumentPageResponse:
    require_project_read(db, project_id, user)
    try:
        page = pdf_indexing_service.get_document_page(
            db, project_id, document_id, page_number
        )
    except (PdfIndexingError, ValueError) as exc:
        raise _handle(exc) from exc
    if page is None:
        raise HTTPException(status_code=404, detail="Document page not found")
    return page


@router.get(
    "/projects/{project_id}/findings/{finding_id}/citations",
    response_model=list[EvidenceCitationResponse],
)
def list_finding_citations(
    project_id: str,
    finding_id: str,
    user: models.UserAccount | None = Depends(get_optional_user),
    db: Session = Depends(get_db),
) -> list[EvidenceCitationResponse]:
    require_project_read(db, project_id, user)
    return pdf_indexing_service.list_finding_citations(
        db, project_id, finding_id
    )


@router.post(
    "/projects/{project_id}/findings/{finding_id}/citations",
    response_model=EvidenceCitationResponse,
    status_code=201,
)
def create_citation(
    project_id: str,
    finding_id: str,
    body: EvidenceCitationCreate,
    user: models.UserAccount | None = Depends(get_optional_user),
    db: Session = Depends(get_db),
) -> EvidenceCitationResponse:
    actor = require_project_reviewer(db, project_id, user)
    try:
        return pdf_indexing_service.create_evidence_citation(
            db,
            project_id=project_id,
            finding_id=finding_id,
            document_id=body.document_id,
            document_page_id=body.document_page_id,
            page_number=body.page_number,
            section_label=body.section_label,
            quoted_excerpt=body.quoted_excerpt,
            reviewer_note=body.reviewer_note,
            citation_type=body.citation_type,
            citation_status=body.citation_status,
            created_by_name=actor.display_name,
        )
    except (PdfIndexingError, ValueError) as exc:
        raise _handle(exc) from exc


@router.get(
    "/projects/{project_id}/evidence-citations",
    response_model=list[EvidenceCitationResponse],
)
def list_project_citations(
    project_id: str,
    user: models.UserAccount | None = Depends(get_optional_user),
    db: Session = Depends(get_db),
) -> list[EvidenceCitationResponse]:
    require_project_read(db, project_id, user)
    return pdf_indexing_service.list_project_citations(db, project_id)


@router.patch(
    "/projects/{project_id}/findings/{finding_id}/citations/{citation_id}",
    response_model=EvidenceCitationResponse,
)
def update_citation(
    project_id: str,
    finding_id: str,
    citation_id: str,
    body: EvidenceCitationUpdate,
    user: models.UserAccount | None = Depends(get_optional_user),
    db: Session = Depends(get_db),
) -> EvidenceCitationResponse:
    require_project_reviewer(db, project_id, user)
    try:
        return pdf_indexing_service.update_evidence_citation(
            db,
            project_id=project_id,
            finding_id=finding_id,
            citation_id=citation_id,
            section_label=body.section_label,
            quoted_excerpt=body.quoted_excerpt,
            reviewer_note=body.reviewer_note,
            citation_status=body.citation_status,
            citation_type=body.citation_type,
        )
    except (PdfIndexingError, ValueError) as exc:
        raise _handle(exc) from exc


@router.delete(
    "/projects/{project_id}/findings/{finding_id}/citations/{citation_id}",
)
def delete_citation(
    project_id: str,
    finding_id: str,
    citation_id: str,
    user: models.UserAccount | None = Depends(get_optional_user),
    db: Session = Depends(get_db),
) -> dict[str, str | bool]:
    require_project_reviewer(db, project_id, user)
    try:
        pdf_indexing_service.delete_evidence_citation(
            db,
            project_id=project_id,
            finding_id=finding_id,
            citation_id=citation_id,
        )
    except (PdfIndexingError, ValueError) as exc:
        raise _handle(exc) from exc
    return {"deleted": True, "evidence_citation_id": citation_id}
