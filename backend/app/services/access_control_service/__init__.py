"""Authorization and project access control (Sprint 5).

Builds on the local authentication foundation in auth_service. Resolves the
current user from a bearer token, decides who may read or take reviewer actions
on a project, and records access grants. The seeded Brookside Meadows demo
remains publicly readable when AUTH_ALLOW_PUBLIC_DEMO is true, and demo reviewer
actions keep working when AUTH_DEMO_MODE is true so the public demo and the
existing seeded workflow are preserved.

Access control protects review records and improves audit attribution. It never
controls whether a project satisfies engineering requirements and never implies
approval, certification, or compliance.

This module was split into a package (errors, organizations, projects,
enforcement, reads, _common). The public surface is unchanged: both
`from app.services import access_control_service` and
`from app.services.access_control_service import <name>` keep working.
"""

from __future__ import annotations

from app.core.safety import (
    ALLOWED_MEMBERSHIP_ROLES,
    ALLOWED_ORGANIZATION_TYPES,
    ALLOWED_PROJECT_ACCESS_LEVELS,
    REVIEWER_ACCESS_LEVELS,
)

from app.services.access_control_service.errors import ActorContext, AuthError
from app.services.access_control_service._common import (
    DEMO_ADMIN_EMAIL,
    DEMO_ADMIN_NAME,
    DEMO_ADMIN_USER_ID,
    DEMO_ORG_ID,
    DEMO_ORG_NAME,
    DEMO_REVIEWER_EMAIL,
    DEMO_REVIEWER_NAME,
    DEMO_REVIEWER_USER_ID,
    _ACCESS_PRECEDENCE,
    _demo_reviewer_context,
    _now,
    _require_project,
    _short,
    _user_context,
)
from app.services.access_control_service.organizations import (
    ensure_auth_seed,
    get_organization,
    list_organization_members,
    list_user_memberships,
    list_user_organizations,
    org_admin_org_ids,
    primary_organization_id,
    user_org_ids,
    _ensure_demo_user,
    _ensure_project_access,
)
from app.services.access_control_service.projects import (
    effective_access_level,
    grant_project_access,
    list_project_access,
    list_user_accessible_projects,
)
from app.services.access_control_service.enforcement import (
    context_for_create,
    is_admin_user,
    require_admin_user,
    require_org_admin,
    require_org_member,
    require_project_admin,
    require_project_read,
    require_project_reviewer,
)
from app.services.access_control_service.reads import (
    get_current_user,
    get_optional_user,
    _token_from_header,
)

# Re-export allowed sets for schema validation reuse.
__all__ = [
    "ActorContext",
    "ALLOWED_MEMBERSHIP_ROLES",
    "ALLOWED_ORGANIZATION_TYPES",
    "ALLOWED_PROJECT_ACCESS_LEVELS",
    "ensure_auth_seed",
    "get_optional_user",
    "get_current_user",
    "require_project_read",
    "require_project_reviewer",
    "require_project_admin",
    "require_admin_user",
    "is_admin_user",
    "context_for_create",
]
