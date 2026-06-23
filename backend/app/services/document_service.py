"""Read operations for documents."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import models


def list_documents(db: Session, project_id: str) -> list[models.Document]:
    stmt = (
        select(models.Document)
        .where(models.Document.project_id == project_id)
        .order_by(models.Document.document_id)
    )
    return list(db.scalars(stmt).all())


def get_document(db: Session, document_id: str) -> models.Document | None:
    return db.get(models.Document, document_id)
