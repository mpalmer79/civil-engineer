"""Reviewer response package service (Sprint 8).

Production Foundations Sprint 8 adds the first reviewer-controlled output
workflow. A reviewer assembles selected review-support records (findings,
checklist items, response matrix items, citations, document references,
resubmittal summaries, and manual reviewer notes) into a response package, then
generates a deterministic comment letter draft from the package.

Everything here is review-support communication. Issuing a package records that a
reviewer issued a communication. It never approves a project, certifies
compliance, verifies CAD, validates design, declares safety, resolves an issue,
or closes an issue. A revision never overwrites a prior issued record. Nothing
here makes a final engineering decision.

Audit metadata records ids, statuses, and counts only. It never records full
comment letter text, full applicant response text, full extracted page text,
storage keys, raw server file paths, secrets, or tokens.

This package preserves the original single-module import path. Callers can
continue to use ``from app.services import reviewer_response_package_service``
and ``from app.services.reviewer_response_package_service import name``.
"""

from __future__ import annotations

from ._common import (
    _actor_name,
    _next_sort_order,
    _now,
    _require_item,
    _require_package,
    _require_project,
    _short,
)
from .build import (
    _add_item,
    _finalize_added,
    add_checklist_items_to_package,
    add_citations_to_package,
    add_findings_to_package,
    add_manual_package_item,
    add_matrix_items_to_package,
    create_response_package,
    update_package_item,
)
from .errors import ReviewerResponsePackageError
from .lifecycle import (
    PACKAGE_BOUNDARY_STATEMENT,
    create_package_revision,
    issue_response_package,
    mark_package_ready_for_handoff,
    preview_response_package,
)
from .reads import (
    _item_dict,
    _package_detail,
    _package_dict,
    _package_items,
    get_response_package,
    list_package_items,
    list_response_packages,
)

__all__ = [
    "ReviewerResponsePackageError",
    "create_response_package",
    "list_response_packages",
    "get_response_package",
    "add_matrix_items_to_package",
    "add_findings_to_package",
    "add_checklist_items_to_package",
    "add_citations_to_package",
    "add_manual_package_item",
    "update_package_item",
    "preview_response_package",
    "mark_package_ready_for_handoff",
    "issue_response_package",
    "create_package_revision",
    "list_package_items",
    "PACKAGE_BOUNDARY_STATEMENT",
]
