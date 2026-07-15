"""Traceability error type."""

from __future__ import annotations


class TraceabilityError(Exception):
    """Raised when a traceability review action is not allowed."""

    def __init__(self, message: str, *, status_code: int = 400) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code
