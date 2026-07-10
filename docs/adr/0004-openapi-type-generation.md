# ADR 0004: OpenAPI-derived frontend types

Status: Proposed (direction accepted, implementation staged)

## Context

Frontend TypeScript types in `lib/api/*.ts` are maintained by hand against the
FastAPI Pydantic schemas. Each module maps snake_case wire payloads to
camelCase view models. Drift between the two is caught today by unit tests and
by the mapping layer's narrow field access, not by the type system.

## Decision

Adopt generation of wire types from the FastAPI OpenAPI document:

1. Export the schema with a repeatable script
   (`python -c "import json; from app.main import app; print(json.dumps(app.openapi()))"`)
   into a committed `lib/api/generated/openapi.json`.
2. Generate TypeScript wire types with `openapi-typescript` into
   `lib/api/generated/schema.d.ts`. Generated files are never edited by hand.
3. Keep the existing camelCase view models as the UI-facing layer; the
   adapters in each module convert wire types to view models, so generation
   changes the wire layer only.
4. Add a CI freshness check that regenerates the schema and fails when the
   committed output is stale.
5. Migrate the highest-risk modules first: auth, projects, documents,
   evidence, findings, reviewer queue, command center, review packets,
   response packages, CAD intake.

## Status and rationale for staging

The generation tooling introduces a new build-time dependency and a large
mechanical diff across thirty-plus modules. It is staged behind the security
and data-honesty work that changed observable behavior. Until it lands, the
contract is protected by the backend's schema tests, the frontend mapping
tests, and the narrow adapters. This ADR records the agreed target so the
migration does not drift into ad hoc decisions.
