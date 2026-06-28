"""Project-wide traceability aggregation and reviewer review actions (Phase 4A/4B).

This service aggregates relationships that already exist between project checklist
items, evidence links, citations, candidates, documents and pages, findings,
workflow items, and review packets. The aggregation (build_project_traceability)
is read-only: it organizes existing links, runs no analysis engine, calls no AI
provider, mutates no data, and never determines whether a requirement is
satisfied. Every row is review-support context that requires reviewer
confirmation.

Phase 4B adds reviewer-controlled review actions on a single traceability row.
Because traceability rows are computed and have no stable stored primary key, a
review action is keyed by a stable traceability_row_key derived from the row's
existing entity IDs (checklist item, evidence citation or candidate, finding, and
relationship), not by the positional row id. Recording an action is append-only:
it writes one TraceabilityReviewAction row and one audit event, and it never
mutates the checklist item, evidence, finding, workflow item, or packet the row
references. reviewer_confirmed_link means the reviewer confirmed the link is
useful for review only; it does not mean the requirement is satisfied, approved,
certified, verified, validated, or compliant.

The aggregation deliberately preserves four distinct states:

* no_linked_evidence_yet: the checklist item has no linked evidence, citation, or
  candidate. This is not a statement that the requirement is unsupported.
* not_enough_indexed_information: there is no linked evidence and the project has
  no indexed, searchable document pages yet.
* not_reviewed: linked evidence exists but the reviewer has not confirmed it.
* linked_evidence_exists: evidence is linked, still review-support only.
"""

from __future__ import annotations

import hashlib
import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.safety import (
    ALLOWED_TRACEABILITY_REVIEW_ACTIONS,
    find_prohibited_language,
)
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


def build_project_traceability(db: Session, project_id: str) -> dict | None:
    """Aggregate read-only project-wide traceability rows. Returns None when the
    project does not exist."""

    project = db.get(models.Project, project_id)
    if project is None:
        return None

    documents = _document_map(db, project_id)
    has_indexed = _has_indexed_pages(db, project_id)
    workflow_by_finding = _workflow_items_by_finding(db, project_id)

    checklist_items = list(
        db.scalars(
            select(models.ProjectChecklistItem)
            .where(models.ProjectChecklistItem.project_id == project_id)
            .order_by(models.ProjectChecklistItem.sort_order)
        ).all()
    )

    citations = list(
        db.scalars(
            select(models.EvidenceCitation).where(
                models.EvidenceCitation.project_id == project_id
            )
        ).all()
    )
    candidates = list(
        db.scalars(
            select(models.EvidenceCandidate).where(
                models.EvidenceCandidate.project_id == project_id
            )
        ).all()
    )
    links = list(
        db.scalars(
            select(models.ChecklistEvidenceLink).where(
                models.ChecklistEvidenceLink.project_id == project_id
            )
        ).all()
    )
    findings = {
        f.finding_id: f
        for f in db.scalars(
            select(models.Finding).where(models.Finding.project_id == project_id)
        ).all()
    }

    citations_by_item: dict[str, list[models.EvidenceCitation]] = {}
    for citation in citations:
        if citation.project_checklist_item_id:
            citations_by_item.setdefault(
                citation.project_checklist_item_id, []
            ).append(citation)
    candidates_by_item: dict[str, list[models.EvidenceCandidate]] = {}
    for candidate in candidates:
        if candidate.checklist_item_id:
            candidates_by_item.setdefault(
                candidate.checklist_item_id, []
            ).append(candidate)
    links_by_item: dict[str, list[models.ChecklistEvidenceLink]] = {}
    for link in links:
        links_by_item.setdefault(link.project_checklist_item_id, []).append(link)

    rows: list[dict] = []
    items_with_evidence = 0
    rows_requiring_confirmation = 0
    row_counter = 0

    def _next_row_id() -> str:
        nonlocal row_counter
        row_counter += 1
        return f"trace_{project_id}_{row_counter}"

    for item in checklist_items:
        finding = (
            findings.get(item.related_finding_id)
            if item.related_finding_id
            else None
        )
        finding_workflow = (
            workflow_by_finding.get(finding.finding_id, []) if finding else []
        )
        first_workflow = finding_workflow[0] if finding_workflow else None
        reviewed = item.review_status in _CHECKLIST_REVIEWED

        item_links = links_by_item.get(item.project_checklist_item_id, [])
        item_citations = citations_by_item.get(item.project_checklist_item_id, [])
        item_candidates = candidates_by_item.get(
            item.project_checklist_item_id, []
        )
        has_evidence = bool(item_links or item_citations or item_candidates)
        if has_evidence:
            items_with_evidence += 1

        base = {
            "checklist_item_id": item.project_checklist_item_id,
            "checklist_title": item.item_code,
            "checklist_requirement": item.requirement_text,
            "checklist_status": item.review_status,
            "finding_id": finding.finding_id if finding else None,
            "finding_title": finding.title if finding else None,
            "finding_status": finding.human_review_status if finding else None,
            "workflow_item_id": (
                first_workflow.workflow_item_id if first_workflow else None
            ),
            "workflow_item_title": (
                first_workflow.title if first_workflow else None
            ),
            "workflow_status": first_workflow.status if first_workflow else None,
            "review_packet_id": (
                first_workflow.packet_id if first_workflow else None
            ),
            "review_packet_item_id": (
                first_workflow.packet_item_id if first_workflow else None
            ),
            "cad_finding_id": None,
            "plan_finding_id": None,
            "plan_sheet_id": None,
        }

        if not has_evidence:
            notes = (
                "not_enough_indexed_information"
                if not has_indexed
                else "no_linked_evidence_yet"
            )
            rows_requiring_confirmation += 1
            rows.append(
                {
                    **base,
                    "traceability_row_id": _next_row_id(),
                    "evidence_candidate_id": None,
                    "evidence_citation_id": None,
                    "document_id": None,
                    "document_name": None,
                    "document_page_id": None,
                    "page_number": None,
                    "citation_excerpt": None,
                    "relationship_type": "no_linked_evidence_yet",
                    "relationship_source": "checklist_item",
                    "reviewer_action_needed": True,
                    "notes": notes,
                    "source_links": _source_links(
                        project_id,
                        finding_id=base["finding_id"],
                        workflow_item_id=base["workflow_item_id"],
                        review_packet_id=base["review_packet_id"],
                        has_workflow=bool(first_workflow),
                    ),
                }
            )
            continue

        # One row per linked evidence record, preserving the finding/workflow
        # context on each.
        for link in item_links:
            action_needed = (not reviewed) or (
                link.link_status in _LINK_NEEDS_CONFIRM
            )
            if action_needed:
                rows_requiring_confirmation += 1
            rows.append(
                {
                    **base,
                    "traceability_row_id": _next_row_id(),
                    "evidence_candidate_id": link.evidence_candidate_id,
                    "evidence_citation_id": link.evidence_citation_id,
                    "document_id": link.document_id,
                    "document_name": _document_name(documents, link.document_id),
                    "document_page_id": link.document_page_id,
                    "page_number": link.page_number,
                    "citation_excerpt": link.quoted_excerpt,
                    "relationship_type": "linked_evidence",
                    "relationship_source": "checklist_evidence_link",
                    "reviewer_action_needed": action_needed,
                    "notes": (
                        "not_reviewed" if not reviewed else "linked_evidence_exists"
                    ),
                    "source_links": _source_links(
                        project_id,
                        document_id=link.document_id,
                        finding_id=base["finding_id"],
                        workflow_item_id=base["workflow_item_id"],
                        review_packet_id=base["review_packet_id"],
                        has_workflow=bool(first_workflow),
                    ),
                }
            )

        linked_citation_ids = {
            link.evidence_citation_id for link in item_links if link.evidence_citation_id
        }
        for citation in item_citations:
            if citation.evidence_citation_id in linked_citation_ids:
                continue
            action_needed = (not reviewed) or (
                citation.citation_status == "needs_reviewer_confirmation"
            )
            if action_needed:
                rows_requiring_confirmation += 1
            rows.append(
                {
                    **base,
                    "traceability_row_id": _next_row_id(),
                    "evidence_candidate_id": None,
                    "evidence_citation_id": citation.evidence_citation_id,
                    "document_id": citation.document_id,
                    "document_name": _document_name(
                        documents, citation.document_id
                    ),
                    "document_page_id": citation.document_page_id,
                    "page_number": citation.page_number,
                    "citation_excerpt": citation.quoted_excerpt,
                    "relationship_type": "linked_evidence",
                    "relationship_source": "evidence_citation",
                    "reviewer_action_needed": action_needed,
                    "notes": (
                        "not_reviewed" if not reviewed else "linked_evidence_exists"
                    ),
                    "source_links": _source_links(
                        project_id,
                        document_id=citation.document_id,
                        finding_id=base["finding_id"],
                        workflow_item_id=base["workflow_item_id"],
                        review_packet_id=base["review_packet_id"],
                        has_workflow=bool(first_workflow),
                    ),
                }
            )

        for candidate in item_candidates:
            rows_requiring_confirmation += 1
            rows.append(
                {
                    **base,
                    "traceability_row_id": _next_row_id(),
                    "evidence_candidate_id": candidate.evidence_candidate_id,
                    "evidence_citation_id": None,
                    "document_id": candidate.document_id,
                    "document_name": _document_name(
                        documents, candidate.document_id
                    ),
                    "document_page_id": candidate.document_page_id,
                    "page_number": candidate.page_number,
                    "citation_excerpt": candidate.candidate_excerpt,
                    "relationship_type": "related_candidate",
                    "relationship_source": "evidence_candidate",
                    "reviewer_action_needed": True,
                    "notes": "not_reviewed",
                    "source_links": _source_links(
                        project_id,
                        document_id=candidate.document_id,
                        finding_id=base["finding_id"],
                        workflow_item_id=base["workflow_item_id"],
                        review_packet_id=base["review_packet_id"],
                        has_workflow=bool(first_workflow),
                    ),
                }
            )

    # Enrich each row with inline packet context, a stable row key, and the
    # latest reviewer review action. This is a read-only pass over data already
    # loaded; it adds context and never changes the underlying records.
    by_finding, by_checklist = _packet_context_index(db, project_id)
    latest_by_key = _latest_actions_by_key(db, project_id)
    for row in rows:
        contexts = _contexts_for_item(
            by_finding, by_checklist, row["checklist_item_id"], row["finding_id"]
        )
        row["packet_context_count"] = len(contexts)
        row["packet_contexts"] = contexts[:MAX_PACKET_CONTEXTS]
        # Prefer a real packet item over the workflow-derived packet hint when a
        # row is included in a packet.
        if contexts:
            row["review_packet_id"] = contexts[0]["review_packet_id"]
            row["review_packet_item_id"] = contexts[0]["review_packet_item_id"]
        key = build_row_key(
            checklist_item_id=row["checklist_item_id"],
            evidence_citation_id=row["evidence_citation_id"],
            evidence_candidate_id=row["evidence_candidate_id"],
            finding_id=row["finding_id"],
            relationship_type=row["relationship_type"],
            relationship_source=row["relationship_source"],
        )
        row["traceability_row_key"] = key
        row["latest_review_action"] = _action_dict(latest_by_key.get(key))

    packet_item_count = (
        db.query(models.ReviewPacketItem)
        .join(
            models.ReviewPacket,
            models.ReviewPacket.packet_id == models.ReviewPacketItem.packet_id,
        )
        .filter(models.ReviewPacket.project_id == project_id)
        .count()
    )

    summary = {
        "total_checklist_items": len(checklist_items),
        "checklist_items_with_linked_evidence": items_with_evidence,
        "checklist_items_without_linked_evidence": (
            len(checklist_items) - items_with_evidence
        ),
        "total_evidence_citations": len(citations),
        "total_evidence_candidates": len(candidates),
        "total_findings": len(findings),
        "total_workflow_items": sum(
            len(v) for v in workflow_by_finding.values()
        ),
        "total_packet_items": packet_item_count,
        "total_traceability_rows": len(rows),
        "rows_requiring_reviewer_confirmation": rows_requiring_confirmation,
    }

    handoff_readiness = _build_handoff_readiness(rows)

    return {
        "project_id": project_id,
        "generated_at": _now(),
        "limitations_note": LIMITATIONS_NOTE,
        "has_indexed_information": has_indexed,
        "summary": summary,
        "handoff_readiness": handoff_readiness,
        "rows": rows,
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


class TraceabilityError(Exception):
    """Raised when a traceability review action is not allowed."""

    def __init__(self, message: str, *, status_code: int = 400) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code


def record_traceability_review_action(
    db: Session,
    *,
    project_id: str,
    traceability_row_key: str,
    action_type: str,
    reviewer_note: str | None = None,
    created_by: str | None = None,
    checklist_item_id: str | None = None,
    evidence_citation_id: str | None = None,
    evidence_candidate_id: str | None = None,
    finding_id: str | None = None,
    workflow_item_id: str | None = None,
    review_packet_item_id: str | None = None,
    relationship_type: str | None = None,
) -> models.TraceabilityReviewAction:
    """Record one reviewer review action on a traceability row (append-only).

    Writes a TraceabilityReviewAction row and a matching audit event. It never
    mutates the checklist item, evidence, finding, workflow item, or packet the
    row references, so a link_rejected action discards the link for review without
    deleting any source data.
    """

    if db.get(models.Project, project_id) is None:
        raise TraceabilityError("Project not found.", status_code=404)
    if not traceability_row_key or not traceability_row_key.strip():
        raise TraceabilityError(
            "traceability_row_key is required.", status_code=422
        )
    if action_type not in ALLOWED_TRACEABILITY_REVIEW_ACTIONS:
        raise TraceabilityError(
            f"Unknown traceability review action '{action_type}'.",
            status_code=422,
        )
    note = (reviewer_note or "").strip() or None
    if note and find_prohibited_language(note):
        raise TraceabilityError(
            "reviewer_note contains prohibited final-decision wording.",
            status_code=422,
        )
    author = (created_by or "").strip() or "reviewer"
    row_key = traceability_row_key.strip()

    action_id = f"trace_act_{uuid.uuid4().hex[:12]}"
    record = models.TraceabilityReviewAction(
        action_id=action_id,
        project_id=project_id,
        traceability_row_key=row_key,
        action_type=action_type,
        reviewer_note=note,
        created_by=author,
        checklist_item_id=checklist_item_id,
        evidence_citation_id=evidence_citation_id,
        evidence_candidate_id=evidence_candidate_id,
        finding_id=finding_id,
        workflow_item_id=workflow_item_id,
        review_packet_item_id=review_packet_item_id,
        relationship_type=relationship_type,
    )
    db.add(record)
    db.add(
        models.AuditEvent(
            audit_event_id=f"audit_trace_{uuid.uuid4().hex[:12]}",
            project_id=project_id,
            event_type="traceability_review_action_recorded",
            actor_type="reviewer",
            related_entity_type="traceability_row",
            related_entity_id=row_key,
            description=(
                f"Traceability review action '{action_type}' recorded by "
                f"{author}."
            ),
            timestamp=_now(),
            event_metadata={
                "action_id": action_id,
                "traceability_row_key": row_key,
                "action_type": action_type,
                "checklist_item_id": checklist_item_id,
                "finding_id": finding_id,
                "relationship_type": relationship_type,
            },
        )
    )
    db.commit()
    db.refresh(record)
    return record


def list_traceability_review_actions(
    db: Session, project_id: str, traceability_row_key: str
) -> list[models.TraceabilityReviewAction]:
    """Return the recorded review action history for one traceability row."""

    stmt = (
        select(models.TraceabilityReviewAction)
        .where(
            models.TraceabilityReviewAction.project_id == project_id,
            models.TraceabilityReviewAction.traceability_row_key
            == traceability_row_key,
        )
        .order_by(models.TraceabilityReviewAction.created_at)
    )
    return list(db.scalars(stmt).all())
