"""Shared helpers for the model domain modules."""

from __future__ import annotations

from datetime import datetime, timezone


def _utcnow() -> datetime:
    """Return a timezone-aware UTC timestamp for column defaults.

    Used instead of datetime.utcnow, which is deprecated on Python 3.12 and
    returns a naive datetime. The stored value and column type are unchanged.
    """

    return datetime.now(timezone.utc)
