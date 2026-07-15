"""Section and item assembly for review-support packet drafts.

The _Builder accumulates sections, items, and evidence links while a packet is
being built, and _build_sections populates them from seeded prior-phase data.
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.db import models
from app.services import (
    cad_metadata_service,
    checklist_service,
    document_service,
    finding_service,
    plan_consistency_service,
    plan_review_service,
    plan_sheet_hotspot_service,
    plan_sheet_service,
)

from ._common import PROFESSIONAL_LIMITATIONS, _short


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
