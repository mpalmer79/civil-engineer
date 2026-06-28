"""Read-only project-wide traceability aggregation (Phase 4A).

This service aggregates relationships that already exist between project checklist
items, evidence links, citations, candidates, documents and pages, findings,
workflow items, and review packets. It organizes existing links only. It does not
run any analysis engine, call any AI provider, mutate any data, or determine
whether a requirement is satisfied. Every row is review-support context that
requires reviewer confirmation.

The aggregation deliberately preserves four distinct states:

* no_linked_evidence_yet: the checklist item has no linked evidence, citation, or
  candidate. This is not a statement that the requirement is unsupported.
* not_enough_indexed_information: there is no linked evidence and the project has
  no indexed, searchable document pages yet.
* not_reviewed: linked evidence exists but the reviewer has not confirmed it.
* linked_evidence_exists: evidence is linked, still review-support only.
"""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import models

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
        "total_packet_items": 0,
        "total_traceability_rows": len(rows),
        "rows_requiring_reviewer_confirmation": rows_requiring_confirmation,
    }

    return {
        "project_id": project_id,
        "generated_at": _now(),
        "limitations_note": LIMITATIONS_NOTE,
        "has_indexed_information": has_indexed,
        "summary": summary,
        "rows": rows,
    }
