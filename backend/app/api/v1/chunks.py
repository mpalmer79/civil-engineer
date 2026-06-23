"""Document chunk API routes."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.schemas.chunk import ChunkRead
from app.services import document_service, project_service, retrieval_service

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
