"""External review response package service for Phase 10.

This service turns the Phase 9 reviewer workflow board items into a structured
draft external response package a human reviewer can prepare for an applicant,
design engineer, municipal reviewer, or internal review team. It groups items by
topic, drafts plain external-review wording, keeps traceability to the workflow
item, packet item, and source entities, and builds an attachment checklist and a
human review sign-off checklist.

The response package supports drafting external communication. It does not send
email, approve plans, certify compliance, stamp drawings, verify CAD, validate
the design, or make final engineering decisions. There is no action called
approve, and every item stays under human review.

Read side effects: get_response_package, get_response_package_print_view,
get_response_package_attachments, and get_response_package_history each write an
audit event recording the access. This is intentional so the decision history
shows reviewer access.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.safety import (
    ALLOWED_RESPONSE_ITEM_STATUSES,
    ALLOWED_RESPONSE_PACKAGE_STATUSES,
    RESPONSE_ITEM_STATUS_TO_ACTION,
    RESPONSE_PACKAGE_STATUS_TO_ACTION,
    find_prohibited_language,
)
from app.db import models
from app.services import review_packet_service, workflow_service

GENERATED_BY = "system"
DEFAULT_AUDIENCE = "design_engineer"

LIMITATIONS_NOTE = (
    "This is a draft external response package. It supports human review and "
    "does not send official correspondence, approve plans, certify compliance, "
    "stamp drawings, verify CAD, validate the design, or replace a licensed "
    "Professional Engineer."
)

EXTERNAL_COMMUNICATION_BOUNDARY = (
    "Civil Engineer AI prepares draft external communication for a human "
    "reviewer. It does not send email or official correspondence, and it does "
    "not approve plans, certify compliance, stamp drawings, verify CAD drawings, "
    "validate the design, or make final engineering decisions. A licensed "
    "Professional Engineer remains responsible for the review and any issued "
    "response."
)

DRAFT_NOTICE = (
    "Draft external response support material. It does not approve, certify, "
    "stamp, verify CAD, validate the design, or constitute final engineering "
    "approval, and it has not been sent."
)

DRAFT_INTRO = (
    "Thank you for the Brookside Meadows submission. The following review-support "
    "items were prepared to help organize a response. Each item is a draft "
    "prepared for human review and does not constitute final engineering "
    "approval."
)

DRAFT_CLOSING = (
    "Please direct questions on these review-support items to the reviewing "
    "office. This draft response is intended to support human review and does "
    "not constitute final engineering approval. A licensed Professional Engineer "
    "remains responsible for the review."
)

# Topical sections, in display order. opening_summary, attachments, and
# limitations_and_review_boundary are always present and informational. The
# demand sections only appear when at least one item maps to them.
SECTION_TITLES: dict[str, str] = {
    "opening_summary": "Opening summary",
    "requested_revisions": "Requested revisions",
    "missing_information": "Missing or incomplete information",
    "plan_sheet_items": "Plan sheet items",
    "stormwater_items": "Stormwater items",
    "erosion_control_items": "Erosion and sediment control items",
    "wetland_buffer_items": "Wetland buffer items",
    "attachments": "Attachments",
    "limitations_and_review_boundary": "Limitations and review boundary",
}
DEMAND_SECTION_ORDER = [
    "requested_revisions",
    "missing_information",
    "plan_sheet_items",
    "stormwater_items",
    "erosion_control_items",
    "wetland_buffer_items",
]


class ResponsePackageError(Exception):
    """Raised when a response package operation is not allowed."""

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
            audit_event_id=f"audit_resp_{uuid.uuid4().hex[:12]}",
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


def select_source_workflow_items(items: list) -> tuple[list, bool]:
    """Select the workflow items a response package should be built from.

    Selection tiers, in order:

    1. Items with status ready_for_handoff (the primary source).
    2. If none are ready, items with status needs_follow_up or
       needs_more_information (the package is labeled draft).
    3. If none of those exist either, any item that still requires human review
       and is not excluded (a defensive fallback so the package is not empty).

    Informational limitations items are never promoted as response demands.
    Returns the selected items and a flag that is True when a fallback tier was
    used so the caller can label the package as draft.
    """

    def _eligible(item) -> bool:
        if not getattr(item, "requires_human_review", True):
            return False
        if item.section_type == "limitations":
            return False
        if item.status == "excluded_from_packet":
            return False
        return True

    eligible = [i for i in items if _eligible(i)]
    ready = [i for i in eligible if i.status == "ready_for_handoff"]
    if ready:
        return ready, False
    follow = [
        i
        for i in eligible
        if i.status in {"needs_follow_up", "needs_more_information"}
    ]
    if follow:
        return follow, True
    return eligible, True


def _classify_section(item) -> str:
    """Map a workflow item to a topical response section type."""

    text = f"{item.title} {item.description}".lower()
    if item.status == "needs_more_information" or item.source_type == "document":
        if any(k in text for k in ("missing", "incomplete", "not included", "provide")):
            return "missing_information"
    if any(k in text for k in ("wetland", "buffer", "setback")):
        return "wetland_buffer_items"
    if any(k in text for k in ("erosion", "sediment", "stabilization")):
        return "erosion_control_items"
    if any(k in text for k in ("basin", "stormwater", "drainage", "detention", "outlet", "runoff")):
        return "stormwater_items"
    if item.section_type in {"plan_sheet_cad", "sheet_hotspots"} or item.source_type in {
        "plan_sheet",
        "plan_reference",
        "sheet_hotspot",
    }:
        return "plan_sheet_items"
    if item.status == "needs_more_information":
        return "missing_information"
    return "requested_revisions"


def _draft_text(item, section_type: str) -> str:
    """Draft plain, professional external-review wording for an item.

    The wording avoids final-decision language. It frames each item as a
    review-support request or observation for a human reviewer.
    """

    title = item.title.strip().rstrip(".")
    description = (item.description or "").strip()
    if section_type == "missing_information":
        lead = (
            f"Please provide additional information regarding {title}. The "
            "available materials appear incomplete for review-support purposes."
        )
    elif section_type == "plan_sheet_items":
        lead = (
            f"Please clarify the plan reference for {title}. The review packet "
            "identifies a potential inconsistency to confirm."
        )
    elif section_type in {"stormwater_items", "erosion_control_items", "wetland_buffer_items"}:
        lead = (
            f"The review packet identifies a potential issue related to {title}. "
            "The following item should be reviewed by the design professional."
        )
    else:
        lead = (
            f"The following item should be reviewed by the design professional: "
            f"{title}."
        )
    if description:
        return f"{lead} Reviewer context: {description}"
    return lead


class _Builder:
    """Accumulates sections, items, links, and attachments during generation."""

    def __init__(self, response_package_id: str, project_id: str) -> None:
        self.response_package_id = response_package_id
        self.project_id = project_id
        self.sections: list[models.ResponsePackageSection] = []
        self.items: list[models.ResponsePackageItem] = []
        self.links: list[models.ResponsePackageEvidenceLink] = []
        self.attachments: list[models.ResponsePackageAttachment] = []
        self._order = 0

    def section(
        self,
        section_type: str,
        summary: str,
        *,
        requires_human_review: bool = True,
    ) -> str:
        section_id = f"rsec_{_short()}"
        self.sections.append(
            models.ResponsePackageSection(
                section_id=section_id,
                response_package_id=self.response_package_id,
                title=SECTION_TITLES[section_type],
                section_type=section_type,
                display_order=self._order,
                summary=summary,
                status="draft",
                requires_human_review=requires_human_review,
            )
        )
        self._order += 1
        return section_id

    def item(
        self,
        section_id: str,
        *,
        title: str,
        draft_text: str,
        severity: str,
        source_type: str,
        source_id: str | None,
        assigned_role: str,
        workflow_item_id: str | None = None,
        packet_item_id: str | None = None,
        requires_human_review: bool = True,
        links: list[tuple[str, str, str, str, str | None]] | None = None,
    ) -> None:
        item_id = f"ritem_{_short()}"
        self.items.append(
            models.ResponsePackageItem(
                item_id=item_id,
                response_package_id=self.response_package_id,
                section_id=section_id,
                workflow_item_id=workflow_item_id,
                packet_item_id=packet_item_id,
                title=title,
                draft_text=draft_text,
                reviewer_note=None,
                severity=severity,
                status="draft",
                source_type=source_type,
                source_id=source_id,
                assigned_role=assigned_role,
                requires_human_review=requires_human_review,
                display_order=len(self.items),
            )
        )
        for evidence_type, evidence_id, relationship, label, description in links or []:
            if not evidence_id:
                continue
            self.links.append(
                models.ResponsePackageEvidenceLink(
                    evidence_link_id=f"revl_{_short()}",
                    response_package_id=self.response_package_id,
                    response_item_id=item_id,
                    evidence_type=evidence_type,
                    evidence_id=evidence_id,
                    relationship=relationship,
                    label=label,
                    description=description,
                )
            )

    def attachment(
        self,
        *,
        label: str,
        attachment_type: str,
        source_type: str,
        source_id: str | None,
        description: str | None,
    ) -> None:
        self.attachments.append(
            models.ResponsePackageAttachment(
                attachment_id=f"ratt_{_short()}",
                response_package_id=self.response_package_id,
                label=label,
                attachment_type=attachment_type,
                source_type=source_type,
                source_id=source_id,
                included=True,
                description=description,
                display_order=len(self.attachments),
            )
        )


def _current_package(db: Session, project_id: str) -> models.ResponsePackage | None:
    return db.scalars(
        select(models.ResponsePackage)
        .where(models.ResponsePackage.project_id == project_id)
        .order_by(models.ResponsePackage.created_at.desc())
    ).first()


def _delete_existing(db: Session, project_id: str) -> None:
    # Select only the id column so this does not populate the identity map with
    # ResponsePackage objects that would collide with a freshly inserted row.
    package_ids = list(
        db.scalars(
            select(models.ResponsePackage.response_package_id).where(
                models.ResponsePackage.project_id == project_id
            )
        ).all()
    )
    if not package_ids:
        return
    for model in (
        models.ResponsePackageAction,
        models.ResponsePackageEvidenceLink,
        models.ResponsePackageAttachment,
        models.ResponsePackageItem,
        models.ResponsePackageSection,
    ):
        db.query(model).filter(
            model.response_package_id.in_(package_ids)
        ).delete(synchronize_session=False)
    db.query(models.ResponsePackage).filter(
        models.ResponsePackage.project_id == project_id
    ).delete(synchronize_session=False)
    db.commit()


def _build_attachments(db: Session, builder: _Builder, selected: list) -> None:
    builder.attachment(
        label="Draft review-support response summary",
        attachment_type="review_support_summary",
        source_type="response_package",
        source_id=builder.response_package_id,
        description=(
            "Printable draft review-support summary generated from the workflow "
            "board. Draft material for human review."
        ),
    )
    seen_docs: set[str] = set()
    for item in selected:
        if not item.packet_item_id:
            continue
        for link in review_packet_service.list_evidence_links_for_item(
            db, item.packet_item_id
        ):
            if link.evidence_type == "document" and link.evidence_id not in seen_docs:
                seen_docs.add(link.evidence_id)
                builder.attachment(
                    label=f"Source document: {link.label}",
                    attachment_type="source_document",
                    source_type="document",
                    source_id=link.evidence_id,
                    description=(
                        "Referenced submitted document for reviewer context. "
                        "Not parsed or verified."
                    ),
                )


def generate_response_package(
    db: Session, project_id: str
) -> models.ResponsePackage:
    """Generate a draft external response package for a project.

    Idempotent for the current project unless the existing package status is
    archived: existing non-archived packages are removed and a fresh draft is
    built from the current workflow board. Writes a response_package_generated
    audit event.
    """

    if db.get(models.Project, project_id) is None:
        raise ResponsePackageError("Project not found.", status_code=404)

    existing = _current_package(db, project_id)
    if existing is not None and existing.status == "archived":
        raise ResponsePackageError(
            "The current response package is archived. Generation is paused "
            "until it is reset.",
            status_code=409,
        )

    # Ensure the workflow board exists, then read its items.
    workflow_service.ensure_workflow_board(db, project_id)
    items = workflow_service.list_workflow_items(db, project_id)
    selected, is_fallback = select_source_workflow_items(items)

    packet = None
    packets = review_packet_service.list_review_packets(db, project_id)
    if packets:
        packet = packets[0]

    if existing is not None:
        # Drop the prior package object from the identity map so the fresh
        # insert does not collide on a reused primary key after deletion.
        db.expunge(existing)
    _delete_existing(db, project_id)

    package_id = f"resp_{_short()}"
    status_label = "draft"
    if is_fallback:
        summary = (
            "Draft external response package for Brookside Meadows. No items are "
            "marked ready for handoff yet, so this draft was assembled from open "
            "review-support items and needs reviewer revision before any use."
        )
    else:
        summary = (
            "Draft external response package for Brookside Meadows assembled from "
            "the workflow items marked ready for handoff. Every item needs human "
            "review before any response is issued."
        )

    package = models.ResponsePackage(
        response_package_id=package_id,
        project_id=project_id,
        source_packet_id=packet.packet_id if packet else None,
        title="Brookside Meadows draft review-support response package",
        audience_type=DEFAULT_AUDIENCE,
        status=status_label,
        summary=summary,
        draft_intro=DRAFT_INTRO,
        draft_closing=DRAFT_CLOSING,
        limitations_note=LIMITATIONS_NOTE,
        created_by=GENERATED_BY,
    )
    db.add(package)

    builder = _Builder(package_id, project_id)

    # Opening summary section (informational).
    opening = builder.section(
        "opening_summary",
        "Overview of the draft review-support items prepared for an external "
        "response. Nothing here is a final engineering decision.",
        requires_human_review=False,
    )
    builder.item(
        opening,
        title="Draft external response overview",
        draft_text=(
            f"This draft organizes {len(selected)} review-support items for an "
            "external response. Each item needs human review and does not "
            "constitute final engineering approval."
        ),
        severity="info",
        source_type="project",
        source_id=project_id,
        assigned_role="review_coordinator",
        requires_human_review=False,
    )

    # Demand sections, grouped by topic.
    grouped: dict[str, list] = {}
    for item in selected:
        grouped.setdefault(_classify_section(item), []).append(item)

    for section_type in DEMAND_SECTION_ORDER:
        section_items = grouped.get(section_type)
        if not section_items:
            continue
        sec = builder.section(
            section_type,
            f"Review-support items grouped under {SECTION_TITLES[section_type].lower()}.",
        )
        for item in section_items:
            links: list[tuple[str, str, str, str, str | None]] = []
            if item.workflow_item_id:
                links.append(
                    (
                        "workflow_item",
                        item.workflow_item_id,
                        "source_workflow_item",
                        "Workflow item",
                        None,
                    )
                )
            if item.packet_item_id:
                links.append(
                    (
                        "packet_item",
                        item.packet_item_id,
                        "source_packet_item",
                        "Review packet item",
                        None,
                    )
                )
                for link in review_packet_service.list_evidence_links_for_item(
                    db, item.packet_item_id
                ):
                    links.append(
                        (
                            link.evidence_type,
                            link.evidence_id,
                            link.relationship,
                            link.label,
                            link.description,
                        )
                    )
            builder.item(
                sec,
                title=item.title,
                draft_text=_draft_text(item, section_type),
                severity=item.severity,
                source_type=item.source_type,
                source_id=item.source_id,
                assigned_role=item.assigned_role,
                workflow_item_id=item.workflow_item_id,
                packet_item_id=item.packet_item_id,
                links=links,
            )

    # Attachments section (informational pointer) and the attachment checklist.
    _build_attachments(db, builder, selected)
    attach_sec = builder.section(
        "attachments",
        "Suggested attachments to include with the external response. Review the "
        "attachment checklist and confirm each item.",
        requires_human_review=False,
    )
    builder.item(
        attach_sec,
        title="Attachment checklist",
        draft_text=(
            f"This draft suggests {len(builder.attachments)} attachments. Confirm "
            "each attachment before any response is prepared for issue."
        ),
        severity="info",
        source_type="response_package",
        source_id=package_id,
        assigned_role="review_coordinator",
        requires_human_review=False,
    )

    # Limitations section (informational).
    lim_sec = builder.section(
        "limitations_and_review_boundary",
        "The professional boundary that applies to this draft response package.",
        requires_human_review=False,
    )
    builder.item(
        lim_sec,
        title="Limitations and review boundary",
        draft_text=EXTERNAL_COMMUNICATION_BOUNDARY,
        severity="info",
        source_type="project",
        source_id=project_id,
        assigned_role="review_coordinator",
        requires_human_review=False,
    )

    for section in builder.sections:
        db.add(section)
    for item in builder.items:
        db.add(item)
    for link in builder.links:
        db.add(link)
    for attachment in builder.attachments:
        db.add(attachment)

    db.add(
        models.ResponsePackageAction(
            action_id=f"resp_act_{_short()}",
            response_package_id=package_id,
            response_item_id=None,
            action_type="package_generated",
            previous_status="none",
            new_status=status_label,
            reviewer_note=(
                "Draft response package generated from the workflow board."
            ),
            reviewer_name=GENERATED_BY,
        )
    )

    _audit(
        db,
        project_id=project_id,
        event_type="response_package_generated",
        related_entity_type="response_package",
        related_entity_id=package_id,
        description=(
            f"Draft response package generated with {len(builder.sections)} "
            f"sections and {len(builder.items)} items."
        ),
        metadata={
            "response_package_id": package_id,
            "section_count": len(builder.sections),
            "item_count": len(builder.items),
            "attachment_count": len(builder.attachments),
            "fallback": is_fallback,
        },
    )
    db.commit()
    db.refresh(package)
    return package


def get_package(db: Session, response_package_id: str) -> models.ResponsePackage | None:
    return db.scalars(
        select(models.ResponsePackage).where(
            models.ResponsePackage.response_package_id == response_package_id
        )
    ).first()


def list_response_packages(
    db: Session, project_id: str
) -> list[models.ResponsePackage]:
    stmt = (
        select(models.ResponsePackage)
        .where(models.ResponsePackage.project_id == project_id)
        .order_by(models.ResponsePackage.created_at.desc())
    )
    return list(db.scalars(stmt).all())


def _links_by_item(db: Session, response_package_id: str) -> dict[str, list]:
    links = db.scalars(
        select(models.ResponsePackageEvidenceLink).where(
            models.ResponsePackageEvidenceLink.response_package_id
            == response_package_id
        )
    ).all()
    grouped: dict[str, list] = {}
    for link in links:
        grouped.setdefault(link.response_item_id, []).append(link)
    return grouped


def _items_by_section(db: Session, response_package_id: str) -> dict[str, list]:
    items = db.scalars(
        select(models.ResponsePackageItem)
        .where(
            models.ResponsePackageItem.response_package_id == response_package_id
        )
        .order_by(models.ResponsePackageItem.display_order)
    ).all()
    grouped: dict[str, list] = {}
    for item in items:
        grouped.setdefault(item.section_id, []).append(item)
    return grouped


def list_attachments(db: Session, response_package_id: str) -> list:
    return list(
        db.scalars(
            select(models.ResponsePackageAttachment)
            .where(
                models.ResponsePackageAttachment.response_package_id
                == response_package_id
            )
            .order_by(models.ResponsePackageAttachment.display_order)
        ).all()
    )


def list_actions(db: Session, response_package_id: str) -> list:
    return list(
        db.scalars(
            select(models.ResponsePackageAction)
            .where(
                models.ResponsePackageAction.response_package_id
                == response_package_id
            )
            .order_by(models.ResponsePackageAction.created_at)
        ).all()
    )


def _item_dict(item: models.ResponsePackageItem, links_by_item: dict) -> dict:
    return {
        "item_id": item.item_id,
        "response_package_id": item.response_package_id,
        "section_id": item.section_id,
        "workflow_item_id": item.workflow_item_id,
        "packet_item_id": item.packet_item_id,
        "title": item.title,
        "draft_text": item.draft_text,
        "reviewer_note": item.reviewer_note,
        "severity": item.severity,
        "status": item.status,
        "source_type": item.source_type,
        "source_id": item.source_id,
        "assigned_role": item.assigned_role,
        "requires_human_review": item.requires_human_review,
        "display_order": item.display_order,
        "evidence_links": links_by_item.get(item.item_id, []),
    }


def assemble_package_detail(db: Session, package: models.ResponsePackage) -> dict:
    sections = db.scalars(
        select(models.ResponsePackageSection)
        .where(
            models.ResponsePackageSection.response_package_id
            == package.response_package_id
        )
        .order_by(models.ResponsePackageSection.display_order)
    ).all()
    links_by_item = _links_by_item(db, package.response_package_id)
    items_by_section = _items_by_section(db, package.response_package_id)

    section_dicts = []
    for section in sections:
        section_dicts.append(
            {
                "section_id": section.section_id,
                "response_package_id": section.response_package_id,
                "title": section.title,
                "section_type": section.section_type,
                "display_order": section.display_order,
                "summary": section.summary,
                "status": section.status,
                "requires_human_review": section.requires_human_review,
                "items": [
                    _item_dict(i, links_by_item)
                    for i in items_by_section.get(section.section_id, [])
                ],
            }
        )

    return {
        "response_package_id": package.response_package_id,
        "project_id": package.project_id,
        "source_packet_id": package.source_packet_id,
        "title": package.title,
        "audience_type": package.audience_type,
        "status": package.status,
        "summary": package.summary,
        "draft_intro": package.draft_intro,
        "draft_closing": package.draft_closing,
        "limitations_note": package.limitations_note,
        "created_by": package.created_by,
        "created_at": package.created_at,
        "updated_at": package.updated_at,
        "sections": section_dicts,
        "attachments": list_attachments(db, package.response_package_id),
    }


def get_response_package(db: Session, response_package_id: str) -> dict | None:
    """Return the full package detail and record that it was viewed.

    Read side effect: writes a response_package_viewed audit event.
    """

    package = get_package(db, response_package_id)
    if package is None:
        return None
    _audit(
        db,
        project_id=package.project_id,
        event_type="response_package_viewed",
        related_entity_type="response_package",
        related_entity_id=response_package_id,
        description="Response package viewed.",
        actor_type="reviewer",
        metadata={"response_package_id": response_package_id},
    )
    db.commit()
    return assemble_package_detail(db, package)


def get_response_package_attachments(
    db: Session, response_package_id: str
) -> dict | None:
    """Return the attachment checklist for a package.

    Read side effect: writes a response_package_attachments_viewed audit event.
    """

    package = get_package(db, response_package_id)
    if package is None:
        return None
    attachments = list_attachments(db, response_package_id)
    _audit(
        db,
        project_id=package.project_id,
        event_type="response_package_attachments_viewed",
        related_entity_type="response_package",
        related_entity_id=response_package_id,
        description="Response package attachment checklist viewed.",
        actor_type="reviewer",
        metadata={
            "response_package_id": response_package_id,
            "attachment_count": len(attachments),
        },
    )
    db.commit()
    return {"attachments": attachments}


def _signoff_checklist() -> list[dict]:
    return [
        {
            "label": "Human review still required",
            "detail": (
                "A licensed Professional Engineer or authorized reviewer must "
                "review every item before any response is issued."
            ),
            "confirmed": False,
        },
        {
            "label": "Draft wording reviewed",
            "detail": (
                "Reviewer has read each draft response item and confirmed the "
                "wording is appropriate."
            ),
            "confirmed": False,
        },
        {
            "label": "Evidence traceability checked",
            "detail": (
                "Reviewer has confirmed each item traces back to its workflow "
                "item, packet item, and source evidence."
            ),
            "confirmed": False,
        },
        {
            "label": "No final-decision language",
            "detail": (
                "Reviewer has confirmed the draft does not approve, certify, "
                "verify, or validate anything."
            ),
            "confirmed": False,
        },
        {
            "label": "Not sent",
            "detail": (
                "This system does not send correspondence. Any response is "
                "issued outside the system by an authorized person."
            ),
            "confirmed": False,
        },
    ]


def get_response_package_print_view(
    db: Session, response_package_id: str
) -> dict | None:
    """Return a printable draft response view for a package.

    Read side effect: writes a response_package_print_view_requested audit event.
    """

    package = get_package(db, response_package_id)
    if package is None:
        return None
    detail = assemble_package_detail(db, package)
    print_sections = [
        {
            "title": s["title"],
            "section_type": s["section_type"],
            "summary": s["summary"],
            "items": s["items"],
        }
        for s in detail["sections"]
    ]
    _audit(
        db,
        project_id=package.project_id,
        event_type="response_package_print_view_requested",
        related_entity_type="response_package",
        related_entity_id=response_package_id,
        description="Response package printable draft requested.",
        actor_type="reviewer",
        metadata={"response_package_id": response_package_id},
    )
    db.commit()
    return {
        "response_package_id": package.response_package_id,
        "project_id": package.project_id,
        "title": package.title,
        "audience_type": package.audience_type,
        "status": package.status,
        "summary": package.summary,
        "draft_intro": package.draft_intro,
        "draft_closing": package.draft_closing,
        "created_by": package.created_by,
        "created_at": package.created_at,
        "limitations_note": package.limitations_note,
        "external_communication_boundary": EXTERNAL_COMMUNICATION_BOUNDARY,
        "draft_notice": DRAFT_NOTICE,
        "sections": print_sections,
        "attachments": detail["attachments"],
        "signoff_checklist": _signoff_checklist(),
    }


def get_response_package_history(
    db: Session, response_package_id: str
) -> dict | None:
    """Return the recorded action history for a package.

    Read side effect: writes a response_package_history_requested audit event.
    """

    package = get_package(db, response_package_id)
    if package is None:
        return None
    actions = list_actions(db, response_package_id)
    _audit(
        db,
        project_id=package.project_id,
        event_type="response_package_history_requested",
        related_entity_type="response_package",
        related_entity_id=response_package_id,
        description="Response package history requested.",
        actor_type="reviewer",
        metadata={
            "response_package_id": response_package_id,
            "action_count": len(actions),
        },
    )
    db.commit()
    return {
        "response_package_id": response_package_id,
        "project_id": package.project_id,
        "actions": actions,
        "note": (
            "This is the recorded reviewer activity for the draft response "
            "package. It is review-support history, not a final engineering "
            "decision."
        ),
    }


def summarize_response_package(
    db: Session, response_package_id: str
) -> dict | None:
    package = get_package(db, response_package_id)
    if package is None:
        return None
    sections = db.scalars(
        select(models.ResponsePackageSection).where(
            models.ResponsePackageSection.response_package_id
            == response_package_id
        )
    ).all()
    section_type_by_id = {s.section_id: s.section_type for s in sections}
    items = db.scalars(
        select(models.ResponsePackageItem).where(
            models.ResponsePackageItem.response_package_id == response_package_id
        )
    ).all()
    link_count = (
        db.query(models.ResponsePackageEvidenceLink)
        .filter(
            models.ResponsePackageEvidenceLink.response_package_id
            == response_package_id
        )
        .count()
    )
    attachment_count = (
        db.query(models.ResponsePackageAttachment)
        .filter(
            models.ResponsePackageAttachment.response_package_id
            == response_package_id
        )
        .count()
    )

    by_section: dict[str, int] = {}
    by_status: dict[str, int] = {}
    by_severity: dict[str, int] = {}
    for item in items:
        stype = section_type_by_id.get(item.section_id, "unknown")
        by_section[stype] = by_section.get(stype, 0) + 1
        by_status[item.status] = by_status.get(item.status, 0) + 1
        by_severity[item.severity] = by_severity.get(item.severity, 0) + 1

    return {
        "response_package_id": response_package_id,
        "project_id": package.project_id,
        "status": package.status,
        "audience_type": package.audience_type,
        "total_sections": len(sections),
        "total_items": len(items),
        "total_attachments": attachment_count,
        "total_evidence_links": link_count,
        "items_by_section_type": by_section,
        "items_by_status": by_status,
        "items_by_severity": by_severity,
        "items_requiring_human_review": len(
            [i for i in items if i.requires_human_review]
        ),
    }


def _get_item(
    db: Session, response_package_id: str, response_item_id: str
) -> models.ResponsePackageItem:
    item = db.scalars(
        select(models.ResponsePackageItem).where(
            models.ResponsePackageItem.item_id == response_item_id,
            models.ResponsePackageItem.response_package_id == response_package_id,
        )
    ).first()
    if item is None:
        raise ResponsePackageError(
            "Response item not found for this package.", status_code=404
        )
    return item


def _record_action(
    db: Session,
    *,
    response_package_id: str,
    response_item_id: str | None,
    action_type: str,
    previous_status: str,
    new_status: str,
    reviewer_note: str,
    reviewer_name: str,
) -> models.ResponsePackageAction:
    action = models.ResponsePackageAction(
        action_id=f"resp_act_{_short()}",
        response_package_id=response_package_id,
        response_item_id=response_item_id,
        action_type=action_type,
        previous_status=previous_status,
        new_status=new_status,
        reviewer_note=reviewer_note,
        reviewer_name=reviewer_name,
    )
    db.add(action)
    return action


def update_response_package_status(
    db: Session,
    *,
    response_package_id: str,
    new_status: str,
    reviewer_note: str | None = None,
    reviewer_name: str | None = None,
) -> models.ResponsePackage:
    """Validate and apply a status transition to a response package."""

    package = get_package(db, response_package_id)
    if package is None:
        raise ResponsePackageError(
            "Response package not found.", status_code=404
        )
    if new_status not in ALLOWED_RESPONSE_PACKAGE_STATUSES:
        raise ResponsePackageError(
            f"Unknown response package status '{new_status}'.", status_code=422
        )
    if new_status not in RESPONSE_PACKAGE_STATUS_TO_ACTION:
        raise ResponsePackageError(
            f"Status '{new_status}' is not a valid manual transition.",
            status_code=422,
        )
    note = (reviewer_note or "").strip()
    if find_prohibited_language(note):
        raise ResponsePackageError(
            "reviewer_note contains prohibited final-decision wording.",
            status_code=422,
        )

    previous_status = package.status
    package.status = new_status
    package.updated_at = _now()
    _record_action(
        db,
        response_package_id=response_package_id,
        response_item_id=None,
        action_type=RESPONSE_PACKAGE_STATUS_TO_ACTION[new_status],
        previous_status=previous_status,
        new_status=new_status,
        reviewer_note=note or "Package status updated by reviewer.",
        reviewer_name=(reviewer_name or "reviewer").strip(),
    )
    _audit(
        db,
        project_id=package.project_id,
        event_type="response_package_status_updated",
        related_entity_type="response_package",
        related_entity_id=response_package_id,
        description=(
            f"Response package status updated from {previous_status} to "
            f"{new_status}."
        ),
        actor_type="reviewer",
        metadata={
            "response_package_id": response_package_id,
            "previous_status": previous_status,
            "new_status": new_status,
        },
    )
    db.commit()
    db.refresh(package)
    return package


def update_response_item_status(
    db: Session,
    *,
    response_package_id: str,
    response_item_id: str,
    new_status: str,
    reviewer_note: str | None = None,
    reviewer_name: str | None = None,
) -> models.ResponsePackageItem:
    """Validate and apply a status transition to a response item."""

    item = _get_item(db, response_package_id, response_item_id)
    if new_status not in ALLOWED_RESPONSE_ITEM_STATUSES:
        raise ResponsePackageError(
            f"Unknown response item status '{new_status}'.", status_code=422
        )
    if new_status not in RESPONSE_ITEM_STATUS_TO_ACTION:
        raise ResponsePackageError(
            f"Status '{new_status}' is not a valid manual transition.",
            status_code=422,
        )
    note = (reviewer_note or "").strip()
    if find_prohibited_language(note):
        raise ResponsePackageError(
            "reviewer_note contains prohibited final-decision wording.",
            status_code=422,
        )

    package = get_package(db, response_package_id)
    previous_status = item.status
    item.status = new_status
    if note:
        item.reviewer_note = note
    item.updated_at = _now()
    _record_action(
        db,
        response_package_id=response_package_id,
        response_item_id=response_item_id,
        action_type=RESPONSE_ITEM_STATUS_TO_ACTION[new_status],
        previous_status=previous_status,
        new_status=new_status,
        reviewer_note=note or "Item status updated by reviewer.",
        reviewer_name=(reviewer_name or "reviewer").strip(),
    )
    _audit(
        db,
        project_id=package.project_id,
        event_type="response_item_status_updated",
        related_entity_type="response_item",
        related_entity_id=response_item_id,
        description=(
            f"Response item status updated from {previous_status} to "
            f"{new_status}."
        ),
        actor_type="reviewer",
        metadata={
            "response_package_id": response_package_id,
            "response_item_id": response_item_id,
            "previous_status": previous_status,
            "new_status": new_status,
        },
    )
    db.commit()
    db.refresh(item)
    return item


def update_response_item_draft_text(
    db: Session,
    *,
    response_package_id: str,
    response_item_id: str,
    draft_text: str,
    reviewer_note: str | None = None,
    reviewer_name: str | None = None,
) -> models.ResponsePackageItem:
    """Edit the draft response text of an item.

    Editing the draft text records an item_revised action and moves the item to
    needs_revision so the change is visible in the workflow. Writes a
    response_item_draft_text_updated audit event.
    """

    item = _get_item(db, response_package_id, response_item_id)
    text = (draft_text or "").strip()
    if not text:
        raise ResponsePackageError("draft_text is required.", status_code=422)
    if find_prohibited_language(text):
        raise ResponsePackageError(
            "draft_text contains prohibited final-decision wording.",
            status_code=422,
        )
    note = (reviewer_note or "").strip()
    if find_prohibited_language(note):
        raise ResponsePackageError(
            "reviewer_note contains prohibited final-decision wording.",
            status_code=422,
        )

    previous_status = item.status
    item.draft_text = text
    if note:
        item.reviewer_note = note
    item.status = "needs_revision"
    item.updated_at = _now()
    package = get_package(db, response_package_id)
    _record_action(
        db,
        response_package_id=response_package_id,
        response_item_id=response_item_id,
        action_type="item_revised",
        previous_status=previous_status,
        new_status="needs_revision",
        reviewer_note=note or "Draft text edited by reviewer.",
        reviewer_name=(reviewer_name or "reviewer").strip(),
    )
    _audit(
        db,
        project_id=package.project_id,
        event_type="response_item_draft_text_updated",
        related_entity_type="response_item",
        related_entity_id=response_item_id,
        description="Response item draft text edited.",
        actor_type="reviewer",
        metadata={
            "response_package_id": response_package_id,
            "response_item_id": response_item_id,
        },
    )
    db.commit()
    db.refresh(item)
    return item


def add_response_package_note(
    db: Session,
    *,
    response_package_id: str,
    reviewer_note: str,
    reviewer_name: str,
    response_item_id: str | None = None,
) -> models.ResponsePackageAction:
    """Record a reviewer note on a package or item without changing status."""

    package = get_package(db, response_package_id)
    if package is None:
        raise ResponsePackageError(
            "Response package not found.", status_code=404
        )
    note = (reviewer_note or "").strip()
    if not note:
        raise ResponsePackageError("reviewer_note is required.", status_code=422)
    if not reviewer_name or not reviewer_name.strip():
        raise ResponsePackageError("reviewer_name is required.", status_code=422)
    if find_prohibited_language(note):
        raise ResponsePackageError(
            "reviewer_note contains prohibited final-decision wording.",
            status_code=422,
        )

    current_status = package.status
    if response_item_id is not None:
        item = _get_item(db, response_package_id, response_item_id)
        item.reviewer_note = note
        item.updated_at = _now()
        current_status = item.status

    action = _record_action(
        db,
        response_package_id=response_package_id,
        response_item_id=response_item_id,
        action_type="note_added",
        previous_status=current_status,
        new_status=current_status,
        reviewer_note=note,
        reviewer_name=reviewer_name.strip(),
    )
    _audit(
        db,
        project_id=package.project_id,
        event_type="response_package_note_added",
        related_entity_type="response_package",
        related_entity_id=response_package_id,
        description=f"Reviewer note added by {reviewer_name.strip()}.",
        actor_type="reviewer",
        metadata={
            "response_package_id": response_package_id,
            "response_item_id": response_item_id,
        },
    )
    db.commit()
    db.refresh(action)
    return action


def ensure_response_package(db: Session, project_id: str) -> None:
    """Generate a response package once if none exists for the project.

    Used at startup so the read endpoints and frontend have a package without a
    manual generate call. Gated on no package existing, so it does not regenerate
    on every restart.
    """

    if db.get(models.Project, project_id) is None:
        return
    existing = (
        db.query(models.ResponsePackage)
        .filter(models.ResponsePackage.project_id == project_id)
        .first()
    )
    if existing is None:
        generate_response_package(db, project_id)
