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

## Authentication placeholder

This sprint has no real authentication. A clearly labeled demo reviewer identity
(`actor_demo_reviewer`) provides attribution so real actions have an actor. It
grants no access and will be replaced when authentication lands (Phase 4).

## Known limitations

- No authentication, roles, or tenant separation yet.
- Local file system storage only; no object storage, malware scanning, or
  backups yet.
- No database migrations in the prototype; recreate an existing development
  database to pick up the new columns.
