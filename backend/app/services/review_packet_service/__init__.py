"""Review packet builder service for Phase 8.

This service assembles a review-support packet draft for a project from seeded
data created in prior phases: documents, checklist items, findings, plan sheets,
CAD-aware metadata, plan references, plan consistency findings, sheet hotspots,
plan consistency review actions, and audit evidence. The packet organizes
evidence for a human reviewer.

The packet is a review-support draft. It does not approve plans, certify
compliance, stamp drawings, verify CAD, validate a design, or make final
engineering decisions. There is no action called approve.

Read side effects: get_review_packet, get_review_packet_traceability, and
get_review_packet_print_view each write an audit event recording that the packet
was viewed, the traceability matrix was requested, or the print view was
requested. This is intentional so the decision history shows reviewer access.

This package preserves the public import surface of the former single-module
service. Import paths such as app.services.review_packet_service.<name> continue
to resolve unchanged.
"""

from __future__ import annotations

from ._common import (
    DRAFT_NOTICE,
    GENERATED_BY,
    GENERATED_FROM_PHASE,
    LIMITATIONS_NOTE,
    PACKET_TYPE,
    PROFESSIONAL_LIMITATIONS,
    TRACEABILITY_REVIEW_NOTE,
    _audit,
    _now,
    _short,
)
from .errors import ReviewPacketError
from .export import (
    _packet_traceability_review_rows,
    get_review_packet_print_view,
    get_review_packet_traceability,
)
from .items_links import (
    _get_item,
    _packet_project,
    _record_action,
    create_review_packet_reviewer_action,
    list_evidence_links_for_item,
    update_review_packet_item_status,
)
from .lifecycle import (
    _delete_existing,
    ensure_packet,
    generate_review_packet,
)
from .reads import (
    _items_by_section,
    _links_by_item,
    assemble_packet_detail,
    get_packet,
    get_review_packet,
    list_review_packets,
    summarize_review_packet,
)
from .sections import _Builder, _build_sections

__all__ = [
    "DRAFT_NOTICE",
    "GENERATED_BY",
    "GENERATED_FROM_PHASE",
    "LIMITATIONS_NOTE",
    "PACKET_TYPE",
    "PROFESSIONAL_LIMITATIONS",
    "TRACEABILITY_REVIEW_NOTE",
    "ReviewPacketError",
    "_Builder",
    "_audit",
    "_build_sections",
    "_delete_existing",
    "_get_item",
    "_items_by_section",
    "_links_by_item",
    "_now",
    "_packet_project",
    "_packet_traceability_review_rows",
    "_record_action",
    "_short",
    "assemble_packet_detail",
    "create_review_packet_reviewer_action",
    "ensure_packet",
    "generate_review_packet",
    "get_packet",
    "get_review_packet",
    "get_review_packet_print_view",
    "get_review_packet_traceability",
    "list_evidence_links_for_item",
    "list_review_packets",
    "summarize_review_packet",
    "update_review_packet_item_status",
]
