"""Reviewer dashboard and workload composition (Sprint 9).

Builds the reviewer dashboard, reviewer queue, organization dashboard, and
per-project workload summaries from access-controlled review records. Every view
is filtered to projects the signed-in user may read. The dashboard organizes
review-support work and operational indicators. It never approves plans,
certifies compliance, verifies CAD, validates design, declares a project safe,
resolves or closes an issue, or makes any final engineering decision.

Aggregation reuses operational_metrics_service for per-project counts and safe
aging indicators. Assignment and priority updates are reviewer-controlled
workflow metadata changes; they are audit-attributed and never change a project's
engineering status.
"""

from __future__ import annotations

from datetime import datetime, timezone

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.core.safety import (
    ALLOWED_REVIEW_PRIORITIES,
    reject_prohibited_language,
)
from app.db import models
from app.services import access_control_service, operational_metrics_service
from app.services.auth_service import ActorContext, audit_kwargs
from app.services.operational_metrics_service import (
    aging_bucket,
    build_project_queue_items,
    compute_project_metrics,
    due_date_indicators,
    project_reference_timestamp,
)
from app.services.real_intake_service import record_audit_event

# Metric keys aggregated into dashboard-level totals. Kept in one place so the
# reviewer dashboard and organization dashboard report the same safe counts.
AGGREGATE_METRIC_KEYS: list[str] = [
    "documents_uploaded",
    "documents_needing_indexing",
    "documents_indexed_with_text",
    "documents_extraction_unavailable",
    "findings_needing_reviewer_confirmation",
    "evidence_candidates_needing_triage",
    "checklist_items_missing_evidence",
    "checklist_items_unclear_evidence",
    "applicant_responses_needing_review",
    "resubmittal_rounds_registered",
    "matrix_items_carried_forward",
    "response_packages_draft",
    "response_packages_ready_for_handoff",
    "packages_issued_by_reviewer",
    "pending_reviewer_action_count",
]


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _empty_aggregate() -> dict:
    return {key: 0 for key in AGGREGATE_METRIC_KEYS}


def _project_summary(
    db: Session, project: models.Project, *, now: datetime
) -> dict:
    """Build a dashboard project summary card with safe counts and aging."""

    metrics = compute_project_metrics(db, project, now=now)
    reference = project_reference_timestamp(project)
    return {
        "project_id": project.project_id,
        "project_name": project.project_name,
        "status": project.status,
        "source_mode": project.source_mode,
        "organization_id": project.organization_id,
        "assigned_reviewer_user_id": project.assigned_reviewer_user_id,
        "assigned_reviewer_name": project.assigned_reviewer_name,
        "review_priority": project.review_priority,
        "review_due_date": project.review_due_date,
        "last_reviewer_activity_at": project.last_reviewer_activity_at,
        "age_bucket": aging_bucket(reference, now=now),
        "due_date_indicators": due_date_indicators(
            project.review_due_date, now=now
        ),
        "pending_reviewer_action_count": metrics[
            "pending_reviewer_action_count"
        ],
        "has_pending_reviewer_action": metrics["has_pending_reviewer_action"],
        "metrics": metrics,
    }


def _accumulate(aggregate: dict, metrics: dict) -> None:
    for key in AGGREGATE_METRIC_KEYS:
        aggregate[key] += int(metrics.get(key, 0) or 0)


# ---------------------------------------------------------------------------
# Reviewer dashboard
# ---------------------------------------------------------------------------


def get_reviewer_dashboard(
    db: Session, user: models.UserAccount, filters: dict | None = None
) -> dict:
    """Build the reviewer dashboard for the signed-in user.

    Only projects the user can read are included. The response carries safe
    aggregate counts, per-project summaries, and a bounded reviewer queue.
    """

    now = _now()
    projects = access_control_service.list_user_accessible_projects(db, user)
    summaries: list[dict] = []
    aggregate = _empty_aggregate()
    queue: list[dict] = []
    projects_with_pending = 0
    for project in projects:
        summary = _project_summary(db, project, now=now)
        summaries.append(summary)
        _accumulate(aggregate, summary["metrics"])
        if summary["has_pending_reviewer_action"]:
            projects_with_pending += 1
        queue.extend(
            build_project_queue_items(project, summary["metrics"], now=now)
        )

    summaries.sort(
        key=lambda s: (-s["pending_reviewer_action_count"], s["project_name"])
    )
    queue.sort(key=lambda q: (-q["count"], q["project_name"]))

    return {
        "scope": "reviewer",
        "generated_at": now,
        "user_id": user.user_id,
        "display_name": user.display_name,
        "accessible_project_count": len(projects),
        "projects_with_pending_action_count": projects_with_pending,
        "totals": aggregate,
        "projects": summaries,
        "queue": queue,
        "access_note": (
            "Dashboard data is limited to projects you can access. Counts are "
            "operational review-support indicators only. They do not approve "
            "plans, certify compliance, or resolve issues."
        ),
    }


def get_reviewer_queue(
    db: Session, user: models.UserAccount, filters: dict | None = None
) -> dict:
    """Build the reviewer queue across the user's accessible projects."""

    now = _now()
    filters = filters or {}
    item_type_filter = filters.get("item_type")
    projects = access_control_service.list_user_accessible_projects(db, user)
    queue: list[dict] = []
    for project in projects:
        metrics = compute_project_metrics(db, project, now=now)
        queue.extend(build_project_queue_items(project, metrics, now=now))
    if item_type_filter:
        queue = [q for q in queue if q["item_type"] == item_type_filter]
    queue.sort(key=lambda q: (-q["count"], q["project_name"]))
    return {
        "scope": "reviewer",
        "generated_at": now,
        "item_count": len(queue),
        "items": queue,
    }


def get_reviewer_dashboard_projects(
    db: Session, user: models.UserAccount, filters: dict | None = None
) -> list[dict]:
    """List accessible project summaries for the reviewer dashboard."""

    now = _now()
    projects = access_control_service.list_user_accessible_projects(db, user)
    summaries = [_project_summary(db, p, now=now) for p in projects]
    summaries.sort(
        key=lambda s: (-s["pending_reviewer_action_count"], s["project_name"])
    )
    return summaries


# ---------------------------------------------------------------------------
# Organization dashboard
# ---------------------------------------------------------------------------


def _accessible_org_projects(
    db: Session,
    organization_id: str,
    user: models.UserAccount,
) -> list[models.Project]:
    """Return organization projects the user may read.

    A project belongs to the organization when project.organization_id matches.
    Each is intersected with the user's accessible projects so a member never
    sees a project they cannot read.
    """

    accessible_ids = {
        p.project_id
        for p in access_control_service.list_user_accessible_projects(db, user)
    }
    org_projects: list[models.Project] = []
    for project in db.query(models.Project).all():
        if project.organization_id != organization_id:
            continue
        if project.project_id in accessible_ids:
            org_projects.append(project)
    return org_projects


def _require_org_membership(
    db: Session, organization_id: str, user: models.UserAccount
) -> str:
    """Require the user is a member of the organization. Returns their role."""

    access_control_service.get_organization(db, organization_id)
    for membership in access_control_service.list_user_memberships(
        db, user.user_id
    ):
        if membership.organization_id == organization_id:
            return membership.role
    raise HTTPException(
        status_code=403,
        detail="You are not a member of this organization.",
    )


def get_organization_dashboard(
    db: Session,
    organization_id: str,
    user: models.UserAccount,
    filters: dict | None = None,
) -> dict:
    """Build the organization workload dashboard for an org member.

    Requires organization membership. Includes only projects the member can read.
    Project counts by review-support status and aggregate counts are returned.
    """

    now = _now()
    role = _require_org_membership(db, organization_id, user)
    org = access_control_service.get_organization(db, organization_id)
    projects = _accessible_org_projects(db, organization_id, user)

    summaries: list[dict] = []
    aggregate = _empty_aggregate()
    status_counts: dict[str, int] = {}
    priority_counts: dict[str, int] = {}
    projects_with_pending = 0
    for project in projects:
        summary = _project_summary(db, project, now=now)
        summaries.append(summary)
        _accumulate(aggregate, summary["metrics"])
        status_counts[project.status] = status_counts.get(project.status, 0) + 1
        priority = project.review_priority or "unassigned"
        priority_counts[priority] = priority_counts.get(priority, 0) + 1
        if summary["has_pending_reviewer_action"]:
            projects_with_pending += 1

    summaries.sort(
        key=lambda s: (-s["pending_reviewer_action_count"], s["project_name"])
    )

    return {
        "scope": "organization",
        "generated_at": now,
        "organization_id": organization_id,
        "organization_name": org.organization_name,
        "viewer_role": role,
        "project_count": len(projects),
        "projects_with_pending_action_count": projects_with_pending,
        "status_counts": status_counts,
        "priority_counts": priority_counts,
        "totals": aggregate,
        "projects": summaries,
        "access_note": (
            "Organization workload is limited to projects you can access. "
            "Counts are operational review-support indicators only."
        ),
    }


def get_organization_workload(
    db: Session,
    organization_id: str,
    user: models.UserAccount,
    filters: dict | None = None,
) -> dict:
    """Return the organization workload aggregate summary for an org member."""

    dashboard = get_organization_dashboard(db, organization_id, user, filters)
    return {
        "scope": "organization",
        "generated_at": dashboard["generated_at"],
        "organization_id": organization_id,
        "organization_name": dashboard["organization_name"],
        "project_count": dashboard["project_count"],
        "projects_with_pending_action_count": dashboard[
            "projects_with_pending_action_count"
        ],
        "status_counts": dashboard["status_counts"],
        "priority_counts": dashboard["priority_counts"],
        "totals": dashboard["totals"],
        "access_note": dashboard["access_note"],
    }


# Roles allowed to view organization reviewer workload summaries.
WORKLOAD_ADMIN_ROLES: set[str] = {"org_admin", "senior_reviewer"}


def get_organization_reviewer_workload(
    db: Session,
    organization_id: str,
    user: models.UserAccount,
    filters: dict | None = None,
) -> dict:
    """Build per-reviewer workload summaries for an organization.

    Requires org_admin or senior_reviewer membership. Read-only and reviewer
    members receive 403. Workload is grouped by assigned reviewer across the
    organization's accessible projects.
    """

    now = _now()
    role = _require_org_membership(db, organization_id, user)
    if role not in WORKLOAD_ADMIN_ROLES:
        raise HTTPException(
            status_code=403,
            detail=(
                "Organization reviewer workload requires org_admin or "
                "senior_reviewer access."
            ),
        )
    org = access_control_service.get_organization(db, organization_id)
    projects = _accessible_org_projects(db, organization_id, user)

    groups: dict[str, dict] = {}
    for project in projects:
        metrics = compute_project_metrics(db, project, now=now)
        key = project.assigned_reviewer_user_id or "unassigned"
        name = project.assigned_reviewer_name or "Unassigned"
        group = groups.setdefault(
            key,
            {
                "assigned_reviewer_user_id": (
                    None if key == "unassigned" else key
                ),
                "assigned_reviewer_name": name,
                "project_count": 0,
                "pending_reviewer_action_count": 0,
                "projects_with_pending_action_count": 0,
            },
        )
        group["project_count"] += 1
        group["pending_reviewer_action_count"] += metrics[
            "pending_reviewer_action_count"
        ]
        if metrics["has_pending_reviewer_action"]:
            group["projects_with_pending_action_count"] += 1

    reviewers = sorted(
        groups.values(),
        key=lambda g: (-g["pending_reviewer_action_count"], g["assigned_reviewer_name"]),
    )
    return {
        "scope": "organization",
        "generated_at": now,
        "organization_id": organization_id,
        "organization_name": org.organization_name,
        "viewer_role": role,
        "reviewers": reviewers,
        "access_note": (
            "Reviewer workload is grouped by assigned reviewer across accessible "
            "projects. Counts are operational indicators only."
        ),
    }


# ---------------------------------------------------------------------------
# Project workload
# ---------------------------------------------------------------------------


def get_project_workload_summary(
    db: Session, project_id: str, actor: ActorContext
) -> dict:
    """Build a single project's workload summary. Caller must enforce read access."""

    now = _now()
    project = db.get(models.Project, project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")
    summary = _project_summary(db, project, now=now)
    summary["scope"] = "project"
    summary["generated_at"] = now
    summary["queue"] = build_project_queue_items(
        project, summary["metrics"], now=now
    )
    summary["access_note"] = (
        "Project workload counts are operational review-support indicators "
        "only. Every pending item requires human review."
    )
    return summary


def get_project_pending_actions(
    db: Session, project_id: str, actor: ActorContext
) -> dict:
    """Return the pending reviewer action queue for one project."""

    now = _now()
    project = db.get(models.Project, project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")
    metrics = compute_project_metrics(db, project, now=now)
    items = build_project_queue_items(project, metrics, now=now)
    return {
        "scope": "project",
        "generated_at": now,
        "project_id": project_id,
        "project_name": project.project_name,
        "pending_reviewer_action_count": metrics[
            "pending_reviewer_action_count"
        ],
        "items": items,
        "access_note": (
            "Pending actions are operational review-support indicators. They do "
            "not represent approval, compliance, or issue resolution."
        ),
    }


# ---------------------------------------------------------------------------
# Assignment and priority updates
# ---------------------------------------------------------------------------


def assign_project_reviewer(
    db: Session,
    project_id: str,
    payload: dict,
    *,
    actor: ActorContext,
) -> dict:
    """Assign a reviewer to a project. Caller must enforce admin access.

    Records a project_assignment_updated audit event. The assignment is workflow
    metadata; it never changes a project's engineering status.
    """

    now = _now()
    project = db.get(models.Project, project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")

    assigned_reviewer_user_id = payload.get("assigned_reviewer_user_id")
    assigned_reviewer_name = payload.get("assigned_reviewer_name")
    note = payload.get("note")
    if assigned_reviewer_name:
        reject_prohibited_language(
            assigned_reviewer_name, field="assigned_reviewer_name"
        )
    if note:
        reject_prohibited_language(note, field="note")

    # Resolve a display name from the user account when only an id is given.
    if assigned_reviewer_user_id and not assigned_reviewer_name:
        target = db.get(models.UserAccount, assigned_reviewer_user_id)
        if target is not None:
            assigned_reviewer_name = target.display_name

    project.assigned_reviewer_user_id = assigned_reviewer_user_id
    project.assigned_reviewer_name = assigned_reviewer_name
    project.last_reviewer_activity_at = now
    project.updated_at = now

    record_audit_event(
        db,
        **audit_kwargs(actor),
        project_id=project_id,
        event_type="project_assignment_updated",
        related_entity_type="project",
        related_entity_id=project_id,
        description=(
            f"{actor.display_name} updated the assigned reviewer to "
            f"{assigned_reviewer_name or 'unassigned'}."
        ),
        actor_type="reviewer",
        actor_id=actor.user_id,
        actor_display_name=actor.display_name,
        metadata={
            "project_id": project_id,
            "assigned_reviewer_user_id": assigned_reviewer_user_id,
        },
    )
    db.commit()
    db.refresh(project)
    return _project_summary(db, project, now=now)


def update_project_priority(
    db: Session,
    project_id: str,
    payload: dict,
    *,
    actor: ActorContext,
) -> dict:
    """Update a project's review priority and optional due date.

    Caller must enforce admin access. Records a project_priority_updated audit
    event. review_priority is a workflow sequencing label, not an engineering
    judgment.
    """

    now = _now()
    project = db.get(models.Project, project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")

    if "review_priority" in payload and payload["review_priority"] is not None:
        priority = payload["review_priority"]
        if priority not in ALLOWED_REVIEW_PRIORITIES:
            raise HTTPException(
                status_code=422,
                detail=f"Invalid review_priority '{priority}'.",
            )
        project.review_priority = priority

    if "review_due_date" in payload:
        project.review_due_date = payload["review_due_date"]

    note = payload.get("note")
    if note:
        reject_prohibited_language(note, field="note")

    project.last_reviewer_activity_at = now
    project.updated_at = now

    record_audit_event(
        db,
        **audit_kwargs(actor),
        project_id=project_id,
        event_type="project_priority_updated",
        related_entity_type="project",
        related_entity_id=project_id,
        description=(
            f"{actor.display_name} updated the review priority to "
            f"{project.review_priority or 'unset'}."
        ),
        actor_type="reviewer",
        actor_id=actor.user_id,
        actor_display_name=actor.display_name,
        metadata={
            "project_id": project_id,
            "review_priority": project.review_priority,
        },
    )
    db.commit()
    db.refresh(project)
    return _project_summary(db, project, now=now)
