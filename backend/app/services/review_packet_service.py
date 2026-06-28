"""Review packet builder service for Phase 8.

This service assembles a review-support packet draft for a project from seeded
data created in prior phases: documents, checklist items, findings, plan sheets,
CAD-aware metadata, plan references, plan consistency findings, sheet hotspots,
plan consistency review actions, and audit evidence. The packet organizes
evidence for a human reviewer.

The packet is a review-support draft. It does not approve plans, certify
compliance, stamp drawings, verify CAD, validate a design, or make final
engineering decisions. There is no action called approve.

Read side effects: get_review_packet, get_review_packet_traceability, and
get_review_packet_print_view each write an audit event recording that the packet
was viewed, the traceability matrix was requested, or the print view was
requested. This is intentional so the decision history shows reviewer access.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.safety import (
    ALLOWED_REVIEW_PACKET_ACTIONS,
    ALLOWED_REVIEW_PACKET_STATUSES,
    PACKET_ACTION_TO_STATUS,
    find_prohibited_language,
)
from app.db import models
from app.services import (
    audit_service,
    cad_metadata_service,
    checklist_service,
    document_service,
    finding_service,
    plan_consistency_service,
    plan_review_service,
    plan_sheet_hotspot_service,
    plan_sheet_service,
)

PACKET_TYPE = "review_support_draft"
GENERATED_BY = "system"
GENERATED_FROM_PHASE = "phase_1_to_7"

LIMITATIONS_NOTE = (
    "This is a draft review-support packet. It organizes evidence for a human "
    "reviewer and does not approve plans, certify compliance, stamp drawings, "
    "verify CAD, validate the design, or replace a licensed Professional "
    "Engineer."
)

PROFESSIONAL_LIMITATIONS = (
    "Civil Engineer AI is a review-support and evidence-organization system. "
    "This packet is a draft that organizes submitted documents, checklist "
    "items, findings, plan sheet metadata, CAD-aware metadata, and review "
    "actions for a human reviewer. It does not approve plans, certify "
    "compliance, stamp drawings, verify CAD drawings, validate the design, or "
    "make final engineering decisions. Every item requires human review, and a "
    "licensed Professional Engineer remains responsible for the review."
)

DRAFT_NOTICE = (
    "Draft review-support material. It does not approve, certify, stamp, "
    "verify CAD, or validate the design, and it does not replace a licensed "
    "Professional Engineer."
)

TRACEABILITY_REVIEW_NOTE = (
    "Traceability review state for rows included in this packet. A reviewer "
    "review action records that the reviewer reviewed the link for review only. "
    "Rows without an action require reviewer confirmation. None of this means a "
    "requirement is satisfied or a plan is approved."
)


class ReviewPacketError(Exception):
    """Raised when a review packet operation is not allowed."""

    def __init__(self, message: str, *, status_code: int = 400) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code


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
    actor_type: str = "system",
    metadata: dict | None = None,
) -> None:
    db.add(
        models.AuditEvent(
            audit_event_id=f"audit_pkt_{uuid.uuid4().hex[:12]}",
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


# A small accumulator used while building a packet, so each section can add
# items and each item can add evidence links with monotonic display order.
class _Builder:
    def __init__(self, packet_id: str, project_id: str) -> None:
        self.packet_id = packet_id
        self.project_id = project_id
        self.sections: list[models.ReviewPacketSection] = []
        self.items: list[models.ReviewPacketItem] = []
        self.links: list[models.ReviewPacketEvidenceLink] = []
        self._section_order = 0

    def section(
        self, title: str, section_type: str, summary: str,
        *, requires_human_review: bool = True,
    ) -> str:
        section_id = f"sec_{_short()}"
        self.sections.append(
            models.ReviewPacketSection(
                section_id=section_id,
                packet_id=self.packet_id,
                title=title,
                section_type=section_type,
                display_order=self._section_order,
                summary=summary,
                status="draft",
                requires_human_review=requires_human_review,
            )
        )
        self._section_order += 1
        return section_id

    def item(
        self,
        section_id: str,
        *,
        item_type: str,
        title: str,
        description: str,
        severity: str,
        source_type: str,
        source_id: str | None,
        requires_human_review: bool = True,
        links: list[tuple[str, str, str, str]] | None = None,
    ) -> None:
        item_id = f"item_{_short()}"
        self.items.append(
            models.ReviewPacketItem(
                item_id=item_id,
                packet_id=self.packet_id,
                section_id=section_id,
                item_type=item_type,
                title=title,
                description=description,
                severity=severity,
                source_type=source_type,
                source_id=source_id,
                reviewer_status="draft",
                reviewer_note=None,
                requires_human_review=requires_human_review,
                display_order=len(self.items),
            )
        )
        for evidence_type, evidence_id, relationship, label in links or []:
            if not evidence_id:
                continue
            self.links.append(
                models.ReviewPacketEvidenceLink(
                    evidence_link_id=f"evl_{_short()}",
                    packet_id=self.packet_id,
                    item_id=item_id,
                    evidence_type=evidence_type,
                    evidence_id=evidence_id,
                    relationship=relationship,
                    label=label,
                )
            )


def _delete_existing(db: Session, project_id: str) -> None:
    packet_ids = [
        p.packet_id
        for p in db.scalars(
            select(models.ReviewPacket).where(
                models.ReviewPacket.project_id == project_id
            )
        ).all()
    ]
    if not packet_ids:
        return
    for model in (
        models.ReviewPacketReviewerAction,
        models.ReviewPacketEvidenceLink,
        models.ReviewPacketItem,
        models.ReviewPacketSection,
    ):
        db.query(model).filter(model.packet_id.in_(packet_ids)).delete(
            synchronize_session=False
        )
    db.query(models.ReviewPacket).filter(
        models.ReviewPacket.project_id == project_id
    ).delete(synchronize_session=False)
    db.commit()


def _build_sections(db: Session, project_id: str, builder: _Builder) -> None:
    documents = document_service.list_documents(db, project_id)
    checklist = checklist_service.list_checklist_items(db, project_id)
    findings = finding_service.list_findings(db, project_id)
    plan_sheets = plan_sheet_service.list_plan_sheets(db, project_id)
    cad = cad_metadata_service.list_cad_metadata(db, project_id)
    plan_refs = plan_consistency_service.list_plan_references(db, project_id)
    plan_findings = plan_consistency_service.list_plan_consistency_findings(
        db, project_id
    )
    hotspots = plan_sheet_hotspot_service.list_sheet_hotspots(db, project_id)
    review_actions = plan_review_service.list_plan_consistency_review_actions(
        db, project_id
    )

    cad_by_sheet: dict[str, list[models.CadMetadata]] = {}
    for record in cad:
        if record.sheet_id:
            cad_by_sheet.setdefault(record.sheet_id, []).append(record)

    # Section 1: Executive review-support summary.
    sec = builder.section(
        "Executive review-support summary",
        "executive_summary",
        "High-level overview of the review-support evidence gathered for this "
        "project draft packet.",
        requires_human_review=False,
    )
    builder.item(
        sec,
        item_type="summary",
        title="Brookside Meadows review-support overview",
        description=(
            f"This draft packet organizes {len(documents)} documents, "
            f"{len(checklist)} checklist items, {len(findings)} review-support "
            f"findings, {len(plan_sheets)} plan sheets, {len(plan_findings)} "
            f"plan consistency findings, and {len(hotspots)} sheet hotspots for "
            "human review. Nothing in this packet is a final engineering "
            "decision."
        ),
        severity="info",
        source_type="project",
        source_id=project_id,
        requires_human_review=False,
    )

    # Section 2: Document and checklist findings.
    sec = builder.section(
        "Document and checklist findings",
        "document_checklist",
        "Review-support findings tied to submitted documents and checklist "
        "items.",
    )
    for f in findings:
        links: list[tuple[str, str, str, str]] = []
        for doc_id in f.related_documents or []:
            links.append(("document", doc_id, "source_document", doc_id))
        for chk_id in f.related_checklist_items or []:
            links.append(("checklist_item", chk_id, "checklist_item", chk_id))
        builder.item(
            sec,
            item_type="finding",
            title=f.title,
            description=f.reason_it_matters,
            severity=f.risk_level,
            source_type="finding",
            source_id=f.finding_id,
            links=links,
        )
    gap_statuses = {"missing", "partial", "referenced_not_included", "not_yet_submitted"}
    for d in documents:
        gap = d.status in gap_statuses or bool(
            d.intentionally_missing_or_conflicting_information
        )
        if not gap:
            continue
        builder.item(
            sec,
            item_type="document",
            title=f"Document needs review: {d.file_name}",
            description=(
                d.intentionally_missing_or_conflicting_information or d.purpose
            ),
            severity="medium",
            source_type="document",
            source_id=d.document_id,
            links=[("document", d.document_id, "source_document", d.file_name)],
        )

    # Section 3: Plan sheet and CAD-aware references.
    sec = builder.section(
        "Plan sheet and CAD-aware references",
        "plan_sheet_cad",
        "Plan sheets and civil feature references that need reviewer "
        "confirmation. CAD-aware metadata is seeded, not extracted from real "
        "CAD files.",
    )
    sheet_attention = {"referenced_not_included", "needs_reviewer_confirmation", "missing"}
    for s in plan_sheets:
        if s.status not in sheet_attention and not s.related_findings:
            continue
        links = [("plan_sheet", s.sheet_id, "plan_sheet", s.sheet_number)]
        for doc_id in s.related_documents or []:
            links.append(("document", doc_id, "source_document", doc_id))
        for record in cad_by_sheet.get(s.sheet_id, []):
            links.append(
                ("cad_metadata", record.cad_metadata_id, "civil_feature",
                 record.entity_label)
            )
        builder.item(
            sec,
            item_type="plan_sheet",
            title=f"{s.sheet_number} {s.sheet_title}",
            description=s.sheet_purpose,
            severity="medium",
            source_type="plan_sheet",
            source_id=s.sheet_id,
            links=links,
        )
    for r in plan_refs:
        if r.consistency_status == "consistent":
            continue
        evidence_type = (
            "plan_sheet" if r.target_type == "plan_sheet" else "cad_metadata"
        )
        links = [(evidence_type, r.target_id, "reference_target", r.target_id)]
        if r.source_type == "document":
            links.append(("document", r.source_id, "source_document", r.source_id))
        description = r.reference_context
        if r.review_note:
            description = f"{description} {r.review_note}"
        builder.item(
            sec,
            item_type="plan_reference",
            title=r.reference_label,
            description=description,
            severity="medium",
            source_type="plan_reference",
            source_id=r.plan_reference_id,
            links=links,
        )

    # Section 4: Sheet hotspot observations.
    sec = builder.section(
        "Sheet hotspot observations",
        "sheet_hotspots",
        "Seeded review-support hotspot annotations over plan sheet previews. "
        "These are not extracted CAD geometry or verified plan locations.",
    )
    for h in hotspots:
        links = [("plan_sheet", h.sheet_id, "plan_sheet", h.sheet_id)]
        for fid in h.related_plan_finding_ids or []:
            links.append(("plan_consistency_finding", fid, "plan_finding", fid))
        for cid in h.related_cad_metadata_ids or []:
            links.append(("cad_metadata", cid, "civil_feature", cid))
        for did in h.related_document_ids or []:
            links.append(("document", did, "source_document", did))
        for chk in h.related_checklist_item_ids or []:
            links.append(("checklist_item", chk, "checklist_item", chk))
        for rid in h.related_plan_reference_ids or []:
            links.append(("plan_reference", rid, "plan_reference", rid))
        builder.item(
            sec,
            item_type="hotspot",
            title=h.label,
            description=h.description,
            severity=h.severity,
            source_type="sheet_hotspot",
            source_id=h.hotspot_id,
            links=links,
        )

    # Section 5: Plan consistency findings.
    sec = builder.section(
        "Plan consistency findings",
        "plan_consistency",
        "Review-support findings from the plan consistency check.",
    )
    for pf in plan_findings:
        links = []
        for sid in pf.related_sheet_ids or []:
            links.append(("plan_sheet", sid, "plan_sheet", sid))
        for cid in pf.related_cad_metadata_ids or []:
            links.append(("cad_metadata", cid, "civil_feature", cid))
        for did in pf.related_document_ids or []:
            links.append(("document", did, "source_document", did))
        for chk in pf.related_checklist_items or []:
            links.append(("checklist_item", chk, "checklist_item", chk))
        builder.item(
            sec,
            item_type="plan_consistency_finding",
            title=pf.title,
            description=pf.summary,
            severity=pf.risk_level,
            source_type="plan_consistency_finding",
            source_id=pf.plan_finding_id,
            links=links,
        )

    # Section 6: Human review actions.
    sec = builder.section(
        "Human review actions",
        "human_review_actions",
        "Reviewer actions recorded on plan consistency findings.",
    )
    if review_actions:
        for a in review_actions:
            builder.item(
                sec,
                item_type="review_action",
                title=f"Reviewer action: {a.action.replace('_', ' ')}",
                description=a.reviewer_note,
                severity="info",
                source_type="plan_consistency_review_action",
                source_id=a.review_action_id,
                requires_human_review=False,
                links=[
                    ("plan_consistency_finding", a.plan_finding_id,
                     "review_action", a.plan_finding_id)
                ],
            )
    else:
        builder.item(
            sec,
            item_type="info",
            title="No reviewer actions recorded yet",
            description=(
                "No plan consistency review actions have been recorded for this "
                "project yet. Reviewer actions appear here once recorded."
            ),
            severity="info",
            source_type="project",
            source_id=project_id,
            requires_human_review=False,
        )

    # Section 7: Evidence traceability matrix.
    sec = builder.section(
        "Evidence traceability matrix",
        "traceability",
        "Each packet item links back to its source evidence. The full matrix "
        "is available from the traceability view.",
        requires_human_review=False,
    )
    builder.item(
        sec,
        item_type="traceability_overview",
        title="Evidence traceability matrix",
        description=(
            "Every item in this packet links to the documents, checklist "
            "items, plan sheets, CAD-aware metadata, plan references, and "
            "findings it was built from. Use the traceability view for the row "
            "by row matrix."
        ),
        severity="info",
        source_type="packet",
        source_id=builder.packet_id,
        requires_human_review=False,
    )

    # Section 8: Professional limitations and review boundary.
    sec = builder.section(
        "Professional limitations and review boundary",
        "limitations",
        "The professional boundary that applies to this packet.",
        requires_human_review=False,
    )
    builder.item(
        sec,
        item_type="limitation",
        title="Professional limitations and review boundary",
        description=PROFESSIONAL_LIMITATIONS,
        severity="info",
        source_type="project",
        source_id=project_id,
        requires_human_review=False,
    )


def generate_review_packet(db: Session, project_id: str) -> models.ReviewPacket:
    """Generate a fresh review-support packet draft for a project.

    Idempotent: existing packets for the project are removed and a new packet is
    built from the current seeded data. Writes a review_packet_generated audit
    event.
    """

    project = db.get(models.Project, project_id)
    if project is None:
        raise ReviewPacketError("Project not found.", status_code=404)

    # Enforce the per-organization review packet limit before any mutation, when
    # enforcement is enabled. A no-op for the demo org and in advisory mode, so
    # the public Brookside demo and startup seeding are never blocked.
    from app.services import usage_service

    usage_service.check_limit(
        db,
        category="review_packet_generated",
        organization_id=project.organization_id,
    )

    _delete_existing(db, project_id)

    packet_id = f"packet_{_short()}"
    packet = models.ReviewPacket(
        packet_id=packet_id,
        project_id=project_id,
        title="Brookside Meadows review-support packet (draft)",
        packet_type=PACKET_TYPE,
        status="draft",
        summary=(
            "Draft review-support packet assembling documents, checklist items, "
            "findings, plan sheets, CAD-aware metadata, hotspots, plan "
            "consistency findings, and reviewer actions for human review."
        ),
        generated_from_phase=GENERATED_FROM_PHASE,
        created_by=GENERATED_BY,
        limitations_note=LIMITATIONS_NOTE,
    )
    db.add(packet)

    builder = _Builder(packet_id, project_id)
    _build_sections(db, project_id, builder)
    for section in builder.sections:
        db.add(section)
    for item in builder.items:
        db.add(item)
    for link in builder.links:
        db.add(link)

    _audit(
        db,
        project_id=project_id,
        event_type="review_packet_generated",
        related_entity_type="review_packet",
        related_entity_id=packet_id,
        description=(
            f"Review-support packet draft generated with "
            f"{len(builder.sections)} sections and {len(builder.items)} items."
        ),
        metadata={
            "packet_id": packet_id,
            "section_count": len(builder.sections),
            "item_count": len(builder.items),
            "evidence_link_count": len(builder.links),
        },
    )
    # Record advisory usage for the generated packet (best-effort, skips the demo
    # organization). Used by usage summaries and enforcement counting.
    usage_service.record_usage_safe(
        db,
        category="review_packet_generated",
        organization_id=project.organization_id,
        project_id=project_id,
    )
    db.commit()
    db.refresh(packet)
    return packet


def get_packet(db: Session, packet_id: str) -> models.ReviewPacket | None:
    return db.scalars(
        select(models.ReviewPacket).where(
            models.ReviewPacket.packet_id == packet_id
        )
    ).first()


def list_review_packets(db: Session, project_id: str) -> list[models.ReviewPacket]:
    stmt = (
        select(models.ReviewPacket)
        .where(models.ReviewPacket.project_id == project_id)
        .order_by(models.ReviewPacket.created_at.desc())
    )
    return list(db.scalars(stmt).all())


def list_evidence_links_for_item(
    db: Session, item_id: str
) -> list[models.ReviewPacketEvidenceLink]:
    """Return the evidence links for one packet item (public accessor)."""

    return list(
        db.scalars(
            select(models.ReviewPacketEvidenceLink).where(
                models.ReviewPacketEvidenceLink.item_id == item_id
            )
        ).all()
    )


def _links_by_item(db: Session, packet_id: str) -> dict[str, list]:
    links = db.scalars(
        select(models.ReviewPacketEvidenceLink).where(
            models.ReviewPacketEvidenceLink.packet_id == packet_id
        )
    ).all()
    grouped: dict[str, list] = {}
    for link in links:
        grouped.setdefault(link.item_id, []).append(link)
    return grouped


def _items_by_section(db: Session, packet_id: str) -> dict[str, list]:
    items = db.scalars(
        select(models.ReviewPacketItem)
        .where(models.ReviewPacketItem.packet_id == packet_id)
        .order_by(models.ReviewPacketItem.display_order)
    ).all()
    grouped: dict[str, list] = {}
    for item in items:
        grouped.setdefault(item.section_id, []).append(item)
    return grouped


def assemble_packet_detail(db: Session, packet: models.ReviewPacket) -> dict:
    sections = db.scalars(
        select(models.ReviewPacketSection)
        .where(models.ReviewPacketSection.packet_id == packet.packet_id)
        .order_by(models.ReviewPacketSection.display_order)
    ).all()
    links_by_item = _links_by_item(db, packet.packet_id)
    items_by_section = _items_by_section(db, packet.packet_id)

    def _item_dict(item: models.ReviewPacketItem) -> dict:
        return {
            "item_id": item.item_id,
            "packet_id": item.packet_id,
            "section_id": item.section_id,
            "item_type": item.item_type,
            "title": item.title,
            "description": item.description,
            "severity": item.severity,
            "source_type": item.source_type,
            "source_id": item.source_id,
            "reviewer_status": item.reviewer_status,
            "reviewer_note": item.reviewer_note,
            "requires_human_review": item.requires_human_review,
            "display_order": item.display_order,
            "evidence_links": links_by_item.get(item.item_id, []),
        }

    section_dicts = []
    for section in sections:
        section_dicts.append(
            {
                "section_id": section.section_id,
                "packet_id": section.packet_id,
                "title": section.title,
                "section_type": section.section_type,
                "display_order": section.display_order,
                "summary": section.summary,
                "status": section.status,
                "requires_human_review": section.requires_human_review,
                "items": [
                    _item_dict(i)
                    for i in items_by_section.get(section.section_id, [])
                ],
            }
        )

    return {
        "packet_id": packet.packet_id,
        "project_id": packet.project_id,
        "title": packet.title,
        "packet_type": packet.packet_type,
        "status": packet.status,
        "summary": packet.summary,
        "generated_from_phase": packet.generated_from_phase,
        "created_by": packet.created_by,
        "limitations_note": packet.limitations_note,
        "created_at": packet.created_at,
        "updated_at": packet.updated_at,
        "sections": section_dicts,
    }


def get_review_packet(db: Session, packet_id: str) -> dict | None:
    """Return the full packet detail and record that it was viewed.

    Read side effect: writes a review_packet_viewed audit event.
    """

    packet = get_packet(db, packet_id)
    if packet is None:
        return None
    _audit(
        db,
        project_id=packet.project_id,
        event_type="review_packet_viewed",
        related_entity_type="review_packet",
        related_entity_id=packet_id,
        description="Review packet draft viewed.",
        actor_type="reviewer",
        metadata={"packet_id": packet_id},
    )
    db.commit()
    return assemble_packet_detail(db, packet)


def get_review_packet_traceability(db: Session, packet_id: str) -> dict | None:
    """Return the evidence traceability matrix for a packet.

    Read side effect: writes a review_packet_traceability_requested audit event.
    """

    packet = get_packet(db, packet_id)
    if packet is None:
        return None

    sections = db.scalars(
        select(models.ReviewPacketSection).where(
            models.ReviewPacketSection.packet_id == packet_id
        )
    ).all()
    section_type_by_id = {s.section_id: s.section_type for s in sections}
    items = db.scalars(
        select(models.ReviewPacketItem)
        .where(models.ReviewPacketItem.packet_id == packet_id)
        .order_by(models.ReviewPacketItem.display_order)
    ).all()
    item_by_id = {i.item_id: i for i in items}
    links = db.scalars(
        select(models.ReviewPacketEvidenceLink).where(
            models.ReviewPacketEvidenceLink.packet_id == packet_id
        )
    ).all()

    rows = []
    for link in links:
        item = item_by_id.get(link.item_id)
        if item is None:
            continue
        rows.append(
            {
                "section_type": section_type_by_id.get(item.section_id, ""),
                "item_id": item.item_id,
                "item_title": item.title,
                "item_type": item.item_type,
                "source_type": item.source_type,
                "source_id": item.source_id,
                "evidence_type": link.evidence_type,
                "evidence_id": link.evidence_id,
                "relationship": link.relationship,
                "label": link.label,
            }
        )

    _audit(
        db,
        project_id=packet.project_id,
        event_type="review_packet_traceability_requested",
        related_entity_type="review_packet",
        related_entity_id=packet_id,
        description="Review packet evidence traceability matrix requested.",
        actor_type="reviewer",
        metadata={"packet_id": packet_id, "row_count": len(rows)},
    )
    db.commit()

    return {
        "packet_id": packet_id,
        "project_id": packet.project_id,
        "total_rows": len(rows),
        "rows": rows,
        "note": (
            "Each row traces a packet item back to one source evidence entity. "
            "This is review-support traceability, not a verification or "
            "certification of the evidence."
        ),
    }


def get_review_packet_print_view(db: Session, packet_id: str) -> dict | None:
    """Return a printable review-support view for a packet.

    Read side effect: writes a review_packet_print_view_requested audit event.
    """

    packet = get_packet(db, packet_id)
    if packet is None:
        return None

    detail = assemble_packet_detail(db, packet)
    print_sections = [
        {
            "title": s["title"],
            "section_type": s["section_type"],
            "summary": s["summary"],
            "items": s["items"],
        }
        for s in detail["sections"]
    ]

    traceability_review_rows = _packet_traceability_review_rows(
        db, packet.project_id, packet_id
    )

    _audit(
        db,
        project_id=packet.project_id,
        event_type="review_packet_print_view_requested",
        related_entity_type="review_packet",
        related_entity_id=packet_id,
        description="Review packet printable view requested.",
        actor_type="reviewer",
        metadata={"packet_id": packet_id},
    )
    db.commit()

    return {
        "packet_id": packet.packet_id,
        "project_id": packet.project_id,
        "title": packet.title,
        "packet_type": packet.packet_type,
        "status": packet.status,
        "summary": packet.summary,
        "generated_from_phase": packet.generated_from_phase,
        "created_by": packet.created_by,
        "created_at": packet.created_at,
        "limitations_note": packet.limitations_note,
        "professional_limitations": PROFESSIONAL_LIMITATIONS,
        "draft_notice": DRAFT_NOTICE,
        "sections": print_sections,
        "traceability_review_rows": traceability_review_rows,
        "traceability_note": TRACEABILITY_REVIEW_NOTE,
    }


def _packet_traceability_review_rows(
    db: Session, project_id: str, packet_id: str
) -> list[dict]:
    """Return project traceability rows included in this packet, with review state.

    Read-only. Each row carries its latest reviewer review action, or
    requires_reviewer_confirmation when no action has been recorded. This shows the
    reviewer's traceability review state on the handoff view; it does not approve
    or certify anything.
    """

    from app.services import traceability_service

    result = traceability_service.build_project_traceability(db, project_id)
    if result is None:
        return []
    rows: list[dict] = []
    for r in result["rows"]:
        contexts = r.get("packet_contexts", [])
        if not any(c["review_packet_id"] == packet_id for c in contexts):
            continue
        action = r.get("latest_review_action")
        rows.append(
            {
                "traceability_row_key": r["traceability_row_key"],
                "checklist_title": r.get("checklist_title"),
                "checklist_requirement": r.get("checklist_requirement"),
                "relationship_type": r["relationship_type"],
                "review_action_type": action["action_type"] if action else None,
                "reviewer_note": action.get("reviewer_note") if action else None,
                "created_by": action.get("created_by") if action else None,
                "requires_reviewer_confirmation": action is None,
            }
        )
    return rows


def summarize_review_packet(db: Session, packet_id: str) -> dict | None:
    packet = get_packet(db, packet_id)
    if packet is None:
        return None

    sections = db.scalars(
        select(models.ReviewPacketSection).where(
            models.ReviewPacketSection.packet_id == packet_id
        )
    ).all()
    section_type_by_id = {s.section_id: s.section_type for s in sections}
    items = db.scalars(
        select(models.ReviewPacketItem).where(
            models.ReviewPacketItem.packet_id == packet_id
        )
    ).all()
    link_count = (
        db.query(models.ReviewPacketEvidenceLink)
        .filter(models.ReviewPacketEvidenceLink.packet_id == packet_id)
        .count()
    )

    by_section: dict[str, int] = {}
    by_status: dict[str, int] = {}
    by_severity: dict[str, int] = {}
    for item in items:
        stype = section_type_by_id.get(item.section_id, "unknown")
        by_section[stype] = by_section.get(stype, 0) + 1
        by_status[item.reviewer_status] = by_status.get(item.reviewer_status, 0) + 1
        by_severity[item.severity] = by_severity.get(item.severity, 0) + 1

    return {
        "packet_id": packet_id,
        "project_id": packet.project_id,
        "status": packet.status,
        "total_sections": len(sections),
        "total_items": len(items),
        "total_evidence_links": link_count,
        "items_by_section_type": by_section,
        "items_by_status": by_status,
        "items_by_severity": by_severity,
        "items_requiring_human_review": len(
            [i for i in items if i.requires_human_review]
        ),
    }


def _get_item(
    db: Session, packet_id: str, item_id: str
) -> models.ReviewPacketItem:
    item = db.scalars(
        select(models.ReviewPacketItem).where(
            models.ReviewPacketItem.item_id == item_id,
            models.ReviewPacketItem.packet_id == packet_id,
        )
    ).first()
    if item is None:
        raise ReviewPacketError(
            "Packet item not found for this packet.", status_code=404
        )
    return item


def _record_action(
    db: Session,
    *,
    item: models.ReviewPacketItem,
    action_type: str,
    new_status: str,
    reviewer_note: str,
    reviewer_name: str,
) -> models.ReviewPacketReviewerAction:
    previous_status = item.reviewer_status
    item.reviewer_status = new_status
    project_id = _packet_project(db, item.packet_id)

    action_id = f"pkt_act_{_short()}"
    record = models.ReviewPacketReviewerAction(
        action_id=action_id,
        packet_id=item.packet_id,
        item_id=item.item_id,
        action_type=action_type,
        reviewer_note=reviewer_note,
        previous_status=previous_status,
        new_status=new_status,
        reviewer_name=reviewer_name,
    )
    db.add(record)
    _audit(
        db,
        project_id=project_id,
        event_type="review_packet_item_action_recorded",
        related_entity_type="review_packet_item",
        related_entity_id=item.item_id,
        description=(
            f"Review packet item action '{action_type}' recorded by "
            f"{reviewer_name}."
        ),
        actor_type="reviewer",
        metadata={
            "packet_id": item.packet_id,
            "item_id": item.item_id,
            "action_id": action_id,
            "action_type": action_type,
            "previous_status": previous_status,
            "new_status": new_status,
            "reviewer_name": reviewer_name,
        },
    )
    _audit(
        db,
        project_id=project_id,
        event_type="review_packet_item_status_updated",
        related_entity_type="review_packet_item",
        related_entity_id=item.item_id,
        description=(
            f"Review packet item status updated from {previous_status} to "
            f"{new_status}."
        ),
        actor_type="reviewer",
        metadata={
            "packet_id": item.packet_id,
            "item_id": item.item_id,
            "previous_status": previous_status,
            "new_status": new_status,
        },
    )
    return record


def _packet_project(db: Session, packet_id: str) -> str:
    packet = get_packet(db, packet_id)
    return packet.project_id if packet else ""


def create_review_packet_reviewer_action(
    db: Session,
    *,
    packet_id: str,
    item_id: str,
    action_type: str,
    reviewer_note: str,
    reviewer_name: str,
) -> tuple[models.ReviewPacketReviewerAction, models.ReviewPacketItem]:
    """Validate and persist a reviewer action on a packet item."""

    item = _get_item(db, packet_id, item_id)
    if action_type not in ALLOWED_REVIEW_PACKET_ACTIONS:
        raise ReviewPacketError(
            f"Unknown packet action '{action_type}'.", status_code=422
        )
    if not reviewer_name or not reviewer_name.strip():
        raise ReviewPacketError("reviewer_name is required.", status_code=422)
    if not reviewer_note or not reviewer_note.strip():
        raise ReviewPacketError("reviewer_note is required.", status_code=422)
    if find_prohibited_language(reviewer_note):
        raise ReviewPacketError(
            "reviewer_note contains prohibited final-decision wording.",
            status_code=422,
        )

    record = _record_action(
        db,
        item=item,
        action_type=action_type,
        new_status=PACKET_ACTION_TO_STATUS[action_type],
        reviewer_note=reviewer_note.strip(),
        reviewer_name=reviewer_name.strip(),
    )
    db.commit()
    db.refresh(record)
    db.refresh(item)
    return record, item


def update_review_packet_item_status(
    db: Session,
    *,
    packet_id: str,
    item_id: str,
    new_status: str,
    reviewer_note: str | None = None,
    reviewer_name: str | None = None,
) -> models.ReviewPacketItem:
    """Validate and apply a status update to a packet item."""

    item = _get_item(db, packet_id, item_id)
    if new_status not in ALLOWED_REVIEW_PACKET_STATUSES:
        raise ReviewPacketError(
            f"Unknown packet status '{new_status}'.", status_code=422
        )
    note = (reviewer_note or "").strip()
    if find_prohibited_language(note):
        raise ReviewPacketError(
            "reviewer_note contains prohibited final-decision wording.",
            status_code=422,
        )

    _record_action(
        db,
        item=item,
        action_type=new_status,
        new_status=new_status,
        reviewer_note=note or "Status updated by reviewer.",
        reviewer_name=(reviewer_name or "reviewer").strip(),
    )
    db.commit()
    db.refresh(item)
    return item


def ensure_packet(db: Session, project_id: str) -> None:
    """Generate a packet once if none exists for the project.

    Used at startup so the read endpoints and frontend have a packet without a
    manual generate call. Gated on no packet existing, so it does not regenerate
    on every restart.
    """

    if db.get(models.Project, project_id) is None:
        return
    existing = (
        db.query(models.ReviewPacket)
        .filter(models.ReviewPacket.project_id == project_id)
        .first()
    )
    if existing is None:
        generate_review_packet(db, project_id)
