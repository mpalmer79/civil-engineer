"""Generation and lifecycle of the draft external response package."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import models
from app.services import review_packet_service, workflow_service

from ._common import (
    DEFAULT_AUDIENCE,
    DEMAND_SECTION_ORDER,
    DRAFT_CLOSING,
    DRAFT_INTRO,
    EXTERNAL_COMMUNICATION_BOUNDARY,
    GENERATED_BY,
    LIMITATIONS_NOTE,
    SECTION_TITLES,
    _audit,
    _short,
)
from .builder import _Builder
from .errors import ResponsePackageError
from .sections import _classify_section, _draft_text, select_source_workflow_items


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
