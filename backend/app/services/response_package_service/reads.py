"""Read-side projections and audited read views for response packages.

Read side effects: get_response_package, get_response_package_print_view,
get_response_package_attachments, and get_response_package_history each write an
audit event recording the access. This is intentional so the decision history
shows reviewer access.
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import models

from ._common import DRAFT_NOTICE, EXTERNAL_COMMUNICATION_BOUNDARY, _audit


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
