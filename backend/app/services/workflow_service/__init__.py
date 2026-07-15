"""Reviewer workflow board service for Phase 9.

This service promotes the review-support items in the latest review packet into
an operational workflow board. A human reviewer can triage each item, request
follow-up or more information, record reviewer notes, mark items reviewer
checked or excluded, and finally mark items ready for handoff to a licensed
Professional Engineer.

The workflow board organizes review-support work. It does not approve plans,
certify compliance, stamp drawings, verify CAD, validate a design, or make
final engineering decisions. There is no action called approve. Handoff means
handing the organized evidence to a human reviewer, not issuing a decision.

Read side effects: get_workflow_item, get_workflow_item_history,
get_workflow_board_summary, and get_ready_for_handoff_summary each write an
audit event recording the access, so the decision history shows reviewer
activity.

This package preserves the public import surface of the former single-module
service. Import paths such as app.services.workflow_service.<name> continue to
resolve unchanged.
"""

from __future__ import annotations

from ._common import (
    BOARD_NOTE,
    DEFAULT_ROLE,
    HANDOFF_NOTE,
    INITIAL_STATUS,
    SECTION_TO_ROLE,
    _audit,
    _now,
    _record_action,
    _short,
)
from .actions import add_workflow_note, update_workflow_item_status
from .board import (
    _delete_existing,
    ensure_workflow_board,
    generate_workflow_items_from_review_packet,
)
from .errors import WorkflowError
from .follow_ups import create_follow_up_request
from .reads import (
    _assemble_item_detail,
    _evidence_links_for_item,
    _open_follow_up_count,
    get_ready_for_handoff_summary,
    get_workflow_board_summary,
    get_workflow_item,
    get_workflow_item_history,
    get_workflow_item_record,
    list_follow_up_requests,
    list_workflow_actions,
    list_workflow_items,
)

__all__ = [
    "BOARD_NOTE",
    "DEFAULT_ROLE",
    "HANDOFF_NOTE",
    "INITIAL_STATUS",
    "SECTION_TO_ROLE",
    "WorkflowError",
    "_assemble_item_detail",
    "_audit",
    "_delete_existing",
    "_evidence_links_for_item",
    "_now",
    "_open_follow_up_count",
    "_record_action",
    "_short",
    "add_workflow_note",
    "create_follow_up_request",
    "ensure_workflow_board",
    "generate_workflow_items_from_review_packet",
    "get_ready_for_handoff_summary",
    "get_workflow_board_summary",
    "get_workflow_item",
    "get_workflow_item_history",
    "get_workflow_item_record",
    "list_follow_up_requests",
    "list_workflow_actions",
    "list_workflow_items",
    "update_workflow_item_status",
]
