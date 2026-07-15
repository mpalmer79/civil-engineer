# Security and Professional Boundary

This document summarizes the security posture and the professional boundary for
the real project intake foundation added in Production Foundations Sprint 1. The
goal of this sprint is the first credible bridge from seeded demo to real
project records, not enterprise readiness.

## Professional boundary

Civil Engineer AI is review-support only. It helps a human reviewer organize
evidence, draft review-support findings, track workflow, and prepare
reviewer-controlled response language.

It does not approve plans, certify compliance, stamp drawings, verify CAD,
validate design, declare a project safe, make final engineering decisions, close
or resolve issues, or replace a licensed Professional Engineer. There is no
action named approve.

Enforcement:

- Project statuses, document processing statuses, finding statuses, and evidence
  statuses are constrained to a review-support vocabulary in
  `app/core/safety.py`.
- User-provided text for projects, documents, and findings is rejected if it
  contains final-decision wording (for example approved, certified, fully
  compliant, safe).
- Document processing statuses never imply approval; they track intake handling.
- Tests assert that intake payloads contain no prohibited final-decision wording
  and that the seeded demo remains intact.

## File upload security

- Only the configured extensions are accepted
  (`ALLOWED_PROJECT_UPLOAD_EXTENSIONS`, default
  `.pdf,.dxf,.csv,.xlsx,.docx,.png,.jpg,.jpeg`).
- Uploads larger than `MAX_PROJECT_UPLOAD_BYTES` (default 25,000,000) are
  rejected.
- Empty files are rejected.
- Files are stored under `PROJECT_UPLOAD_DIR`, one subdirectory per project,
  using a safe generated file name. The raw user file name is never used as a
  storage path, which prevents path traversal. Only the original base name is
  kept as metadata.
- A sha256 checksum is computed and stored for each uploaded file.
- Uploaded files are not parsed in this sprint.
- Upload attempts write an audit event on success and on validation failure,
  without storing secrets.

## Audit and privacy

- Audit events record actor attribution (`actor_type`, `actor_display_name`),
  the related entity, a description, a timestamp, and non-sensitive structured
  `event_metadata`.
- Raw IP addresses and raw user agents are never stored. Only optional hashes
  may be recorded, and only when a caller provides them.
- Audit metadata never stores secrets or API keys.

## Authentication and access control (Sprint 5)

Production Foundations Sprint 5 adds a local authentication and access-control
foundation. See
[AUTHENTICATION_AND_ACCESS_CONTROL.md](AUTHENTICATION_AND_ACCESS_CONTROL.md) and
[API_AUTH_AND_ACCESS_CONTROL.md](API_AUTH_AND_ACCESS_CONTROL.md) for details.

- Passwords are hashed with PBKDF2-HMAC-SHA256 and a per-user salt. Plaintext
  passwords are never stored, never logged, and never placed in audit metadata.
  Password hashes are never returned by the API.
- Access tokens are HMAC-SHA256 signed with `AUTH_SECRET_KEY`, short-lived, never
  logged, never placed in URLs, and never stored in audit metadata.
- Real-project read routes require read access; reviewer-action routes require
  reviewer access; access-management routes require project or organization
  admin. Unauthenticated protected requests return 401; authenticated requests
  without permission return 403.
- When a signed-in user takes an action, the audit event records the user id,
  user email, organization id, and access level for real attribution.
- The seeded demo organization, demo reviewer, and demo admin are local demo
  only; their passwords must be changed or disabled before any real use. The
  public Brookside Meadows demo stays readable without a login when
  `AUTH_ALLOW_PUBLIC_DEMO` is true.
- This is a local auth foundation, not enterprise SSO, and it grants no
  engineering authority. Access control governs who can review records, not
  whether a project satisfies engineering requirements.

## Durable file storage (Sprint 6)

Production Foundations Sprint 6 adds a storage provider abstraction for uploaded
files. See [STORAGE_PROVIDER_ABSTRACTION.md](STORAGE_PROVIDER_ABSTRACTION.md) and
[API_FILE_STORAGE.md](API_FILE_STORAGE.md).

- Uploaded files are stored through a provider (local for development,
  S3-compatible object storage for deployment). Object storage credentials are
  backend-only and are read only when `STORAGE_PROVIDER=s3`. They are never
  exposed to the frontend or returned in any response.
- The database stores only safe metadata (provider, generated storage key,
  checksum, size, availability). API responses never include a raw filesystem
  path, the storage key, the bucket, or any credential.
- Storage keys are generated and never derived from the raw original filename,
  which prevents path traversal. The local provider rejects keys that escape its
  root.
- File download and storage status require project read access; upload and PDF
  indexing require reviewer access; storage health requires an authenticated
  user. The public Brookside Meadows demo remains readable when configured.
- Storage audit metadata records provider, size, checksum, content type, and
  status only. It never includes object storage keys or secrets, signed URLs,
  raw filesystem paths, full file content, extracted page text, tokens, or
  passwords.

## Applicant response matrix and resubmittals (Sprint 7)

Production Foundations Sprint 7 adds a reviewer-controlled applicant response
matrix and a resubmittal collaboration workflow. See
[APPLICANT_RESPONSE_MATRIX.md](APPLICANT_RESPONSE_MATRIX.md),
[RESUBMITTAL_COLLABORATION_WORKFLOW.md](RESUBMITTAL_COLLABORATION_WORKFLOW.md), and
[API_RESPONSE_MATRIX_AND_RESUBMITTALS.md](API_RESPONSE_MATRIX_AND_RESUBMITTALS.md).

- An applicant response is recorded for reviewer review, never as proof and never
  as a final outcome. Carry-forward means continued review, not resolution. The
  workflow never marks an item approved, certified, compliant, verified,
  validated, resolved, or closed.
- Matrix and resubmittal reads require project read access; all mutations require
  project reviewer access. A read-only user receives 403 on mutations. The public
  Brookside Meadows demo remains readable when configured.
- Free-text fields (matrix name, reviewer comment draft, requested evidence,
  reviewer note, applicant response text, round label, summary) are checked
  against the prohibited-language guard. Status values are validated against the
  Sprint 7 review-support status sets.
- Audit metadata for an applicant response records a response length only, never
  the full applicant response text. Document-link responses and audit metadata
  never include a raw filesystem path, a storage key, a signed URL, a token, a
  password, or any credential.

## Reviewer response packages and comment letters (Sprint 8)

Production Foundations Sprint 8 adds reviewer response packages and deterministic
comment letter drafts. See
[RESPONSE_PACKAGE_AND_COMMENT_LETTER_WORKFLOW.md](RESPONSE_PACKAGE_AND_COMMENT_LETTER_WORKFLOW.md),
[API_RESPONSE_PACKAGES.md](API_RESPONSE_PACKAGES.md), and
[COMMENT_LETTER_TEMPLATE_BOUNDARY.md](COMMENT_LETTER_TEMPLATE_BOUNDARY.md).

- A response package is a reviewer communication artifact. Issuing a package
  records that a reviewer issued a communication. It never approves a project,
  certifies compliance, validates design, declares safety, resolves an issue, or
  closes an issue. Issuance never sets an approved, certified, compliant, verified,
  validated, resolved, or closed status.
- Comment letter drafts are generated from fixed deterministic templates. There
  are no live AI calls. A fixed review-support boundary statement is rendered with
  every draft and preview and is never an editable section.
- Package and comment letter reads require project read access; all mutations
  require project reviewer access. A read-only user receives 403 on mutations. The
  public Brookside Meadows demo remains readable when configured, and the Phase 10
  demo response package builder is preserved unchanged.
- Reviewer-entered free-text fields (package title, manual reviewer comment,
  requested evidence, reviewer note, revision reason, recipient fields, and every
  editable comment letter section) are checked against the prohibited-language
  guard. Status values are validated against the Sprint 8 review-support status
  sets. Source records must belong to the same project as the package.
- Package and comment letter responses, previews, and audit metadata never include
  the full comment letter text, full applicant response text, full extracted page
  text, a raw filesystem path, a storage key, a signed URL, a token, a password, or
  any credential. A revision preserves prior issued records rather than
  overwriting them.

## Reviewer dashboard and operational metrics (Sprint 9)

Production Foundations Sprint 9 adds a reviewer dashboard, organization workload
views, per-project workload summaries, a reviewer queue, and a project assignment
and review priority foundation. See
[REVIEWER_DASHBOARD_AND_WORKLOAD.md](REVIEWER_DASHBOARD_AND_WORKLOAD.md),
[API_OPERATIONAL_METRICS.md](API_OPERATIONAL_METRICS.md), and
[METRICS_BOUNDARY_AND_LIMITATIONS.md](METRICS_BOUNDARY_AND_LIMITATIONS.md).

- Dashboard metrics are operational review-support indicators only. No count or
  status represents approval, certification, compliance, verification, or issue
  resolution. There is intentionally no approved, closed, resolved, passed,
  failed, compliant, verified, certified, safe, or unsafe value.
- Every dashboard result is filtered by Sprint 5 access control. The reviewer
  dashboard requires an authenticated user and includes only projects the user
  can read. The organization dashboard requires organization membership; the
  reviewer workload summary requires org_admin or senior_reviewer. Project
  workload requires project read access.
- Assignment and priority updates require project admin (or organization admin)
  access. They write `project_assignment_updated` and `project_priority_updated`
  audit events. Reviewer-entered reviewer names and notes are checked against the
  prohibited-language guard, and review priority is validated against the allowed
  set (low, standard, elevated, time_sensitive). urgent is intentionally absent.
- Dashboard responses never include full extracted page text, full applicant
  response text, full comment letter text, a raw filesystem path, a storage key, a
  storage bucket, a signed URL, a token, a password, a password hash, or any
  credential. Metrics are aggregate counts and safe aging labels only.
- Aging buckets and due date indicators are workflow timing helpers. Past due
  means a reviewer-set due date has passed; it is not an engineering outcome.

## Deployment hardening and observability (Sprint 10)

Production Foundations Sprint 10 adds a deployment readiness and observability
layer: an environment validation service, public health and readiness checks,
admin-gated environment and storage diagnostics, public frontend-connection and
security-boundary diagnostics, and a safe structured logger with a redaction
helper. See
[DEPLOYMENT_HARDENING_AND_OBSERVABILITY.md](DEPLOYMENT_HARDENING_AND_OBSERVABILITY.md),
[API_HEALTH_READINESS_AND_DIAGNOSTICS.md](API_HEALTH_READINESS_AND_DIAGNOSTICS.md),
and [ENVIRONMENT_VALIDATION.md](ENVIRONMENT_VALIDATION.md).

- Deployment diagnostics expose only safe operational status. They report whether
  a value is present and whether it looks ready, never a secret value, a
  credential, a path, a storage key, a signed URL, or any private project data.
  Secret-like keys are masked to `[redacted]` and path-like keys to `[set]` in the
  safe logger, and the startup configuration log event records provider names and
  flags with no secrets.
- Detailed diagnostics are admin-gated. The environment diagnostic requires an
  organization admin; the storage diagnostic requires an authenticated user.
  Readiness is public but sanitized to operational status only, and the
  frontend-config and security-boundary routes are public guidance only.
- The readiness check confirms database connectivity with a `SELECT 1`, required
  configuration presence, and storage provider readiness, reporting operational
  status only. The auth secret is reported as `needs_operator_review` when it
  equals the development default, and its value is never returned.
- Diagnostics never log or return tokens, passwords, password hashes, raw uploaded
  content, full extracted page text, full applicant response text, full comment
  letter text, raw storage paths, storage keys, signed URLs, or object storage
  credentials.
- Diagnostics are operational indicators only. A readiness, environment, or
  storage status reports whether a service is available and whether configuration
  is present. It is not an engineering or compliance determination and does not
  approve plans, certify compliance, validate design, declare a project safe, or
  resolve an issue.

## Known limitations

- Local authentication only; no SSO and no hardened production session system
  yet. No enterprise tenant isolation claims.
- No applicant-facing portal yet; applicant responses are reviewer-entered
  records kept for reviewer review.
- No full applicant portal yet; the applicant role is a limited placeholder.
- Durable object storage must be configured in deployment; the default local
  provider is for development only and is not durable across redeploys without a
  mounted volume. No malware scanning yet.
- No database migrations in the prototype; recreate an existing development
  database to pick up the new columns.
