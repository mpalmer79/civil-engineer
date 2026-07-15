"""Phase 14 reviewer command center and project health dashboard service.

This service aggregates the existing review-support data across all phases into a
single operational view for a human reviewer: a command center snapshot, project
health metrics, reviewer attention items with a recommended next step, a project
timeline of meaningful events, review readiness checks, reviewer notes, next
steps, and module links into the existing modules.

The dashboard organizes review-support work and links into existing modules
rather than replacing them. It does not approve plans, certify compliance, stamp
drawings, verify CAD, validate design, declare a project safe, close or resolve
issues, or make final engineering decisions. ready_for_human_review means an area
is organized enough for human review, never that it is complete, passed, or
approved. There is no action called approve.

Read side effects: get_project_command_center, get_latest_command_center_snapshot,
get_project_health_metrics, get_reviewer_attention_items, get_project_timeline,
get_review_readiness_checks, get_dashboard_reviewer_notes, get_reviewer_next_steps,
get_project_module_links, and get_project_health_summary each write an audit event
recording reviewer access. This is intentional so the decision history shows
reviewer access.

This package preserves the original ``command_center_service`` import path: every
public name and the private helpers other modules and tests rely on are
re-exported here so imports stay unchanged.
"""

from __future__ import annotations

from app.services.command_center_service._common import (
    LIMITATIONS_NOTE,
    ROUTE_CAD_INTAKE,
    ROUTE_CAD_REVIEW,
    ROUTE_CHECKLIST,
    ROUTE_DOCUMENTS,
    ROUTE_PACKET,
    ROUTE_RESPONSE,
    ROUTE_REVIEW_CYCLES,
    ROUTE_SHEET_VIEWER,
    ROUTE_SHEETS,
    ROUTE_WORKFLOW,
    _attention_for,
    _audit,
    _gather,
    _metrics_for,
    _now,
    _readiness_for,
    _require_project,
    _short,
    _SEVERITY_RANK,
    get_latest_snapshot_record,
)
from app.services.command_center_service.errors import CommandCenterError
from app.services.command_center_service.metrics import (
    _module_links_payload,
    get_project_health_metrics,
    get_project_health_summary,
    get_project_module_links,
)
from app.services.command_center_service.queues import (
    _delete_previous_snapshots,
    _ensure_snapshot,
    _overall_status,
    _summary_text,
    generate_command_center_snapshot,
)
from app.services.command_center_service.reads import (
    add_dashboard_reviewer_note,
    ensure_command_center,
    get_dashboard_reviewer_notes,
    get_latest_command_center_snapshot,
    get_project_command_center,
    get_reviewer_attention_items,
    get_reviewer_next_steps,
    get_review_readiness_checks,
    update_attention_item_status,
)
from app.services.command_center_service.timeline import get_project_timeline

__all__ = [
    "LIMITATIONS_NOTE",
    "ROUTE_WORKFLOW",
    "ROUTE_CAD_INTAKE",
    "ROUTE_CAD_REVIEW",
    "ROUTE_REVIEW_CYCLES",
    "ROUTE_RESPONSE",
    "ROUTE_PACKET",
    "ROUTE_SHEETS",
    "ROUTE_SHEET_VIEWER",
    "ROUTE_DOCUMENTS",
    "ROUTE_CHECKLIST",
    "CommandCenterError",
    "generate_command_center_snapshot",
    "get_latest_snapshot_record",
    "get_latest_command_center_snapshot",
    "get_project_health_metrics",
    "get_reviewer_attention_items",
    "update_attention_item_status",
    "get_project_timeline",
    "get_review_readiness_checks",
    "add_dashboard_reviewer_note",
    "get_dashboard_reviewer_notes",
    "get_reviewer_next_steps",
    "get_project_module_links",
    "get_project_health_summary",
    "get_project_command_center",
    "ensure_command_center",
]
