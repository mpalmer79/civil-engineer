"""Document API routes."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.schemas.document import DocumentRead
from app.services import document_service, project_service

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


@router.get("/documents/{document_id}", response_model=DocumentRead)
def get_document(
    document_id: str, db: Session = Depends(get_db)
) -> DocumentRead:
    document = document_service.get_document(db, document_id)
    if document is None:
        raise HTTPException(status_code=404, detail="Document not found")
    return document
