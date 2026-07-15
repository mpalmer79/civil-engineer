"""Read-only projections over review packet context and recorded review actions."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import models


def _packet_context_index(
    db: Session, project_id: str
) -> tuple[dict[str, list[dict]], dict[str, list[dict]]]:
    """Build (by_finding, by_checklist) maps of source id -> packet context dicts.

    Packet context is read from existing review packet items and their evidence
    links only. A packet item whose source is a finding maps to that finding; an
    evidence link to a checklist item or finding maps to that source. Nothing here
    is created or mutated.
    """

    packets = {
        p.packet_id: p
        for p in db.scalars(
            select(models.ReviewPacket).where(
                models.ReviewPacket.project_id == project_id
            )
        ).all()
    }
    if not packets:
        return {}, {}

    packet_ids = list(packets.keys())
    sections = {
        s.section_id: s
        for s in db.scalars(
            select(models.ReviewPacketSection).where(
                models.ReviewPacketSection.packet_id.in_(packet_ids)
            )
        ).all()
    }
    items = list(
        db.scalars(
            select(models.ReviewPacketItem)
            .where(models.ReviewPacketItem.packet_id.in_(packet_ids))
            .order_by(models.ReviewPacketItem.display_order)
        ).all()
    )
    item_by_id = {i.item_id: i for i in items}
    links = list(
        db.scalars(
            select(models.ReviewPacketEvidenceLink).where(
                models.ReviewPacketEvidenceLink.packet_id.in_(packet_ids)
            )
        ).all()
    )

    def _ctx(item: models.ReviewPacketItem, relationship: str) -> dict:
        packet = packets.get(item.packet_id)
        section = sections.get(item.section_id)
        return {
            "review_packet_id": item.packet_id,
            "review_packet_title": packet.title if packet else None,
            "review_packet_item_id": item.item_id,
            "review_packet_section_id": item.section_id,
            "review_packet_section_title": section.title if section else None,
            "packet_item_status": item.reviewer_status,
            "packet_item_source": item.source_type,
            "packet_traceability_relationship": relationship,
            "packet_source_link": {"type": "review_packet", "id": item.packet_id},
        }

    by_finding: dict[str, list[dict]] = {}
    by_checklist: dict[str, list[dict]] = {}
    for item in items:
        if item.source_type == "finding" and item.source_id:
            by_finding.setdefault(item.source_id, []).append(
                _ctx(item, "packet_item_source")
            )
    for link in links:
        item = item_by_id.get(link.item_id)
        if item is None:
            continue
        if link.evidence_type == "checklist_item":
            by_checklist.setdefault(link.evidence_id, []).append(
                _ctx(item, link.relationship)
            )
        elif link.evidence_type == "finding":
            by_finding.setdefault(link.evidence_id, []).append(
                _ctx(item, link.relationship)
            )
    return by_finding, by_checklist


def _contexts_for_item(
    by_finding: dict[str, list[dict]],
    by_checklist: dict[str, list[dict]],
    checklist_item_id: str | None,
    finding_id: str | None,
) -> list[dict]:
    """Return de-duplicated packet contexts for a checklist item, by packet item."""

    seen: set[str] = set()
    out: list[dict] = []
    candidates = list(by_checklist.get(checklist_item_id or "", []))
    if finding_id:
        candidates.extend(by_finding.get(finding_id, []))
    for ctx in candidates:
        item_id = ctx["review_packet_item_id"]
        if item_id in seen:
            continue
        seen.add(item_id)
        out.append(ctx)
    return out


def _latest_actions_by_key(
    db: Session, project_id: str
) -> dict[str, models.TraceabilityReviewAction]:
    """Map traceability_row_key -> the most recent recorded review action."""

    actions = db.scalars(
        select(models.TraceabilityReviewAction)
        .where(models.TraceabilityReviewAction.project_id == project_id)
        .order_by(models.TraceabilityReviewAction.created_at)
    ).all()
    latest: dict[str, models.TraceabilityReviewAction] = {}
    for action in actions:
        latest[action.traceability_row_key] = action
    return latest


def _action_dict(action: models.TraceabilityReviewAction | None) -> dict | None:
    if action is None:
        return None
    return {
        "action_id": action.action_id,
        "action_type": action.action_type,
        "reviewer_note": action.reviewer_note,
        "created_by": action.created_by,
        "created_at": action.created_at,
    }


HANDOFF_READINESS_NOTE = (
    "Handoff readiness signals. These counts organize review-support work and "
    "items needing reviewer attention. They do not determine whether a "
    "requirement is satisfied and are not a final engineering decision. Links "
    "reviewed by a reviewer are confirmed useful for review only."
)

# Latest review actions that mark a row as reviewer-handled for handoff readiness.
_READY_ACTIONS = {"reviewer_confirmed_link", "not_applicable"}


def _build_handoff_readiness(rows: list[dict]) -> dict:
    """Compute read-only handoff readiness signals from enriched rows.

    This is a readiness checklist, not a final decision. No count here means a
    requirement is satisfied, approved, or compliant.
    """

    def _action_type(row: dict) -> str | None:
        action = row.get("latest_review_action")
        return action.get("action_type") if action else None

    linked = sum(
        1 for r in rows if r["relationship_type"] != "no_linked_evidence_yet"
    )
    return {
        "total_traceability_rows": len(rows),
        "rows_with_linked_evidence": linked,
        "rows_without_linked_evidence": len(rows) - linked,
        "rows_with_reviewer_action": sum(
            1 for r in rows if r.get("latest_review_action")
        ),
        "rows_needing_more_information": sum(
            1 for r in rows if _action_type(r) == "needs_more_information"
        ),
        "rows_follow_up_needed": sum(
            1 for r in rows if _action_type(r) == "follow_up_needed"
        ),
        "rows_not_in_packet": sum(
            1 for r in rows if r.get("packet_context_count", 0) == 0
        ),
        "packet_context_count": sum(
            r.get("packet_context_count", 0) for r in rows
        ),
        "ready_for_reviewer_handoff_count": sum(
            1 for r in rows if _action_type(r) in _READY_ACTIONS
        ),
        "note": HANDOFF_READINESS_NOTE,
    }
