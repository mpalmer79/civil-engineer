"""Compatibility facade for the Brookside Meadows plan sheet seed fixture.

The fixture now lives in app.db.seeds.plan_sheets. This module re-exports the
public entry points and fixture constants so existing imports and the
python -m app.db.seed_plansheets command keep working. Prefer importing from
app.db.seeds in new code.
"""

from __future__ import annotations

from app.db.seeds.plan_sheets import (
    CAD_METADATA,
    PLAN_REFERENCES,
    PLAN_SHEET_HOTSPOTS,
    PLAN_SHEETS,
    PROJECT_ID,
    main,
    plan_data_is_loaded,
    seed_plansheets,
)

__all__ = [
    "CAD_METADATA",
    "PLAN_REFERENCES",
    "PLAN_SHEETS",
    "PLAN_SHEET_HOTSPOTS",
    "PROJECT_ID",
    "main",
    "plan_data_is_loaded",
    "seed_plansheets",
]


if __name__ == "__main__":
    main()
