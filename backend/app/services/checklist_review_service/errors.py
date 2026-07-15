"""Error type for the checklist review service."""

from __future__ import annotations


class ChecklistReviewError(Exception):
    """Raised when a checklist review operation is not allowed."""

    def __init__(self, message: str, *, status_code: int = 400) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code
