"""Project intake reads and creation.

A reviewer can list projects (demo and user-created), read a single project
detail, and create a real user-created project record. Nothing here approves
plans or makes a final engineering decision; every record stays review-support
only and under human review.
"""

from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.safety import reject_prohibited_language
from app.db import models
from app.services.real_intake_service._common import (
    DEMO_ACTOR_ID,
    DEMO_ACTOR_NAME,
    _now,
    _short,
    ensure_demo_actor,
    record_audit_event,
)
from app.services.real_intake_service.errors import IntakeError


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

    # Attach the project to the creating user's organization when they belong to
    # one, so the project and its usage are organization-scoped. Users with no
    # organization keep organization_id=None and are not usage-enforced.
    if organization_id is None and created_by_user_id:
        from app.services import access_control_service

        organization_id = access_control_service.primary_organization_id(
            db, created_by_user_id
        )

    # Enforce the per-organization project limit before any mutation, when
    # enforcement is enabled. A no-op for the demo org and in advisory mode.
    from app.services import usage_service

    usage_service.check_limit(
        db, category="project_created", organization_id=organization_id
    )

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
    # Record advisory usage for the created project (best-effort, skips the demo
    # organization, never blocks creation).
    from app.services import usage_service

    usage_service.record_usage_safe(
        db,
        category="project_created",
        organization_id=organization_id,
        project_id=project_id,
    )
    db.commit()
    db.refresh(project)
    return project_detail_dict(db, project)
