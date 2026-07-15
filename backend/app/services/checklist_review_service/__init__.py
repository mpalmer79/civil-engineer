"""Checklist-driven evidence review and rule pack foundation service (Sprint 4).

Production Foundations Sprint 4 adds the first reusable, versioned checklist
foundation for real projects. A reviewer can attach a starter rule pack to a
project as a checklist, search indexed evidence against each checklist
requirement, track reviewer-controlled checklist evidence status, link citations,
and create draft findings from checklist items.

Everything here is review-support only. A rule pack is a reusable review-support
template, not a legal ordinance, not a compliance standard, and not a binding
requirement set. Checklist status is review-support only. Nothing here approves
plans, certifies compliance, verifies CAD, validates design, declares a project
safe, resolves or closes an issue, or makes a final engineering decision. Draft
findings require reviewer confirmation. There are no live AI calls.

Audit metadata records ids, statuses, counts, and safe labels only. It never
records full extracted page text, raw server file paths, secrets, or API keys.

This module was split into a package (errors, _common, rule_packs, checklists,
review_actions, evidence_links, draft_findings). The public surface is
unchanged: both `from app.services import checklist_review_service` and
`from app.services.checklist_review_service import <name>` keep working.
"""

from __future__ import annotations

from app.core.safety import (
    ALLOWED_CHECKLIST_APPLICABILITY_STATUSES,
    ALLOWED_CHECKLIST_EVIDENCE_STATUSES,
    ALLOWED_CHECKLIST_LINK_STATUSES,
    ALLOWED_CHECKLIST_REVIEW_STATUSES,
    ALLOWED_EVIDENCE_STATUSES,
    ALLOWED_PROJECT_CHECKLIST_STATUSES,
    ALLOWED_REVIEWER_FINDING_STATUSES,
    reject_prohibited_language,
)
from app.db import models
from app.services import evidence_retrieval_service
from app.services.pdf_indexing_service import create_evidence_citation
from app.services.real_intake_service import (
    DEMO_ACTOR_ID,
    DEMO_ACTOR_NAME,
    _now,
    _short,
    ensure_demo_actor,
    record_audit_event,
)

from app.services.checklist_review_service.errors import ChecklistReviewError
from app.services.checklist_review_service._common import (
    _checklist_items,
    _require_project,
    get_checklist_item,
)
from app.services.checklist_review_service.rule_packs import (
    STARTER_REFERENCE_LABEL,
    STARTER_RULE_PACK_ID,
    STARTER_RULE_PACK_ITEMS,
    STARTER_RULE_PACK_NAME,
    _rule_pack_dict,
    _rule_pack_item_dict,
    _rule_pack_items,
    ensure_starter_rule_pack,
    get_rule_pack,
    list_rule_packs,
)
from app.services.checklist_review_service.checklists import (
    _checklist_dict,
    create_project_checklist_from_rule_pack,
    get_project_checklist,
    list_project_checklist_items,
    list_project_checklists,
)
from app.services.checklist_review_service.review_actions import (
    search_evidence_for_checklist_item,
    update_project_checklist_item,
)
from app.services.checklist_review_service.evidence_links import (
    link_citation_to_checklist_item,
    list_checklist_item_evidence_links,
)
from app.services.checklist_review_service.draft_findings import (
    create_draft_finding_from_checklist_item,
)

__all__ = [
    "ChecklistReviewError",
    "STARTER_RULE_PACK_ID",
    "STARTER_RULE_PACK_NAME",
    "STARTER_REFERENCE_LABEL",
    "STARTER_RULE_PACK_ITEMS",
    "ensure_starter_rule_pack",
    "list_rule_packs",
    "get_rule_pack",
    "create_project_checklist_from_rule_pack",
    "list_project_checklists",
    "get_project_checklist",
    "list_project_checklist_items",
    "get_checklist_item",
    "update_project_checklist_item",
    "search_evidence_for_checklist_item",
    "link_citation_to_checklist_item",
    "list_checklist_item_evidence_links",
    "create_draft_finding_from_checklist_item",
]
