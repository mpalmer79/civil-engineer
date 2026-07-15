"""Deterministic, local evidence retrieval and reviewer draft finding queue.

Production Foundations Sprint 3 adds a trustworthy retrieval layer over the
Sprint 2 indexed PDF page text, plus a reviewer-controlled queue of evidence
candidates that a human reviewer can promote into draft review-support findings.

Retrieval is deterministic and local. It ranks indexed DocumentPage rows by
keyword overlap, exact phrase match, document metadata match, and keyword
density, and it reports a plain ranking reason for each result. It does not use
embeddings, OCR, or any external service, and it never calls an AI provider.
Every retrieval result is a candidate for reviewer evaluation, not a conclusion.

Nothing here approves plans, certifies compliance, verifies CAD, validates
design, declares a project safe, resolves or closes an issue, or makes a final
engineering decision. A reviewer must act to save, promote, or dismiss a
candidate; the system never auto-promotes. Promotion creates a reviewer draft
finding and a page-level citation; it never finalizes a review outcome.

Search results and audit metadata never include full extracted page text, raw
server file paths, secrets, or API keys. Only short excerpts, counts, and
statuses are surfaced.

This module was split into a package (errors, _common, page_search,
chunk_search, candidates). The public surface is unchanged: both
`from app.services import evidence_retrieval_service` and
`from app.services.evidence_retrieval_service import <name>` keep working.
"""

from __future__ import annotations

from app.core.safety import (
    ALLOWED_CANDIDATE_ORIGINS,
    ALLOWED_CANDIDATE_STATUSES,
    ALLOWED_EVIDENCE_STATUSES,
    ALLOWED_RETRIEVAL_QUERY_TYPES,
    ALLOWED_REVIEWER_FINDING_STATUSES,
    MAX_RETRIEVAL_RESULTS,
    MIN_RETRIEVAL_QUERY_LENGTH,
    reject_prohibited_language,
)
from app.db import models

from app.services.evidence_retrieval_service.errors import (
    RetrievalError,
    _RRF_K,
    _SEMANTIC_MIN_SIMILARITY,
)
from app.services.evidence_retrieval_service._common import (
    _EXCERPT_LIMIT,
    _EXCERPT_WINDOW,
    _checklist_query_text,
    _document_display_name,
    _document_map,
    _excerpt_around,
    _finding_query_text,
    _indexed_pages,
    _record_retrieval_query,
    _require_project,
    _safe_filter_metadata,
    _tokens,
)
from app.services.evidence_retrieval_service.page_search import (
    _ORIGIN_BY_QUERY_TYPE,
    _result_dict,
    _result_message,
    _run_search,
    _score_page,
    search_by_checklist_item,
    search_by_finding_context,
    search_project_evidence,
)
from app.services.evidence_retrieval_service.chunk_search import (
    _CHUNK_MODE_QUERY_TYPE,
    _chunk_result_dict,
    _chunk_result_message,
    _collect_searchable_chunks,
    _hybrid_chunk_results,
    _keyword_chunk_results,
    _page_lookup,
    _real_derived_chunks,
    _score_chunk_evidence,
    _semantic_chunk_results,
    search_project_chunk_evidence,
)
from app.services.evidence_retrieval_service.candidates import (
    dismiss_candidate,
    get_candidate,
    list_project_candidates,
    list_retrieval_queries,
    promote_candidate_to_draft_finding,
    save_candidate,
    update_candidate_status,
)

__all__ = [
    # Error type and tuning constants
    "RetrievalError",
    "MAX_RETRIEVAL_RESULTS",
    "MIN_RETRIEVAL_QUERY_LENGTH",
    "_SEMANTIC_MIN_SIMILARITY",
    "_RRF_K",
    "_EXCERPT_LIMIT",
    "_EXCERPT_WINDOW",
    "_ORIGIN_BY_QUERY_TYPE",
    "_CHUNK_MODE_QUERY_TYPE",
    # Safety re-exports (part of the original module namespace)
    "ALLOWED_CANDIDATE_ORIGINS",
    "ALLOWED_CANDIDATE_STATUSES",
    "ALLOWED_EVIDENCE_STATUSES",
    "ALLOWED_RETRIEVAL_QUERY_TYPES",
    "ALLOWED_REVIEWER_FINDING_STATUSES",
    "reject_prohibited_language",
    "models",
    # Shared helpers
    "_require_project",
    "_tokens",
    "_indexed_pages",
    "_document_map",
    "_document_display_name",
    "_excerpt_around",
    "_safe_filter_metadata",
    "_record_retrieval_query",
    "_checklist_query_text",
    "_finding_query_text",
    # Page-text search
    "_score_page",
    "_result_dict",
    "_run_search",
    "_result_message",
    "search_project_evidence",
    "search_by_checklist_item",
    "search_by_finding_context",
    # Real-derived chunk search
    "_real_derived_chunks",
    "_page_lookup",
    "_score_chunk_evidence",
    "_chunk_result_dict",
    "_chunk_result_message",
    "_collect_searchable_chunks",
    "_keyword_chunk_results",
    "_semantic_chunk_results",
    "_hybrid_chunk_results",
    "search_project_chunk_evidence",
    # Candidate queue and promotion
    "save_candidate",
    "list_project_candidates",
    "list_retrieval_queries",
    "get_candidate",
    "update_candidate_status",
    "dismiss_candidate",
    "promote_candidate_to_draft_finding",
]
