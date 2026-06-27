"""Document chunk API routes."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db import models
from app.db.database import get_db
from app.schemas.chunk import ChunkRead, DocumentChunkingSummary
from app.services import (
    document_service,
    page_chunking_service,
    project_service,
    retrieval_service,
)
from app.services.access_control_service import (
    get_optional_user,
    require_project_reviewer,
)
from app.services.page_chunking_service import ChunkingError

router = APIRouter(tags=["chunks"])


@router.get("/projects/{project_id}/chunks", response_model=list[ChunkRead])
def list_project_chunks(
    project_id: str, db: Session = Depends(get_db)
) -> list[ChunkRead]:
    if project_service.get_project(db, project_id) is None:
        raise HTTPException(status_code=404, detail="Project not found")
    return retrieval_service.list_project_chunks(db, project_id)


@router.get("/documents/{document_id}/chunks", response_model=list[ChunkRead])
def list_document_chunks(
    document_id: str, db: Session = Depends(get_db)
) -> list[ChunkRead]:
    if document_service.get_document(db, document_id) is None:
        raise HTTPException(status_code=404, detail="Document not found")
    return retrieval_service.list_document_chunks(db, document_id)


@router.get("/chunks/{chunk_id}", response_model=ChunkRead)
def get_chunk(chunk_id: str, db: Session = Depends(get_db)) -> ChunkRead:
    chunk = retrieval_service.get_chunk(db, chunk_id)
    if chunk is None:
        raise HTTPException(status_code=404, detail="Chunk not found")
    return chunk


@router.post(
    "/projects/{project_id}/documents/{document_id}/chunk-pages",
    response_model=DocumentChunkingSummary,
)
def rebuild_document_chunks(
    project_id: str,
    document_id: str,
    user: models.UserAccount | None = Depends(get_optional_user),
    db: Session = Depends(get_db),
) -> DocumentChunkingSummary:
    """Rebuild real-derived chunks for a document from its indexed page text.

    This reads the document's indexed page text and produces chunk records for
    reviewer support. It does not parse files, OCR, or finalize any review
    outcome. The operation is idempotent and never deletes seeded chunks.
    """

    actor = require_project_reviewer(db, project_id, user)
    try:
        result = page_chunking_service.rebuild_document_chunks(
            db,
            project_id=project_id,
            document_id=document_id,
            actor_name=actor.display_name,
        )
    except (ChunkingError, ValueError) as exc:
        status_code = getattr(exc, "status_code", 422)
        message = getattr(exc, "message", str(exc))
        raise HTTPException(status_code=status_code, detail=message) from exc
    return DocumentChunkingSummary.model_validate(result)
