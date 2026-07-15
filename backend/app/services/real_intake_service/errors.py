"""Error type for the real project intake service."""

from __future__ import annotations


class IntakeError(Exception):
    """Raised when a real intake operation is not allowed."""

    def __init__(self, message: str, *, status_code: int = 400) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code
