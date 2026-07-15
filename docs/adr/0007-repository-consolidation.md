# ADR 0007: Repository consolidation and bounded-context module structure

Status: accepted

## Context

The repository grew through fourteen feature phases and ten production-foundation sprints. That history left oversized modules (a 2,330-line model file, services up to 2,014 lines, a 1,380-line shared vocabulary module, 844-line pages, 1,245-line API modules), more than one hundred Markdown documents, duplicated request helpers, and recruiter-oriented product framing. The cost showed up as review friction, unclear ownership boundaries, and risk when changing shared modules.

## Decision

1. Backend code is organized by bounded context inside the existing layering rather than a parallel tree. Models live in backend/app/db/models as one module per context (projects, documents, evidence, checklists, findings, evaluation, plans, review_packets, workflow, response_packages, responses, review_cycles, audit, plus the previously split identity, billing, cad, command_center). models/__init__.py is the compatibility facade; application code imports `from app.db import models` and never a specific model module.
2. Per-domain status and action vocabularies live in backend/app/core/vocab, one module per context. backend/app/core/safety.py remains the single canonical home of engineering-safety guardrail language and re-exports the vocabulary names, so its import surface is stable.
3. Oversized services become packages whose __init__ re-exports the public functions and whose submodules split by responsibility (for example uploads, parsing, findings, insights). Callers keep importing the service module path they always used.
4. Seed data lives in backend/app/db/seeds with an orchestrator and per-domain fixture modules; the previous seed module paths remain as thin facades.
5. Frontend API modules over the size budget become directories (types, queries, mutations, index) that preserve their import specifiers. Shared request behavior, including mutations, lives in lib/api/client.ts and shared helpers, not per-module copies.
6. Oversized pages become composition layers over per-section components (components/home, components/proof).
7. Size budgets are enforced by scripts/check-complexity.mjs in CI: TypeScript and TSX warn at 300 lines and fail at 500; Python warns at 400 and fails at 700. Generated files, migrations, and a small allowlist with written cohesion reasons are exempt.
8. Transaction ownership: services own commits. Routers parse, authorize, delegate, and translate domain errors to HTTP; they do not commit. The small number of pre-existing router commits are legacy to be migrated, not a pattern to extend.

## Consequences

- Module moves never changed table names, column names, constraints, the Alembic chain, or the OpenAPI contract; CI verifies the latter two.
- Compatibility facades mean import sites did not churn, at the cost of one extra indirection layer per split module. New code should import from the facade, not the submodules.
- The complexity budget prevents regression toward monolithic modules; exceeding it requires either decomposition or a reviewed allowlist entry.
