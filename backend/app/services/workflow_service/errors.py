"""Error type for the workflow board service."""

from __future__ import annotations


class WorkflowError(Exception):
    """Raised when a workflow board operation is not allowed."""

    def __init__(self, message: str, *, status_code: int = 400) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code
