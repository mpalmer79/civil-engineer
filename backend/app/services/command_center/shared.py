"""Shared helpers and route constants for the command center builders."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

ROUTE_WORKFLOW = "/workflow-board"
ROUTE_CAD_INTAKE = "/cad-intake"
ROUTE_CAD_REVIEW = "/cad-review"
ROUTE_REVIEW_CYCLES = "/review-cycles"
ROUTE_RESPONSE = "/response-package"
ROUTE_PACKET = "/review-packet"
ROUTE_SHEETS = "/plan-sheets"
ROUTE_SHEET_VIEWER = "/sheet-viewer"
ROUTE_DOCUMENTS = "/documents"
ROUTE_CHECKLIST = "/checklist"


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _short() -> str:
    return uuid.uuid4().hex[:12]
