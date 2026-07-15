# API

This is the canonical summary of the Civil Engineer AI backend API surfaces. It
folds in the ten former per-surface API documents. The authoritative contract is
the generated OpenAPI schema, not this page: see
`lib/api/generated/openapi.json` (regenerated from the FastAPI app and checked in
CI by `scripts/generate-api-types.mjs --check`). Frontend wire types are
generated from that schema, so they stay aligned with backend schemas.

All routes are versioned under `/api/v1`. Project-owned routes are gated by the
access-control guards described in `docs/SECURITY.md`: unauthenticated protected
requests return 401, and authenticated requests without permission return 403.
No route returns a secret, a raw storage path, a storage key, a signed URL, a
token, or full extracted text.

## Surfaces

- Authentication and access control: sign up, sign in, sign out, current-user
  check, account profile, password reset, organization team invitations, and the
  organization and per-project access grants.
- Real project intake: create and manage real projects, register or upload
  documents with validated intake, and record intake status. Review-support
  status vocabulary only.
- File storage: upload, download, and storage status through the storage provider
  abstraction. Responses carry safe metadata only.
- PDF evidence citations: page-level PDF text indexing (pypdf) and page-anchored
  evidence citations.
- Evidence retrieval: deterministic ranked search over indexed page text and
  reviewer-facing evidence candidates.
- Checklist review: rule-pack-seeded checklists, checklist items, and evidence
  status.
- Response matrix and resubmittals: the applicant response matrix, resubmittal
  rounds, revision comparison, and issue carry-forward.
- Response packages: reviewer-controlled response packages and deterministic
  comment-letter drafts.
- Operational metrics: reviewer dashboard, organization workload, per-project
  workload, and the reviewer queue. Aggregate review-support indicators only.
- Health, readiness, and diagnostics: public `/health` and `/api/v1/readiness`
  and admin-gated environment and storage diagnostics, all reporting safe
  operational status only.
- Background jobs: enqueue PDF indexing or DXF parsing on the worker and poll job
  status, scoped to the project. Additive to the synchronous index and parse
  routes; requires the worker process to run. See
  `docs/adr/0012-background-job-queue.md`.

For request and response shapes, field names, and status codes, use the OpenAPI
schema.
