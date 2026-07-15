"""Shared private helpers for the evidence retrieval package.

These helpers are used by both the page-text search path and the real-derived
chunk search path: project lookup, tokenization, page and document lookups,
excerpt trimming, filter sanitization, retrieval-query recording, and the query
text builders for checklist items and findings. Nothing here approves plans,
certifies compliance, or reaches a final engineering decision; every result is a
candidate for reviewer review.
"""

from __future__ import annotations

import re

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import models
from app.services.evidence_retrieval_service.errors import (
    MIN_RETRIEVAL_QUERY_LENGTH,
    RetrievalError,
)
from app.services.real_intake_service import (
    DEMO_ACTOR_ID,
    _now,
    _short,
)

_EXCERPT_LIMIT = 240
_EXCERPT_WINDOW = 160


def _require_project(db: Session, project_id: str) -> models.Project:
    project = db.get(models.Project, project_id)
    if project is None:
        raise RetrievalError("Project not found.", status_code=404)
    return project


def _tokens(text: str) -> list[str]:
    """Return lowercased alphanumeric tokens of length >= the query minimum."""

    return [
        token
        for token in re.findall(r"[a-z0-9]+", text.lower())
        if len(token) >= MIN_RETRIEVAL_QUERY_LENGTH
    ]


def _indexed_pages(db: Session, project_id: str) -> list[models.DocumentPage]:
    """Return project pages that carry extractable text, in stable order."""

    stmt = (
        select(models.DocumentPage)
        .where(
            models.DocumentPage.project_id == project_id,
            models.DocumentPage.text_extraction_status == "text_extracted",
        )
        .order_by(
            models.DocumentPage.document_id,
            models.DocumentPage.page_number,
        )
    )
    return list(db.scalars(stmt).all())


def _document_map(db: Session, project_id: str) -> dict[str, models.Document]:
    stmt = select(models.Document).where(
        models.Document.project_id == project_id
    )
    return {doc.document_id: doc for doc in db.scalars(stmt).all()}


def _document_display_name(document: models.Document | None) -> str:
    if document is None:
        return "Unknown document"
    return document.original_file_name or document.file_name


def _excerpt_around(text: str, match_start: int) -> str:
    """Return a short excerpt centered on the first matched term.

    The excerpt is bounded well below the full page text so a search result
    never returns an entire page. Leading and trailing context is marked with
    an ellipsis when the page text extends beyond the window.
    """

    collapsed = " ".join(text.split())
    if len(collapsed) <= _EXCERPT_LIMIT:
        return collapsed
    # Recompute the match position in the whitespace-collapsed text. Falling
    # back to position 0 keeps the excerpt safe if the term is not found after
    # collapsing (for example when the match spanned a line break).
    start = max(match_start - _EXCERPT_WINDOW // 2, 0)
    snippet = collapsed[start : start + _EXCERPT_LIMIT].strip()
    prefix = "..." if start > 0 else ""
    suffix = "..." if start + _EXCERPT_LIMIT < len(collapsed) else ""
    return f"{prefix}{snippet}{suffix}"


def _safe_filter_metadata(filters: dict) -> dict:
    """Return a filter dict safe for audit metadata (no page text, no paths)."""

    allowed_keys = {
        "document_id",
        "document_type",
        "text_extraction_status",
        "page_min",
        "page_max",
        "checklist_item_id",
        "finding_id",
    }
    return {key: filters[key] for key in allowed_keys if filters.get(key) is not None}


def _record_retrieval_query(
    db: Session,
    *,
    project_id: str,
    query_text: str,
    query_type: str,
    filters: dict,
    result_count: int,
    related_checklist_item_id: str | None,
    related_finding_id: str | None,
    actor_name: str,
) -> models.RetrievalQuery:
    query = models.RetrievalQuery(
        retrieval_query_id=f"rq_user_{_short()}",
        project_id=project_id,
        query_text=query_text,
        query_type=query_type,
        filters=_safe_filter_metadata(filters),
        result_count=result_count,
        related_checklist_item_id=related_checklist_item_id,
        related_finding_id=related_finding_id,
        created_by_actor_id=DEMO_ACTOR_ID,
        created_by_name=actor_name,
        event_metadata={"query_type": query_type, "result_count": result_count},
        created_at=_now(),
    )
    db.add(query)
    db.flush()
    return query


def _checklist_query_text(item: models.ChecklistItem) -> str:
    """Build checklist query text from requirement and expected evidence, with a
    soft boost from supporting document hints."""

    parts = [item.requirement or "", item.expected_evidence or ""]
    supporting = item.supporting_documents or []
    if supporting:
        parts.append(" ".join(str(doc) for doc in supporting))
    return " ".join(part for part in parts if part).strip()


def _finding_query_text(finding: models.Finding) -> str:
    """Build finding query text from title, evidence to find, and why it
    matters."""

    parts = [
        finding.title or "",
        finding.evidence_to_find or "",
        finding.reason_it_matters or "",
    ]
    return " ".join(part for part in parts if part).strip()
