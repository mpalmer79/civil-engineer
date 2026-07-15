"""Error type for the reviewer response package service."""

from __future__ import annotations


class ReviewerResponsePackageError(Exception):
    """Raised when a response package operation is not allowed."""

    def __init__(self, message: str, *, status_code: int = 400) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code
