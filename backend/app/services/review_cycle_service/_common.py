"""Shared private helpers for the review cycle service.

These helpers are used by several review cycle submodules: timestamp and id
generation, audit event recording, project lookup, keyword and stem helpers for
deterministic matching, and access to the latest response package and its items.
No live AI calls and no vector search are used.
"""

from __future__ import annotations

import re
import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import models
from app.services.review_cycle_service.errors import ReviewCycleError

_STOPWORDS = {
    "the",
    "and",
    "for",
    "see",
    "with",
    "this",
    "that",
    "from",
    "per",
    "has",
    "have",
    "been",
    "will",
    "should",
    "needs",
    "need",
    "review",
    "reviewer",
    "plan",
    "sheet",
    "detail",
    "note",
    "item",
}


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _short() -> str:
    return uuid.uuid4().hex[:12]


def _audit(
    db: Session,
    *,
    project_id: str,
    event_type: str,
    related_entity_type: str,
    related_entity_id: str,
    description: str,
    actor_type: str = "reviewer",
    metadata: dict | None = None,
) -> None:
    db.add(
        models.AuditEvent(
            audit_event_id=f"audit_cycle_{uuid.uuid4().hex[:12]}",
            project_id=project_id,
            event_type=event_type,
            actor_type=actor_type,
            related_entity_type=related_entity_type,
            related_entity_id=related_entity_id,
            description=description,
            timestamp=_now(),
            event_metadata=metadata or {},
        )
    )


def _require_project(db: Session, project_id: str) -> None:
    if db.get(models.Project, project_id) is None:
        raise ReviewCycleError("Project not found.", status_code=404)


def _keywords(text: str | None) -> set[str]:
    if not text:
        return set()
    tokens = re.findall(r"[a-z0-9][a-z0-9\.\-/]*", text.lower())
    return {t for t in tokens if len(t) >= 3 and t not in _STOPWORDS}


def _stem(normalized: str) -> str:
    stem = re.sub(r"\b\d+\b", "", normalized)
    stem = re.sub(r"\s+", " ", stem).strip()
    return stem or normalized


def _latest_response_package(
    db: Session, project_id: str
) -> models.ResponsePackage | None:
    return db.scalars(
        select(models.ResponsePackage)
        .where(models.ResponsePackage.project_id == project_id)
        .order_by(models.ResponsePackage.created_at.desc())
    ).first()


def _response_package_items(db: Session, project_id: str) -> list:
    package = _latest_response_package(db, project_id)
    if package is None:
        return []
    return list(
        db.scalars(
            select(models.ResponsePackageItem).where(
                models.ResponsePackageItem.response_package_id
                == package.response_package_id
            )
        ).all()
    )
