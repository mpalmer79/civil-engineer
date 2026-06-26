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

## Known limitations

- Local authentication only; no SSO and no hardened production session system
  yet. No enterprise tenant isolation claims.
- No full applicant portal yet; the applicant role is a limited placeholder.
- Durable object storage must be configured in deployment; the default local
  provider is for development only and is not durable across redeploys without a
  mounted volume. No malware scanning yet.
- No database migrations in the prototype; recreate an existing development
  database to pick up the new columns.
