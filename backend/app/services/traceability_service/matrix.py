"""Read-only project-wide traceability matrix build and handoff readiness."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import models
from app.services.traceability_service._common import (
    LIMITATIONS_NOTE,
    MAX_PACKET_CONTEXTS,
    _CHECKLIST_REVIEWED,
    _document_map,
    _document_name,
    _has_indexed_pages,
    _LINK_NEEDS_CONFIRM,
    _now,
    _source_links,
    _workflow_items_by_finding,
    build_row_key,
)
from app.services.traceability_service.reads import (
    _action_dict,
    _build_handoff_readiness,
    _contexts_for_item,
    _latest_actions_by_key,
    _packet_context_index,
)


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
