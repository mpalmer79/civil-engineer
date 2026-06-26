"""Document API routes.

Lists seeded demo documents and real registered or uploaded documents, and
adds document registration and file upload for real project records. A document
processing status tracks intake handling only; no route approves, certifies,
verifies, or validates a document.
"""

from __future__ import annotations

from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    UploadFile,
)
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.schemas.document import DocumentRead, DocumentRegister
from app.services import document_service, project_service, real_intake_service
from app.services.real_intake_service import IntakeError

router = APIRouter(tags=["documents"])


@router.get(
    "/projects/{project_id}/documents", response_model=list[DocumentRead]
)
def list_documents(
    project_id: str, db: Session = Depends(get_db)
) -> list[DocumentRead]:
    if project_service.get_project(db, project_id) is None:
        raise HTTPException(status_code=404, detail="Project not found")
    return document_service.list_documents(db, project_id)


@router.post(
    "/projects/{project_id}/documents/register",
    response_model=DocumentRead,
    status_code=201,
)
def register_document(
    project_id: str,
    body: DocumentRegister,
    db: Session = Depends(get_db),
) -> DocumentRead:
    try:
        return real_intake_service.register_document(
            db,
            project_id=project_id,
            original_file_name=body.original_file_name,
            document_type=body.document_type,
            purpose=body.purpose,
            expected_key_information=body.expected_key_information,
            content_type=body.content_type,
            file_size_bytes=body.file_size_bytes,
            revision_label=body.revision_label,
            revision_date=body.revision_date,
            uploaded_by_name=body.uploaded_by_name,
        )
    except (IntakeError, ValueError) as exc:
        status_code = getattr(exc, "status_code", 422)
        message = getattr(exc, "message", str(exc))
        raise HTTPException(status_code=status_code, detail=message) from exc


@router.post(
    "/projects/{project_id}/documents/upload",
    response_model=DocumentRead,
    status_code=201,
)
async def upload_document(
    project_id: str,
    file: UploadFile = File(...),
    document_type: str = Form("other"),
    purpose: str = Form(""),
    revision_label: str = Form(""),
    uploaded_by_name: str = Form("Demo Reviewer"),
    db: Session = Depends(get_db),
) -> DocumentRead:
    content_bytes = await file.read()
    try:
        return real_intake_service.upload_document(
            db,
            project_id=project_id,
            original_file_name=file.filename,
            content_type=file.content_type,
            content_bytes=content_bytes,
            document_type=document_type,
            purpose=purpose or None,
            revision_label=revision_label or None,
            uploaded_by_name=uploaded_by_name,
        )
    except (IntakeError, ValueError) as exc:
        status_code = getattr(exc, "status_code", 422)
        message = getattr(exc, "message", str(exc))
        raise HTTPException(status_code=status_code, detail=message) from exc


@router.get("/documents/{document_id}", response_model=DocumentRead)
def get_document(
    document_id: str, db: Session = Depends(get_db)
) -> DocumentRead:
    document = document_service.get_document(db, document_id)
    if document is None:
        raise HTTPException(status_code=404, detail="Document not found")
    return document
