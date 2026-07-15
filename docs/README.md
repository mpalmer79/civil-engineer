# Documentation Map

This is the index for Civil Engineer AI documentation. The canonical current-state
set is small and authoritative. Historical phase and sprint records, superseded
specifications, and the folded per-feature and per-API notes are preserved for
provenance under `docs/archive/` and are not implementation guidance.

## Canonical documents

- [PRODUCT.md](PRODUCT.md): what the product does, who it is for, the review
  workflow, the capability boundary, and the real-versus-seeded map.
- [ARCHITECTURE.md](ARCHITECTURE.md): context and container view, frontend and
  backend structure, subsystems, data stores, observability, and failure modes.
- [DOMAIN_MODEL.md](DOMAIN_MODEL.md): the review-support domain model.
- [ROUTE_ARCHITECTURE.md](ROUTE_ARCHITECTURE.md): the canonical route map.
- [SECURITY.md](SECURITY.md): the professional boundary, the proxy threat model,
  authentication and access control, and tenant isolation.
- [OPERATIONS.md](OPERATIONS.md): release readiness, pilot operations, account
  lifecycle email, billing and usage, and the live-site checklist.
- [DEPLOYMENT.md](DEPLOYMENT.md): Railway topology, the production database and
  migrations, hardening, and environment validation.
- [TESTING.md](TESTING.md): test types, coverage and complexity budgets, and the
  local and CI expectations.
- [API.md](API.md): the API surfaces, deferring the contract to the OpenAPI
  schema.
- [DXF_VALIDATION.md](DXF_VALIDATION.md): the DXF proof methodology, ground truth,
  artifacts, and what is and is not proven.
- [REFERENCE_PROJECT.md](REFERENCE_PROJECT.md): the synthetic Brookside Meadows
  reference project and its seed data.
- [ROADMAP.md](ROADMAP.md): committed, planned, research, deferred, and
  out-of-scope work.

## Decision records

Architecture decision records live in [adr/](adr/), numbered 0001 through 0010.

## Internal and archived

- [internal/](internal/): engineering-internal notes, including the dependency
  remediation ledger, the consolidation records, and this consolidation's
  disposition matrix.
- [archive/](archive/): historical, non-authoritative snapshots. See
  [archive/README.md](archive/README.md).
- [security/](security/): the detailed backend-for-frontend proxy threat model,
  referenced from SECURITY.md and from source comments.
