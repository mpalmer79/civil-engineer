"""Error type for the review packet service."""

from __future__ import annotations


class ReviewPacketError(Exception):
    """Raised when a review packet operation is not allowed."""

    def __init__(self, message: str, *, status_code: int = 400) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code
