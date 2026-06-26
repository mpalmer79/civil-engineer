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
"""

from __future__ import annotations

import hashlib
import uuid
from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.safety import (
    ALLOWED_DOCUMENT_PROCESSING_STATUSES,
    ALLOWED_EVIDENCE_STATUSES,
    ALLOWED_PROJECT_STATUSES,
    ALLOWED_REVIEWER_FINDING_STATUSES,
    reject_prohibited_language,
)
from app.db import models
from app.services.auth_service import ActorContext, audit_kwargs
from app.services.storage import storage_service
from app.services.storage.base import StorageError

# Fixed identity for the Sprint 1 demo reviewer. Real authentication will
# replace this placeholder; it grants no access and is attribution only.
DEMO_ACTOR_ID = "actor_demo_reviewer"
DEMO_ACTOR_NAME = "Demo Reviewer"

REVIEW_SUPPORT_NOTE = (
    "Review-support record only. It does not approve plans, certify compliance, "
    "verify CAD, validate design, or replace a licensed Professional Engineer. "
    "It requires human review."
)


class IntakeError(Exception):
    """Raised when a real intake operation is not allowed."""

    def __init__(self, message: str, *, status_code: int = 400) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _short() -> str:
    return uuid.uuid4().hex[:12]


# ---------------------------------------------------------------------------
# Actor and audit helpers
# ---------------------------------------------------------------------------


def ensure_demo_actor(db: Session) -> models.Actor:
    """Create the Sprint 1 demo reviewer identity if it does not exist."""

    actor = db.get(models.Actor, DEMO_ACTOR_ID)
    if actor is None:
        actor = models.Actor(
            actor_id=DEMO_ACTOR_ID,
            display_name=DEMO_ACTOR_NAME,
            actor_type="reviewer",
            organization_name="Municipal Review Team (demo)",
            role_label="Stormwater Reviewer (demo)",
            created_at=_now(),
        )
        db.add(actor)
    return actor


def record_audit_event(
    db: Session,
    *,
    project_id: str,
    event_type: str,
    related_entity_type: str,
    related_entity_id: str,
    description: str,
    actor_type: str = "reviewer",
    actor_id: str | None = DEMO_ACTOR_ID,
    actor_display_name: str | None = DEMO_ACTOR_NAME,
    metadata: dict | None = None,
    request_id: str | None = None,
    user_id: str | None = None,
    user_email: str | None = None,
    organization_id: str | None = None,
    access_level: str | None = None,
) -> models.AuditEvent:
    """Create a durable audit event for a real action.

    Never stores secrets, tokens, passwords, password hashes, raw IP addresses,
    or raw user agents. event_metadata holds only non-sensitive structured
    context. When a signed-in user takes the action (Sprint 5), the user and
    organization identity is recorded for real attribution.
    """

    event = models.AuditEvent(
        audit_event_id=f"audit_{_short()}",
        project_id=project_id,
        event_type=event_type,
        actor_type=actor_type,
        actor_id=actor_id,
        actor_display_name=actor_display_name,
        related_entity_type=related_entity_type,
        related_entity_id=related_entity_id,
        description=description,
        timestamp=_now(),
        event_metadata=metadata or {},
        request_id=request_id,
        user_id=user_id,
        user_email=user_email,
        organization_id=organization_id,
        access_level=access_level,
    )
    db.add(event)
    return event


# ---------------------------------------------------------------------------
# Projects
# ---------------------------------------------------------------------------


def _counts(db: Session, project_id: str) -> dict[str, int]:
    document_count = db.scalar(
        select(func.count())
        .select_from(models.Document)
        .where(models.Document.project_id == project_id)
    )
    finding_count = db.scalar(
        select(func.count())
        .select_from(models.Finding)
        .where(models.Finding.project_id == project_id)
    )
    audit_event_count = db.scalar(
        select(func.count())
        .select_from(models.AuditEvent)
        .where(models.AuditEvent.project_id == project_id)
    )
    return {
        "document_count": int(document_count or 0),
        "finding_count": int(finding_count or 0),
        "audit_event_count": int(audit_event_count or 0),
    }


def project_detail_dict(db: Session, project: models.Project) -> dict:
    """Build a detail dict (project metadata plus counts) for a project."""

    counts = _counts(db, project.project_id)
    return {
        "project_id": project.project_id,
        "project_name": project.project_name,
        "project_type": project.project_type,
        "location_context": project.location_context,
        "jurisdiction": project.jurisdiction,
        "review_type": project.review_type,
        "review_domain": project.review_domain,
        "acreage": project.acreage,
        "disturbed_area": project.disturbed_area,
        "proposed_lots": project.proposed_lots,
        "status": project.status,
        "summary": project.summary,
        "site_conditions": project.site_conditions or [],
        "proposed_improvements": project.proposed_improvements or [],
        "known_constraints": project.known_constraints or [],
        "source_mode": project.source_mode or "demo_fixture",
        "created_by_name": project.created_by_name,
        "created_by_actor_id": project.created_by_actor_id,
        "applicant_name": project.applicant_name,
        "applicant_organization": project.applicant_organization,
        "design_engineer_name": project.design_engineer_name,
        "design_firm": project.design_firm,
        "submission_reference": project.submission_reference,
        "review_round_current": project.review_round_current or 1,
        "parcel_ids": project.parcel_ids or [],
        "organization_id": project.organization_id,
        "created_by_user_id": project.created_by_user_id,
        "visibility_mode": project.visibility_mode or "controlled",
        "demo_public": bool(project.demo_public),
        "assigned_reviewer_user_id": project.assigned_reviewer_user_id,
        "assigned_reviewer_name": project.assigned_reviewer_name,
        "review_priority": project.review_priority,
        "review_due_date": project.review_due_date,
        "last_reviewer_activity_at": project.last_reviewer_activity_at,
        "created_at": project.created_at,
        "updated_at": project.updated_at,
        **counts,
    }


def list_project_details(
    db: Session, source_mode: str | None = None
) -> list[dict]:
    """List all projects (demo and user-created) as detail dicts.

    source_mode may be "all", None, "demo_fixture", or "user_created".
    """

    stmt = select(models.Project)
    if source_mode and source_mode != "all":
        stmt = stmt.where(models.Project.source_mode == source_mode)
    stmt = stmt.order_by(models.Project.project_id)
    return [project_detail_dict(db, p) for p in db.scalars(stmt).all()]


def get_project_detail(db: Session, project_id: str) -> dict | None:
    project = db.get(models.Project, project_id)
    if project is None:
        return None
    return project_detail_dict(db, project)


def create_project(
    db: Session,
    *,
    project_name: str,
    project_type: str,
    jurisdiction: str,
    review_type: str,
    review_domain: str,
    location_context: str,
    acreage: float | None = None,
    disturbed_area: float | None = None,
    proposed_lots: int | None = None,
    summary: str | None = None,
    applicant_name: str | None = None,
    applicant_organization: str | None = None,
    design_engineer_name: str | None = None,
    design_firm: str | None = None,
    submission_reference: str | None = None,
    parcel_ids: list[str] | None = None,
    created_by_name: str = DEMO_ACTOR_NAME,
    created_by_user_id: str | None = None,
    created_by_email: str | None = None,
    organization_id: str | None = None,
    access_level: str | None = None,
) -> dict:
    """Create a real, user-created project record and a project_created event.

    When a signed-in user creates the project (Sprint 5), the project records the
    user and organization, the creating user is granted project_admin access, and
    the audit event carries the user identity. The project is controlled
    visibility (not a public demo).
    """

    if not project_name.strip():
        raise IntakeError("project_name is required.", status_code=422)
    for field, value in (
        ("project_name", project_name),
        ("project_type", project_type),
        ("review_type", review_type),
        ("summary", summary),
    ):
        reject_prohibited_language(value, field=field)

    ensure_demo_actor(db)
    now = _now()
    project_id = f"proj_user_{_short()}"
    project = models.Project(
        project_id=project_id,
        project_name=project_name.strip(),
        project_type=project_type.strip() or "Not specified",
        location_context=(location_context or "").strip(),
        jurisdiction=(jurisdiction or "").strip(),
        review_type=(review_type or "").strip() or "Not specified",
        review_domain=(review_domain or "stormwater").strip() or "stormwater",
        acreage=float(acreage) if acreage is not None else 0.0,
        disturbed_area=float(disturbed_area)
        if disturbed_area is not None
        else 0.0,
        proposed_lots=int(proposed_lots) if proposed_lots is not None else 0,
        status="intake_started",
        summary=(summary or "").strip(),
        site_conditions=[],
        proposed_improvements=[],
        known_constraints=[],
        source_mode="user_created",
        created_by_name=created_by_name,
        created_by_actor_id=DEMO_ACTOR_ID,
        applicant_name=applicant_name,
        applicant_organization=applicant_organization,
        design_engineer_name=design_engineer_name,
        design_firm=design_firm,
        submission_reference=submission_reference,
        review_round_current=1,
        parcel_ids=list(parcel_ids or []),
        organization_id=organization_id,
        created_by_user_id=created_by_user_id,
        visibility_mode="controlled",
        demo_public=False,
        created_at=now,
        updated_at=now,
    )
    db.add(project)
    # Grant the creating user project_admin access so they can read and manage
    # the project they created.
    if created_by_user_id is not None:
        db.add(
            models.ProjectAccess(
                project_access_id=f"pacc_{_short()}",
                project_id=project_id,
                user_id=created_by_user_id,
                organization_id=organization_id,
                access_level="project_admin",
                granted_by_user_id=created_by_user_id,
                is_active=True,
                created_at=now,
                updated_at=now,
            )
        )
    record_audit_event(
        db,
        project_id=project_id,
        event_type="project_created",
        related_entity_type="project",
        related_entity_id=project_id,
        description=(
            f"Reviewer created project record '{project.project_name}'."
        ),
        actor_type="reviewer",
        actor_id=created_by_user_id or DEMO_ACTOR_ID,
        actor_display_name=created_by_name,
        metadata={
            "source_mode": "user_created",
            "jurisdiction": project.jurisdiction,
            "review_type": project.review_type,
        },
        user_id=created_by_user_id,
        user_email=created_by_email,
        organization_id=organization_id,
        access_level=access_level,
    )
    db.commit()
    db.refresh(project)
    return project_detail_dict(db, project)


# ---------------------------------------------------------------------------
# Documents
# ---------------------------------------------------------------------------


def _require_project(db: Session, project_id: str) -> models.Project:
    project = db.get(models.Project, project_id)
    if project is None:
        raise IntakeError("Project not found.", status_code=404)
    return project


def register_document(
    db: Session,
    *,
    project_id: str,
    original_file_name: str,
    document_type: str,
    purpose: str | None = None,
    expected_key_information: str | None = None,
    content_type: str | None = None,
    file_size_bytes: int | None = None,
    revision_label: str | None = None,
    revision_date: str | None = None,
    uploaded_by_name: str = DEMO_ACTOR_NAME,
) -> models.Document:
    """Register document metadata for a project and emit a document_registered
    event. Registration records intake metadata; it never implies approval."""

    _require_project(db, project_id)
    if not (original_file_name or "").strip():
        raise IntakeError("original_file_name is required.", status_code=422)
    reject_prohibited_language(document_type, field="document_type")
    reject_prohibited_language(purpose, field="purpose")

    ensure_demo_actor(db)
    now = _now()
    safe_name = Path(original_file_name).name
    document_id = f"doc_user_{_short()}"
    document = models.Document(
        document_id=document_id,
        project_id=project_id,
        file_name=safe_name,
        original_file_name=safe_name,
        document_type=(document_type or "other").strip() or "other",
        status="registered",
        purpose=(purpose or "").strip(),
        expected_key_information=(expected_key_information or "").strip(),
        intentionally_missing_or_conflicting_information=None,
        source_mode="user_registered",
        upload_status="not_uploaded",
        processing_status="metadata_recorded",
        content_type=content_type,
        file_size_bytes=file_size_bytes,
        revision_label=revision_label,
        revision_date=revision_date,
        uploaded_by_name=uploaded_by_name,
        registered_at=now,
        is_superseded=False,
    )
    db.add(document)
    record_audit_event(
        db,
        project_id=project_id,
        event_type="document_registered",
        related_entity_type="document",
        related_entity_id=document_id,
        description=(
            f"Reviewer registered document '{safe_name}' "
            f"({document.document_type})."
        ),
        actor_type="reviewer",
        actor_display_name=uploaded_by_name,
        metadata={
            "source_mode": "user_registered",
            "processing_status": "metadata_recorded",
            "revision_label": revision_label,
        },
    )
    db.commit()
    db.refresh(document)
    return document


def upload_document(
    db: Session,
    *,
    project_id: str,
    original_file_name: str | None,
    content_type: str | None,
    content_bytes: bytes,
    document_type: str = "other",
    purpose: str | None = None,
    revision_label: str | None = None,
    uploaded_by_name: str = DEMO_ACTOR_NAME,
    actor: ActorContext | None = None,
) -> models.Document:
    """Validate, store, and register a real uploaded document file.

    Storage uses a safe generated file name (never the raw user file name).
    A sha256 checksum is computed and stored. The raw bytes are not parsed in
    this sprint. Rejected uploads raise IntakeError and write a
    document_upload_rejected audit event without storing the file.
    """

    _require_project(db, project_id)
    ensure_demo_actor(db)
    if actor is not None:
        uploaded_by_name = actor.display_name
    reject_prohibited_language(document_type, field="document_type")

    size_bytes = len(content_bytes)
    safe_name = Path(original_file_name or "uploaded").name
    error = validate_project_upload(
        file_name=original_file_name, size_bytes=size_bytes
    )
    if error is not None:
        record_audit_event(
            db,
            project_id=project_id,
            event_type="document_upload_rejected",
            related_entity_type="document",
            related_entity_id=project_id,
            description=f"Document upload rejected: {error}",
            actor_type="reviewer",
            actor_display_name=uploaded_by_name,
            metadata={
                "original_file_name": safe_name,
                "size_bytes": size_bytes,
            },
        )
        db.commit()
        raise IntakeError(error, status_code=422)

    checksum = hashlib.sha256(content_bytes).hexdigest()
    now = _now()
    document_id = f"doc_user_{_short()}"

    record_audit_event(
        db,
        **audit_kwargs(actor),
        project_id=project_id,
        event_type="document_upload_started",
        related_entity_type="document",
        related_entity_id=document_id,
        description=f"Reviewer started upload of '{safe_name}'.",
        actor_type="reviewer",
        actor_display_name=uploaded_by_name,
        metadata={"size_bytes": size_bytes},
    )

    # Store the file through the configured storage provider (local or S3). Only
    # a safe, generated storage key is recorded; the raw filesystem path and any
    # object storage credentials are never stored on the document or in audit
    # metadata.
    try:
        stored = storage_service.save_document_file(
            project_id=project_id,
            document_id=document_id,
            original_filename=safe_name,
            content_bytes=content_bytes,
            content_type=content_type,
        )
    except StorageError as exc:
        record_audit_event(
            db,
            **audit_kwargs(actor),
            project_id=project_id,
            event_type="document_storage_failed",
            related_entity_type="document",
            related_entity_id=document_id,
            description="Document storage failed.",
            actor_type="reviewer",
            actor_display_name=uploaded_by_name,
            metadata={"size_bytes": size_bytes, "status": "storage_failed"},
        )
        db.commit()
        raise IntakeError(
            "The uploaded file could not be stored. A reviewer should retry.",
            status_code=502,
        ) from exc

    document = models.Document(
        document_id=document_id,
        project_id=project_id,
        file_name=f"doc_{_short()}{Path(safe_name).suffix.lower()}",
        original_file_name=safe_name,
        document_type=(document_type or "other").strip() or "other",
        status="uploaded",
        purpose=(purpose or "").strip(),
        expected_key_information="",
        intentionally_missing_or_conflicting_information=None,
        source_mode="user_uploaded",
        upload_status="stored",
        processing_status="parsing_not_available",
        storage_provider=stored.provider,
        storage_key=stored.storage_key,
        storage_bucket=stored.bucket,
        storage_etag=stored.etag,
        storage_version_id=stored.version_id,
        file_available=True,
        last_storage_check_at=now,
        content_type=content_type,
        file_size_bytes=size_bytes,
        checksum_sha256=checksum,
        revision_label=revision_label,
        uploaded_by_name=uploaded_by_name,
        uploaded_at=now,
        registered_at=now,
        is_superseded=False,
    )
    db.add(document)
    record_audit_event(
        db,
        **audit_kwargs(actor),
        project_id=project_id,
        event_type="document_stored",
        related_entity_type="document",
        related_entity_id=document_id,
        description=(
            f"Reviewer uploaded document '{safe_name}' "
            f"({size_bytes} bytes), stored via {stored.provider}."
        ),
        actor_type="reviewer",
        actor_display_name=uploaded_by_name,
        metadata={
            "source_mode": "user_uploaded",
            "storage_provider": stored.provider,
            "checksum_sha256": checksum,
            "file_size_bytes": size_bytes,
            "content_type": content_type,
            "processing_status": "parsing_not_available",
            "status": "stored",
        },
    )
    db.commit()
    db.refresh(document)
    return document


def validate_project_upload(
    *, file_name: str | None, size_bytes: int
) -> str | None:
    """Return an error message if the upload is not allowed, else None.

    Checks extension against the configured allow-list and size against the
    configured maximum. These are review-support intake checks, never an
    engineering determination.
    """

    settings = get_settings()
    extension = Path(file_name or "").suffix.lower()
    allowed = settings.allowed_project_upload_extensions_set
    if extension not in allowed:
        return (
            f"Unsupported file extension '{extension or '(none)'}'. Allowed "
            f"types: {', '.join(sorted(allowed))}."
        )
    if size_bytes <= 0:
        return "The uploaded file is empty (zero bytes)."
    max_bytes = settings.MAX_PROJECT_UPLOAD_BYTES
    if size_bytes > max_bytes:
        return (
            f"The uploaded file is {size_bytes} bytes, which exceeds the "
            f"{max_bytes} byte limit."
        )
    return None


def save_uploaded_project_file(
    *, content_bytes: bytes, project_id: str, original_file_name: str
) -> tuple[str, str]:
    """Write uploaded bytes to disk under a safe generated file name.

    The stored file name is generated and preserves only the validated
    extension. It is never derived from the user file name, which prevents
    path traversal. Returns (stored_file_name, storage_path).
    """

    settings = get_settings()
    upload_root = Path(settings.PROJECT_UPLOAD_DIR).resolve()
    project_dir = upload_root / project_id
    project_dir.mkdir(parents=True, exist_ok=True)
    extension = Path(original_file_name).suffix.lower()
    stored_file_name = f"doc_{_short()}{extension}"
    storage_path = project_dir / stored_file_name
    storage_path.write_bytes(content_bytes)
    return stored_file_name, str(storage_path)


# ---------------------------------------------------------------------------
# Findings
# ---------------------------------------------------------------------------


def create_finding(
    db: Session,
    *,
    project_id: str,
    title: str,
    category: str,
    risk_level: str,
    evidence_status: str,
    evidence_to_find: str,
    reason_it_matters: str,
    recommended_human_action: str,
    related_documents: list[str] | None = None,
    related_checklist_items: list[str] | None = None,
    reviewer_notes: str | None = None,
    human_review_status: str = "needs_reviewer_confirmation",
    created_by_name: str = DEMO_ACTOR_NAME,
    actor: ActorContext | None = None,
) -> models.Finding:
    """Create a reviewer-owned review-support finding and a finding_created
    event. The finding stays under human review and carries no final decision."""

    _require_project(db, project_id)
    if actor is not None:
        created_by_name = actor.display_name
    if not (title or "").strip():
        raise IntakeError("title is required.", status_code=422)
    for field, value in (
        ("title", title),
        ("category", category),
        ("evidence_to_find", evidence_to_find),
        ("reason_it_matters", reason_it_matters),
        ("recommended_human_action", recommended_human_action),
        ("reviewer_notes", reviewer_notes),
    ):
        reject_prohibited_language(value, field=field)

    if evidence_status not in ALLOWED_EVIDENCE_STATUSES:
        raise IntakeError(
            f"Invalid evidence_status '{evidence_status}'. Allowed: "
            f"{', '.join(sorted(ALLOWED_EVIDENCE_STATUSES))}.",
            status_code=422,
        )
    if human_review_status not in ALLOWED_REVIEWER_FINDING_STATUSES:
        raise IntakeError(
            f"Invalid human_review_status '{human_review_status}'. Allowed: "
            f"{', '.join(sorted(ALLOWED_REVIEWER_FINDING_STATUSES))}.",
            status_code=422,
        )

    ensure_demo_actor(db)
    now = _now()
    finding_id = f"find_user_{_short()}"
    finding = models.Finding(
        finding_id=finding_id,
        project_id=project_id,
        planted_issue="",
        title=title.strip(),
        category=(category or "general").strip() or "general",
        risk_level=(risk_level or "medium").strip() or "medium",
        expected_status=evidence_status,
        evidence_status=evidence_status,
        evidence_to_find=(evidence_to_find or "").strip(),
        reason_it_matters=(reason_it_matters or "").strip(),
        recommended_human_action=(recommended_human_action or "").strip(),
        human_review_status=human_review_status,
        related_checklist_items=list(related_checklist_items or []),
        related_documents=list(related_documents or []),
        source_mode="user_created",
        finding_origin="reviewer_created",
        reviewer_notes=reviewer_notes,
        created_by_name=created_by_name,
        created_by_actor_id=DEMO_ACTOR_ID,
        created_at=now,
        updated_at=now,
    )
    db.add(finding)
    record_audit_event(
        db,
        **audit_kwargs(actor),
        project_id=project_id,
        event_type="finding_created",
        related_entity_type="finding",
        related_entity_id=finding_id,
        description=(
            f"Reviewer created review-support finding '{finding.title}'."
        ),
        actor_type="reviewer",
        actor_display_name=created_by_name,
        metadata={
            "finding_origin": "reviewer_created",
            "evidence_status": evidence_status,
            "human_review_status": human_review_status,
            "risk_level": finding.risk_level,
        },
    )
    db.commit()
    db.refresh(finding)
    return finding


# ---------------------------------------------------------------------------
# Evidence references
# ---------------------------------------------------------------------------


def create_evidence_reference(
    db: Session,
    *,
    finding_id: str,
    document_id: str,
    reviewer_note: str,
    page_number: int | None = None,
    sheet_number: str | None = None,
    section_label: str | None = None,
    created_by_name: str = DEMO_ACTOR_NAME,
) -> models.FindingSource:
    """Create a basic manual evidence reference linking a finding to a document.

    This is a review-support evidence reference placeholder, not a final
    citation engine. It records where a reviewer can inspect relevant evidence.
    """

    finding = db.get(models.Finding, finding_id)
    if finding is None:
        raise IntakeError("Finding not found.", status_code=404)
    document = db.get(models.Document, document_id)
    if document is None:
        raise IntakeError("Document not found.", status_code=404)
    if document.project_id != finding.project_id:
        raise IntakeError(
            "Document and finding belong to different projects.",
            status_code=422,
        )
    reject_prohibited_language(reviewer_note, field="reviewer_note")

    ensure_demo_actor(db)
    reference_id = f"evref_{_short()}"
    reference = models.FindingSource(
        finding_source_id=reference_id,
        finding_id=finding_id,
        document_id=document_id,
        chunk_id=None,
        page_number=page_number,
        excerpt=(reviewer_note or "").strip(),
        evidence_role="requires_reviewer_confirmation",
        confidence=0.0,
        sheet_number=sheet_number,
        section_label=section_label,
        source_mode="user_created",
        created_at=_now(),
    )
    db.add(reference)
    record_audit_event(
        db,
        project_id=finding.project_id,
        event_type="evidence_reference_created",
        related_entity_type="finding",
        related_entity_id=finding_id,
        description=(
            f"Reviewer linked document '{document.file_name}' as evidence for "
            f"finding '{finding.title}'."
        ),
        actor_type="reviewer",
        actor_display_name=created_by_name,
        metadata={
            "finding_source_id": reference_id,
            "document_id": document_id,
            "page_number": page_number,
            "sheet_number": sheet_number,
            "section_label": section_label,
        },
    )
    db.commit()
    db.refresh(reference)
    return reference


def list_evidence_references(
    db: Session, finding_id: str
) -> list[models.FindingSource]:
    stmt = (
        select(models.FindingSource)
        .where(models.FindingSource.finding_id == finding_id)
        .order_by(models.FindingSource.id)
    )
    return list(db.scalars(stmt).all())


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
