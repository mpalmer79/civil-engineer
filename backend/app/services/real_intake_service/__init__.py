"""Real project intake and persistent review record service.

Production Foundations Sprint 1 adds the first real-world foundation layer on
top of the seeded Brookside Meadows demo. A reviewer can create a real project
record, register or upload documents, create reviewer-owned review-support
findings, attach basic evidence references, and produce durable audit events.

Nothing here approves plans, certifies compliance, stamps drawings, verifies
CAD, validates design, declares a project safe, resolves or closes an issue, or
makes a final engineering decision. Every record stays review-support only and
under human review. There is no action called approve.

Brookside Meadows remains a seeded demo fixture (source_mode demo_fixture);
records created through this service are source_mode user_created. Live AI
calls, real authentication, PDF parsing, and jurisdiction rule packs are out of
scope for this sprint and tracked on the roadmap.

This module was split into a package (errors, _common, projects, documents,
findings). The public surface is unchanged: both
`from app.services import real_intake_service` and
`from app.services.real_intake_service import <name>` keep working.
"""

from __future__ import annotations

from app.core.config import get_settings
from app.core.safety import (
    ALLOWED_DOCUMENT_PROCESSING_STATUSES,
    ALLOWED_EVIDENCE_STATUSES,
    ALLOWED_PROJECT_STATUSES,
    ALLOWED_REVIEWER_FINDING_STATUSES,
    reject_prohibited_language,
)
from app.db import models

from app.services.real_intake_service.errors import IntakeError
from app.services.real_intake_service._common import (
    DEMO_ACTOR_ID,
    DEMO_ACTOR_NAME,
    REVIEW_SUPPORT_NOTE,
    _now,
    _require_project,
    _short,
    ensure_demo_actor,
    record_audit_event,
)
from app.services.real_intake_service.projects import (
    _counts,
    create_project,
    get_project_detail,
    list_project_details,
    project_detail_dict,
)
from app.services.real_intake_service.documents import (
    register_document,
    save_uploaded_project_file,
    upload_document,
    validate_project_upload,
)
from app.services.real_intake_service.findings import (
    create_evidence_reference,
    create_finding,
    list_evidence_references,
)

# Re-export allowed status sets for documentation and validation reuse.
__all__ = [
    "IntakeError",
    "DEMO_ACTOR_ID",
    "DEMO_ACTOR_NAME",
    "ALLOWED_PROJECT_STATUSES",
    "ALLOWED_DOCUMENT_PROCESSING_STATUSES",
    "ensure_demo_actor",
    "record_audit_event",
    "create_project",
    "list_project_details",
    "get_project_detail",
    "register_document",
    "upload_document",
    "create_finding",
    "create_evidence_reference",
    "list_evidence_references",
]
