"""Read operations for projects."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import models


def list_projects(db: Session) -> list[models.Project]:
    return list(db.scalars(select(models.Project)).all())


def get_project(db: Session, project_id: str) -> models.Project | None:
    return db.get(models.Project, project_id)
