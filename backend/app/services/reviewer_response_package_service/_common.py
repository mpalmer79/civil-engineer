"""Shared helpers for the reviewer response package service.

Kept private to the package. The public surface is re-exported from the package
__init__.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db import models
from app.services.auth_service import ActorContext

from .errors import ReviewerResponsePackageError


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _short() -> str:
    return uuid.uuid4().hex[:12]


def _actor_name(actor: ActorContext | None) -> str:
    return actor.display_name if actor else "Demo Reviewer"


def _require_project(db: Session, project_id: str) -> models.Project:
    project = db.get(models.Project, project_id)
    if project is None:
        raise ReviewerResponsePackageError("Project not found.", status_code=404)
    return project


def _require_package(
    db: Session, project_id: str, response_package_id: str
) -> models.ReviewerResponsePackage:
    package = db.get(models.ReviewerResponsePackage, response_package_id)
    if package is None or package.project_id != project_id:
        raise ReviewerResponsePackageError(
            "Response package not found.", status_code=404
        )
    return package


def _require_item(
    db: Session, project_id: str, response_package_item_id: str
) -> models.ReviewerResponsePackageItem:
    item = db.get(models.ReviewerResponsePackageItem, response_package_item_id)
    if item is None or item.project_id != project_id:
        raise ReviewerResponsePackageError(
            "Response package item not found.", status_code=404
        )
    return item


def _next_sort_order(db: Session, response_package_id: str) -> int:
    count = db.scalar(
        select(func.count())
        .select_from(models.ReviewerResponsePackageItem)
        .where(
            models.ReviewerResponsePackageItem.response_package_id
            == response_package_id
        )
    )
    return int(count or 0)
