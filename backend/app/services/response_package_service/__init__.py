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

This package preserves the original single-module import path. Callers can
continue to use ``from app.services import response_package_service`` and
``from app.services.response_package_service import name``.
"""

from __future__ import annotations

from ._common import (
    DEFAULT_AUDIENCE,
    DEMAND_SECTION_ORDER,
    DRAFT_CLOSING,
    DRAFT_INTRO,
    DRAFT_NOTICE,
    EXTERNAL_COMMUNICATION_BOUNDARY,
    GENERATED_BY,
    LIMITATIONS_NOTE,
    SECTION_TITLES,
    _audit,
    _now,
    _short,
)
from .assembly import (
    _build_attachments,
    _current_package,
    _delete_existing,
    ensure_response_package,
    generate_response_package,
)
from .builder import _Builder
from .errors import ResponsePackageError
from .items import (
    _get_item,
    _record_action,
    add_response_package_note,
    update_response_item_draft_text,
    update_response_item_status,
    update_response_package_status,
)
from .reads import (
    _item_dict,
    _items_by_section,
    _links_by_item,
    _signoff_checklist,
    assemble_package_detail,
    get_package,
    get_response_package,
    get_response_package_attachments,
    get_response_package_history,
    get_response_package_print_view,
    list_actions,
    list_attachments,
    list_response_packages,
    summarize_response_package,
)
from .sections import (
    _classify_section,
    _draft_text,
    select_source_workflow_items,
)

__all__ = [
    "GENERATED_BY",
    "DEFAULT_AUDIENCE",
    "LIMITATIONS_NOTE",
    "EXTERNAL_COMMUNICATION_BOUNDARY",
    "DRAFT_NOTICE",
    "DRAFT_INTRO",
    "DRAFT_CLOSING",
    "SECTION_TITLES",
    "DEMAND_SECTION_ORDER",
    "ResponsePackageError",
    "select_source_workflow_items",
    "generate_response_package",
    "ensure_response_package",
    "get_package",
    "list_response_packages",
    "list_attachments",
    "list_actions",
    "assemble_package_detail",
    "get_response_package",
    "get_response_package_attachments",
    "get_response_package_print_view",
    "get_response_package_history",
    "summarize_response_package",
    "update_response_package_status",
    "update_response_item_status",
    "update_response_item_draft_text",
    "add_response_package_note",
]
