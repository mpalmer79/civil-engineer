"""Evidence retrieval and reviewer draft finding queue vocabulary and limits."""

from __future__ import annotations

# Production Foundations Sprint 3 evidence retrieval and reviewer draft finding
# queue vocabulary. Retrieval is deterministic and local over indexed PDF page
# text. A retrieval result is a candidate for reviewer evaluation, never a
# conclusion. None of these values implies a final engineering decision,
# approval, certification, compliance state, or that a design is safe.

# Retrieval query types a reviewer may run against indexed page text. combined
# allows a keyword query that also carries metadata filters.
ALLOWED_RETRIEVAL_QUERY_TYPES: set[str] = {
    "keyword",
    "phrase",
    "checklist_item",
    "finding_context",
    "document_filter",
    "combined",
    # Keyword search over real-derived DocumentChunk rows (chunks built from
    # indexed PDF page text). Distinct from the page-text "keyword" search.
    "chunk_keyword",
    # Semantic search over real-derived chunk embeddings.
    "chunk_semantic",
    # Hybrid keyword plus semantic search over real-derived chunks.
    "chunk_hybrid",
}

# Evidence candidate statuses. Every value keeps the candidate under reviewer
# control. promoted_to_draft records that a reviewer promoted the candidate into
# a draft finding; it is not a final outcome. There is intentionally no
# approved, verified, passed, failed, resolved, or closed value.
ALLOWED_CANDIDATE_STATUSES: set[str] = {
    "retrieval_candidate",
    "saved_for_review",
    "needs_reviewer_triage",
    "reviewer_selected",
    "promoted_to_draft",
    "dismissed_by_reviewer",
}

# How an evidence candidate entered the queue. manual_save records a candidate a
# reviewer saved directly; the search origins record which retrieval mode
# surfaced it.
ALLOWED_CANDIDATE_ORIGINS: set[str] = {
    "keyword_search",
    "phrase_search",
    "checklist_search",
    "finding_context_search",
    "manual_save",
    # A candidate surfaced by searching real-derived DocumentChunk rows.
    "chunk_search",
}

# Maximum number of retrieval results returned in a single search. Keeps result
# lists small and review-friendly and bounds audit metadata counts.
MAX_RETRIEVAL_RESULTS: int = 50

# Minimum length of a retrieval query string. Shorter queries are rejected as a
# validation error rather than scanning every page for one or two characters.
MIN_RETRIEVAL_QUERY_LENGTH: int = 2
