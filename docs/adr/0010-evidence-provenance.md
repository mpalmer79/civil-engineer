# ADR 0010: Evidence provenance model

Status: accepted

## Context

Every review-support finding must be traceable to its source evidence, and evidence must be traceable to how it was produced. The consolidation initiative reviewed the provenance fields that exist today and which additions would require schema and contract changes.

## Current model

- Documents carry source_mode (seeded demo fixture versus uploaded), name, and storage metadata. Document pages carry page numbers and extracted text from the pypdf text layer.
- Document chunks carry the source document, page linkage, and content; chunk embeddings carry content_hash (staleness detection) and the embedding provider identity.
- Evidence citations carry the source document, page_number, snippet, created_at, created_by actor id and name, and source_mode (user_created versus seeded).
- Evidence candidates carry the source document, page_number, candidate_origin (which retrieval mode produced them), created_by actor identity, status, and created_at.
- CAD metadata carries parser_name and parser_version for every parsed DXF, and the deterministic proof pipeline publishes content hashes for its artifacts.
- Audit events record material actions with actor attribution.

## Decision

1. The current model is the supported provenance contract: source document, page, creation actor, creation time, source mode or origin, parser identity for CAD extractions, and content hashing for chunk embeddings and proof artifacts.
2. The following fields were evaluated and deliberately deferred because each is a database column addition with migration, OpenAPI contract, and frontend type consequences, and no current workflow reads them: extraction_method and extractor_name/extractor_version on citations (today derivable: PDF citations come from the pypdf text-layer index, CAD references from the recorded parser identity), source_entity_id for DXF entity-level anchors, manually_verified_at and manually_verified_by on citations, and per-citation confidence scores (ranking scores exist on retrieval results but are not persisted onto citations).
3. When any deferred field is added, it arrives with an Alembic migration, regenerated contract, frontend mapping, and an update to this ADR in the same change.

## Consequences

- Reviewers can trace every citation to a document and page and every CAD reference to a parser version today.
- Entity-level DXF anchoring and explicit manual-verification stamps are known gaps, recorded in ROADMAP.md, rather than silently absent.
