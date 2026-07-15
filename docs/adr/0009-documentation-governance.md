# ADR 0009: Documentation governance

Status: accepted

## Context

The repository accumulated more than one hundred Markdown documents: seventeen phase histories, ten sprint histories, ten per-feature API references, four recruiter-oriented walkthroughs, several overlapping architecture, security, deployment, and roadmap documents. New readers could not tell which document was authoritative, and doc-assertion tests pinned historical documents in place.

## Decision

1. The active documentation set is one canonical document per subject: PRODUCT, ARCHITECTURE, DOMAIN_MODEL, SECURITY, OPERATIONS, DEPLOYMENT, TESTING, API, DXF_VALIDATION, REFERENCE_PROJECT, ROADMAP, ROUTE_ARCHITECTURE, plus the ADR series and docs/README.md as the map.
2. Historical material moves to docs/archive, which carries a README stating that archived documents are historical and non-authoritative. Nothing is deleted if it records a decision; durable content is folded into the canonical set before the source is archived.
3. Working records of large initiatives live under docs/internal (baselines, plans, disposition matrices, validation reports). They are engineering documents, not product documentation.
4. New durable decisions get an ADR. Feature work updates the relevant canonical document in the same change; it does not create a new standalone document per feature.
5. Tests and scripts may assert that canonical documents exist and contain required boundary language, but must not pin archived documents.
6. Documentation follows the same content gates as code: no attribution footers, no em dashes, review-support language only, and no capability claims beyond what the system does.

## Consequences

- A reader finds one authoritative document per subject; history is preserved but clearly separated.
- The guide knowledge catalog and doc-assertion tests reference only the canonical set, so consolidations do not silently break gates.
