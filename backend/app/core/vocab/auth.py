"""Authentication, organization, and per-project access control vocabulary."""

from __future__ import annotations

# Production Foundations Sprint 5 authentication and access control vocabulary.
# Roles and access levels control who may view or act on review records and
# improve audit attribution. They never introduce final engineering decision
# workflows and never imply approval, certification, or compliance.

# Organization account types. internal_demo and demo_organization mark seeded
# demo organizations; the others describe real organization accounts.
ALLOWED_ORGANIZATION_TYPES: set[str] = {
    "municipality",
    "consulting_engineer",
    "developer_applicant",
    "county_agency",
    "demo_organization",
    "internal_demo",
}

# Organization membership roles. demo_reviewer behaves as a reviewer for the
# local demo; applicant_placeholder is intentionally limited and holds no
# reviewer actions yet.
ALLOWED_MEMBERSHIP_ROLES: set[str] = {
    "org_admin",
    "senior_reviewer",
    "reviewer",
    "read_only",
    "applicant_placeholder",
    "demo_reviewer",
}

# Per-project access levels. project_admin can manage project access; reviewer
# and senior_reviewer can take reviewer actions; read_only can view only;
# applicant_placeholder is limited and holds no reviewer actions yet.
ALLOWED_PROJECT_ACCESS_LEVELS: set[str] = {
    "project_admin",
    "reviewer",
    "senior_reviewer",
    "read_only",
    "applicant_placeholder",
}

# Roles and access levels that may take reviewer (write) actions on a project.
REVIEWER_ACCESS_LEVELS: set[str] = {
    "project_admin",
    "senior_reviewer",
    "reviewer",
}
REVIEWER_MEMBERSHIP_ROLES: set[str] = {
    "org_admin",
    "senior_reviewer",
    "reviewer",
    "demo_reviewer",
}

# Project visibility modes. demo_public projects may be read without a login when
# AUTH_ALLOW_PUBLIC_DEMO is true; controlled projects require explicit access.
ALLOWED_PROJECT_VISIBILITY_MODES: set[str] = {
    "controlled",
    "organization_visible",
    "demo_public",
}
