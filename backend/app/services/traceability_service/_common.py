"""Shared constants and private helpers for the traceability service."""

from __future__ import annotations

import hashlib
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import models

# A traceability row may relate to several review packets. The response keeps the
# inline packet context list bounded so it does not grow without limit; the full
# count is always reported alongside it.
MAX_PACKET_CONTEXTS = 3

LIMITATIONS_NOTE = (
    "Review-support traceability. This view organizes existing links between "
    "checklist items, evidence, findings, workflow items, and review packets. It "
    "does not determine whether a requirement is satisfied and makes no final "
    "engineering decision. Reviewer confirmation is required. A missing link is "
    "not a final finding about the project; it may mean no linked evidence yet, "
    "not reviewed yet, or not enough indexed information."
)

# A checklist item is treated as reviewer-handled once it reaches the handoff
# state. Every other review status (including not_started) is "not reviewed yet".
_CHECKLIST_REVIEWED = {"ready_for_reviewer_handoff"}

# Evidence link / citation statuses that still need reviewer confirmation.
_LINK_NEEDS_CONFIRM = {"needs_reviewer_confirmation", "citation_candidate"}


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _document_map(db: Session, project_id: str) -> dict[str, models.Document]:
    stmt = select(models.Document).where(models.Document.project_id == project_id)
    return {doc.document_id: doc for doc in db.scalars(stmt).all()}


def _document_name(documents: dict, document_id: str | None) -> str | None:
    if not document_id:
        return None
    doc = documents.get(document_id)
    if doc is None:
        return None
    return doc.original_file_name or doc.file_name


def _has_indexed_pages(db: Session, project_id: str) -> bool:
    count = db.scalar(
        select(models.DocumentPage)
        .where(
            models.DocumentPage.project_id == project_id,
            models.DocumentPage.text_extraction_status == "text_extracted",
        )
        .limit(1)
    )
    return count is not None


def _workflow_items_by_finding(
    db: Session, project_id: str
) -> dict[str, list[models.WorkflowItem]]:
    """Map finding_id to workflow items whose source is that finding."""

    stmt = select(models.WorkflowItem).where(
        models.WorkflowItem.project_id == project_id
    )
    mapping: dict[str, list[models.WorkflowItem]] = {}
    for item in db.scalars(stmt).all():
        if item.source_id and "finding" in (item.source_type or ""):
            mapping.setdefault(item.source_id, []).append(item)
    return mapping


def _source_links(
    project_id: str,
    *,
    document_id: str | None = None,
    finding_id: str | None = None,
    workflow_item_id: str | None = None,
    review_packet_id: str | None = None,
    plan_sheet_id: str | None = None,
    has_workflow: bool = False,
) -> list[dict]:
    """Return typed source link hints. The frontend resolves these to routes and
    renders a source-link-unavailable chip when no route exists."""

    links: list[dict] = []
    if document_id:
        links.append({"type": "document", "id": document_id})
    if finding_id:
        links.append({"type": "finding", "id": finding_id})
    if workflow_item_id or has_workflow:
        links.append({"type": "workflow_board", "id": workflow_item_id})
    if review_packet_id:
        links.append({"type": "review_packet", "id": review_packet_id})
    if plan_sheet_id:
        links.append({"type": "plan_sheet", "id": plan_sheet_id})
    return links


def build_row_key(
    *,
    checklist_item_id: str | None,
    evidence_citation_id: str | None = None,
    evidence_candidate_id: str | None = None,
    finding_id: str | None = None,
    relationship_type: str,
    relationship_source: str,
) -> str:
    """Return a stable, URL-safe key for a traceability row.

    The key is a deterministic hash of the row's existing entity IDs and its
    relationship. It is stable across requests and across review packet
    regeneration because it deliberately excludes the positional row id and the
    regenerated workflow/packet item ids. It identifies the same checklist
    requirement plus evidence linkage so a reviewer's review action stays attached
    to that linkage.
    """

    canonical = "|".join(
        [
            f"ci={checklist_item_id or ''}",
            f"cit={evidence_citation_id or ''}",
            f"cand={evidence_candidate_id or ''}",
            f"find={finding_id or ''}",
            f"rel={relationship_type}",
            f"src={relationship_source}",
        ]
    )
    digest = hashlib.sha256(canonical.encode("utf-8")).hexdigest()[:24]
    return f"trk_{digest}"
