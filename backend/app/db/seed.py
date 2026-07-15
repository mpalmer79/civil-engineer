"""Compatibility facade for the core Brookside Meadows seed fixture.

The fixture now lives in the app.db.seeds package, split by domain. This module
re-exports the public entry points and fixture constants so existing imports
and the python -m app.db.seed command keep working. Prefer importing from
app.db.seeds in new code.
"""

from __future__ import annotations

from app.db.seeds import (
    AUDIT_EVENTS,
    CHECKLIST,
    DOCUMENTS,
    EVALUATION_CASES,
    FINDINGS,
    HOTSPOTS,
    PROJECT,
    PROJECT_ID,
    main,
    seed_database,
    seed_is_loaded,
)

__all__ = [
    "AUDIT_EVENTS",
    "CHECKLIST",
    "DOCUMENTS",
    "EVALUATION_CASES",
    "FINDINGS",
    "HOTSPOTS",
    "PROJECT",
    "PROJECT_ID",
    "main",
    "seed_database",
    "seed_is_loaded",
]


if __name__ == "__main__":
    main()
