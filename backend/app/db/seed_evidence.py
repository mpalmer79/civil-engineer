"""Compatibility facade for the Brookside Meadows evidence seed fixture.

The fixture now lives in app.db.seeds.evidence. This module re-exports the
public entry point and fixture constants so existing imports keep working.
Prefer importing from app.db.seeds in new code.
"""

from __future__ import annotations

from app.db.seeds.evidence import (
    CHUNKS,
    FINDING_SOURCES,
    RETRIEVAL_QUERIES,
    evidence_is_loaded,
    seed_evidence,
)

__all__ = [
    "CHUNKS",
    "FINDING_SOURCES",
    "RETRIEVAL_QUERIES",
    "evidence_is_loaded",
    "seed_evidence",
]
