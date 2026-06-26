# API: Authentication and Access Control

Production Foundations Sprint 5 routes for local authentication, organizations,
the current user, and project access. All routes are under the `/api/v1` prefix.

These endpoints are a local authentication foundation, not enterprise SSO.
Access control protects review records and improves audit attribution. It never
approves plans, certifies compliance, verifies CAD, validates design, or makes
any final engineering decision. Password hashes and tokens are never returned
outside the documented token response, and never appear in logs or audit
metadata.

## Auth routes

### POST /api/v1/auth/register

Create a local account and receive an access token. Optionally create a first
organization (the new user becomes its org_admin).

Request:

```json
{
  "email": "reviewer@town.example",
  "display_name": "Jordan Reviewer",
  "password": "a-strong-password",
  "organization_name": "Town of Riverton",
  "organization_type": "municipality"
}
```

Response (201):

```json
{
  "access_token": "<signed token>",
  "token_type": "bearer",
  "expires_in_minutes": 120,
  "user": {
    "user_id": "user_abc123",
    "email": "reviewer@town.example",
    "display_name": "Jordan Reviewer",
    "is_active": true,
    "is_demo_user": false
  }
}
```

Validation: a valid email is required, the password must meet the minimum length
(default 8), and a duplicate email returns 409. The password hash is never
returned.

### POST /api/v1/auth/login

Authenticate and receive an access token. Same response shape as register.
Incorrect credentials return 401.

### GET /api/v1/auth/me

Return the current user. Requires a Bearer token; returns 401 otherwise. Never
includes the password hash.

### POST /api/v1/auth/logout

Tokens are stateless; logout is performed client-side by discarding the token.
This endpoint documents that contract.

## Current-user routes

### GET /api/v1/me/organizations

List the organizations the current user belongs to, with the user's role.

### GET /api/v1/me/projects

List projects the current user can access (public demo projects plus granted
projects), each with the user's effective access level.

## Organization routes

### GET /api/v1/organizations

List the current user's organizations.

### GET /api/v1/organizations/{organization_id}

Get an organization the current user belongs to. Returns 403 for non-members.

### GET /api/v1/organizations/{organization_id}/members

List an organization's members. Returns 403 for non-members.

## Project access routes

### GET /api/v1/projects/{project_id}/access

List a project's access entries. Requires read access to the project.

### POST /api/v1/projects/{project_id}/access/grant

Grant a user or organization access to a project. Requires project_admin or
org_admin. Writes a `project_access_granted` audit event.

Request:

```json
{ "access_level": "reviewer", "user_id": "user_target123" }
```

Response (201):

```json
{
  "project_access_id": "pacc_xyz",
  "project_id": "proj_user_abc",
  "user_id": "user_target123",
  "access_level": "reviewer",
  "is_active": true
}
```

## Authorization header

Protected requests send `Authorization: Bearer <token>`. Unauthenticated
requests to protected real-project routes return 401; authenticated requests
without permission return 403. The public Brookside Meadows demo is readable
without a token when `AUTH_ALLOW_PUBLIC_DEMO` is true.

## Role and permission rules

- read_only: view project records, documents, checklist, citations, findings,
  and audit summaries.
- reviewer / senior_reviewer: reviewer actions (documents, findings, citations,
  retrieval candidates, checklist statuses, draft findings).
- org_admin / project_admin: manage project access and organization membership.
- applicant_placeholder: limited; no reviewer actions yet.
- demo_reviewer: behaves as a reviewer for the local demo.

## Environment variables

- `AUTH_SECRET_KEY`: signs access tokens. Override with a strong secret in
  deployment.
- `AUTH_TOKEN_EXPIRE_MINUTES` (default 120): token lifetime.
- `AUTH_DEMO_MODE` (default true): keeps the demo reviewer fallback available.
- `AUTH_REQUIRE_LOGIN_FOR_REAL_PROJECTS` (default true): requires a signed-in
  user for real (non-demo) project actions.
- `AUTH_ALLOW_PUBLIC_DEMO` (default true): allows reading demo_public projects
  without a login.

## Professional-boundary notes

There is no `approved`, `certified`, `verified`, `passed`, `failed`, `resolved`,
or `closed` status anywhere in this API. Roles and access control govern who can
review records, not whether a project satisfies engineering requirements. Audit
metadata never includes passwords, password hashes, tokens, secrets, API keys,
raw server file paths, or full extracted page text. A licensed Professional
Engineer remains responsible for engineering decisions.
