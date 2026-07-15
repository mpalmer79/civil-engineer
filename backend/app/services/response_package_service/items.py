"""Reviewer actions on response packages and items: status, notes, revisions."""

from __future__ import annotations

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

from ._common import _audit, _now, _short
from .errors import ResponsePackageError
from .reads import get_package


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
