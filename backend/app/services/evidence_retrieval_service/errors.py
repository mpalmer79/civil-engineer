"""Retrieval error type and tuning constants.

This module holds the RetrievalError raised across the retrieval package and the
numeric tuning constants that shape ranking. The result-count and query-length
bounds are sourced from app.core.safety and re-exported here so callers can keep
reading them from the retrieval namespace.
"""

from __future__ import annotations

from app.core.safety import (
    MAX_RETRIEVAL_RESULTS,
    MIN_RETRIEVAL_QUERY_LENGTH,
)

# Minimum cosine similarity for a semantic match to be surfaced, and the
# Reciprocal Rank Fusion constant used to combine keyword and semantic rankings.
_SEMANTIC_MIN_SIMILARITY = 0.1
_RRF_K = 60


class RetrievalError(Exception):
    """Raised when a retrieval or candidate queue operation is not allowed."""

    def __init__(self, message: str, *, status_code: int = 400) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code


__all__ = [
    "RetrievalError",
    "MAX_RETRIEVAL_RESULTS",
    "MIN_RETRIEVAL_QUERY_LENGTH",
    "_SEMANTIC_MIN_SIMILARITY",
    "_RRF_K",
]
