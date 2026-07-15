"""Project-wide traceability aggregation and reviewer review actions (Phase 4A/4B).

This service aggregates relationships that already exist between project checklist
items, evidence links, citations, candidates, documents and pages, findings,
workflow items, and review packets. The aggregation (build_project_traceability)
is read-only: it organizes existing links, runs no analysis engine, calls no AI
provider, mutates no data, and never determines whether a requirement is
satisfied. Every row is review-support context that requires reviewer
confirmation.

Phase 4B adds reviewer-controlled review actions on a single traceability row.
Because traceability rows are computed and have no stable stored primary key, a
review action is keyed by a stable traceability_row_key derived from the row's
existing entity IDs (checklist item, evidence citation or candidate, finding, and
relationship), not by the positional row id. Recording an action is append-only:
it writes one TraceabilityReviewAction row and one audit event, and it never
mutates the checklist item, evidence, finding, workflow item, or packet the row
references. reviewer_confirmed_link means the reviewer confirmed the link is
useful for review only; it does not mean the requirement is satisfied, approved,
certified, verified, validated, or compliant.

The aggregation deliberately preserves four distinct states:

* no_linked_evidence_yet: the checklist item has no linked evidence, citation, or
  candidate. This is not a statement that the requirement is unsupported.
* not_enough_indexed_information: there is no linked evidence and the project has
  no indexed, searchable document pages yet.
* not_reviewed: linked evidence exists but the reviewer has not confirmed it.
* linked_evidence_exists: evidence is linked, still review-support only.

This package preserves the original ``traceability_service`` import path: every
public name and the private helpers other modules and tests rely on are
re-exported here so imports stay unchanged.
"""

from __future__ import annotations

from app.services.traceability_service._common import (
    LIMITATIONS_NOTE,
    MAX_PACKET_CONTEXTS,
    _CHECKLIST_REVIEWED,
    _document_map,
    _document_name,
    _has_indexed_pages,
    _LINK_NEEDS_CONFIRM,
    _now,
    _source_links,
    _workflow_items_by_finding,
    build_row_key,
)
from app.services.traceability_service.errors import TraceabilityError
from app.services.traceability_service.matrix import build_project_traceability
from app.services.traceability_service.reads import (
    HANDOFF_READINESS_NOTE,
    _READY_ACTIONS,
    _action_dict,
    _build_handoff_readiness,
    _contexts_for_item,
    _latest_actions_by_key,
    _packet_context_index,
)
from app.services.traceability_service.review_actions import (
    list_traceability_review_actions,
    record_traceability_review_action,
)

__all__ = [
    "MAX_PACKET_CONTEXTS",
    "LIMITATIONS_NOTE",
    "build_row_key",
    "build_project_traceability",
    "HANDOFF_READINESS_NOTE",
    "TraceabilityError",
    "record_traceability_review_action",
    "list_traceability_review_actions",
]
