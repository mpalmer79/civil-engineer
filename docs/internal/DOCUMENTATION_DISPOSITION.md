# Documentation Disposition

Internal engineering document. Per-file disposition of the 105 Markdown documents that existed at the start of the consolidation. Actions: KEEP (stays active, possibly renamed), MERGE (content folded into the named canonical document, source archived), ARCHIVE (moved to docs/archive, historical and non-authoritative), DELETE (removed, no durable value).

Canonical active set after consolidation: README.md, CLAUDE.md, backend/README.md, docs/PRODUCT.md, docs/ARCHITECTURE.md, docs/DOMAIN_MODEL.md, docs/SECURITY.md, docs/OPERATIONS.md, docs/DEPLOYMENT.md, docs/TESTING.md, docs/API.md, docs/DXF_VALIDATION.md, docs/REFERENCE_PROJECT.md, docs/ROADMAP.md, docs/ROUTE_ARCHITECTURE.md, docs/README.md (index), docs/adr/*, docs/internal/*, docs/archive/README.md.

## Root

| Document | Purpose | Audience | Action |
| --- | --- | --- | --- |
| README.md | Repo front door, recruiter framing | mixed | KEEP, rewritten as professional product entry |
| CLAUDE.md | Repo operating instructions | eng | KEEP, updated with consolidation rules |
| backend/README.md | Backend developer guide | eng | KEEP |
| public/images/civil-engineer/README.md | Media asset notes | eng | KEEP |

## Product and positioning

| Document | Overlaps | Action |
| --- | --- | --- |
| docs/PRODUCT_OVERVIEW.md | SAAS_POSITIONING, METRICS_BOUNDARY | MERGE into PRODUCT.md |
| docs/SAAS_POSITIONING.md | PRODUCT_OVERVIEW | MERGE into PRODUCT.md |
| docs/METRICS_BOUNDARY_AND_LIMITATIONS.md | PRODUCT_OVERVIEW | MERGE into PRODUCT.md |

## Reference project

| Document | Action |
| --- | --- |
| docs/BROOKSIDE_MEADOWS_PROJECT_STORY.md | MERGE into REFERENCE_PROJECT.md |
| docs/SEED_DATA_PLAN.md | MERGE into REFERENCE_PROJECT.md |
| docs/HOMEPAGE_HOTSPOT_PLAN.md | MERGE into REFERENCE_PROJECT.md (fixture provenance section) |
| docs/synthetic-demo-data.md | MERGE into REFERENCE_PROJECT.md |
| docs/real-vs-mocked.md | MERGE into PRODUCT.md (capability boundary section) |

## Roadmaps

| Document | Action |
| --- | --- |
| docs/ROADMAP.md | KEEP as the single roadmap, restructured (committed, planned, research, deferred, out of scope) |
| docs/REAL_WORLD_PRODUCT_ROADMAP.md | MERGE into ROADMAP.md |
| docs/CAD_INTEGRATION_ROADMAP.md | MERGE into ROADMAP.md |
| docs/civil-engineer-ai-saas-roadmap.md | ARCHIVE |

## Architecture

| Document | Action |
| --- | --- |
| docs/ARCHITECTURE.md (1,428 lines) | KEEP, rewritten as a concise canonical document |
| docs/DOMAIN_MODEL.md | KEEP |
| docs/ROUTE_ARCHITECTURE.md | KEEP |
| docs/architecture-overview.md | MERGE into ARCHITECTURE.md |
| docs/technical-decisions.md | MERGE into ARCHITECTURE.md (ADR pointers) |
| docs/RESEARCH_AND_SYSTEM_DESIGN.md | ARCHIVE |
| docs/adr/0001 through 0006 | KEEP; new ADRs 0007+ added |

## Security

| Document | Action |
| --- | --- |
| docs/SECURITY_AND_PROFESSIONAL_BOUNDARY.md | MERGE into SECURITY.md (primary source) |
| docs/security/BFF_PROXY_THREAT_MODEL.md | MERGE into SECURITY.md (threat model section); source comments updated |
| docs/AUTHENTICATION_AND_ACCESS_CONTROL.md | MERGE into SECURITY.md |
| docs/AUTH_LIFECYCLE.md | MERGE into SECURITY.md |
| docs/TENANT_ISOLATION_AUDIT.md | MERGE into SECURITY.md |
| docs/COMMENT_LETTER_TEMPLATE_BOUNDARY.md | MERGE into SECURITY.md (professional boundary section) |

## API references

All ten API_*.md documents (AUTH_AND_ACCESS_CONTROL, CHECKLIST_REVIEW, EVIDENCE_RETRIEVAL, FILE_STORAGE, HEALTH_READINESS_AND_DIAGNOSTICS, OPERATIONAL_METRICS, PDF_EVIDENCE_CITATIONS, REAL_PROJECT_INTAKE, RESPONSE_MATRIX_AND_RESUBMITTALS, RESPONSE_PACKAGES): MERGE into API.md, which summarizes each surface and defers the authoritative contract to the generated OpenAPI schema.

## Feature and workflow specs

PDF_PAGE_INDEXING_AND_EVIDENCE_CITATIONS, CHECKLIST_RULE_PACK_FOUNDATION, STORAGE_PROVIDER_ABSTRACTION, EVIDENCE_RETRIEVAL_AND_DRAFT_QUEUE, APPLICANT_RESPONSE_MATRIX, RESPONSE_PACKAGE_AND_COMMENT_LETTER_WORKFLOW, RESUBMITTAL_COLLABORATION_WORKFLOW, REVIEWER_DASHBOARD_AND_WORKLOAD, PROJECT_TRACEABILITY_AND_HANDOFF: MERGE into ARCHITECTURE.md (subsystem sections), with workflow detail into PRODUCT.md where user-facing.

## Billing, email, deployment, operations

| Document | Action |
| --- | --- |
| docs/BILLING_AND_USAGE.md, docs/STRIPE_BILLING.md, docs/EMAIL_DELIVERY.md | MERGE into OPERATIONS.md |
| docs/RAILWAY_DEPLOYMENT_GUIDE.md, docs/PRODUCTION_DATABASE.md, docs/DEPLOYMENT_HARDENING_AND_OBSERVABILITY.md, docs/ENVIRONMENT_VALIDATION.md | MERGE into DEPLOYMENT.md |
| docs/RELEASE_READINESS.md, docs/PILOT_RELEASE_CHECKLIST.md, docs/PILOT_OPERATIONS.md, docs/LIVE_SITE_VERIFICATION.md, docs/DESIGN_PARTNER_OUTREACH.md | MERGE into OPERATIONS.md |

## Testing

| Document | Action |
| --- | --- |
| docs/civil-engineer-ai-guide.md | MERGE into TESTING.md (guide freshness) and ARCHITECTURE.md (guide design) |
| docs/test-summary.md | MERGE into TESTING.md |

## DXF validation

| Document | Action |
| --- | --- |
| docs/proof-of-concept/DXF_PROOF_OF_CONCEPT.md, DXF_TEST_METHODOLOGY.md, DXF_LIMITATIONS.md, DXF_ARTIFACT_MANIFEST.md | MERGE into DXF_VALIDATION.md |
| public/proof-of-concept/dxf/DXF_INTEGRATION_TEST_REPORT.md | KEEP (generated by scripts/run_dxf_proof.py, never hand-edited) |

## Historical and recruiter-oriented

| Document | Action |
| --- | --- |
| docs/PHASE_0 through PHASE_14 (17 documents) | ARCHIVE |
| docs/PRODUCTION_FOUNDATIONS_SPRINT_1 through _10 | ARCHIVE |
| docs/100_SCORE_TRANSFORMATION.md | ARCHIVE (CI comment references repointed first) |
| docs/recruiter-walkthrough.md, docs/recruiter-walkthrough-storyboard.md | ARCHIVE |
| docs/DEMO_WALKTHROUGH.md | ARCHIVE |
| docs/V1_SCOPE.md | ARCHIVE |
| docs/README.md | KEEP, rewritten as the documentation map |

## Reference updates required by these moves

- lib/guide/knowledge.ts entries and scripts/generate-guide-knowledge.mjs (walks docs/*.md); regenerate repo-facts.json.
- app/__tests__/recruiterDocs.test.ts replaced by a canonical-docs test asserting the new active set with equally strong content assertions.
- app/__tests__/releaseReadiness.test.ts, deployment and phase doc tests, capabilityClaimsDocs.test.ts repointed to canonical documents.
- scripts/verify-pilot-release.mjs and scripts/verify-live-site.mjs doc path checks repointed.
- Source comments referencing merged or archived docs (data/*.ts, backend config.py, database.py, models, lib/api modules) repointed.
- .github/workflows/ci.yml comment references repointed (done during dependency remediation).
- app/admin/pilot-requests/page.tsx link to PILOT_RELEASE_CHECKLIST.md repointed to OPERATIONS.md.

## Information preservation rule

Nothing is deleted outright: every merged or superseded document moves to docs/archive with its content intact, under an archive README stating that archived material is historical and non-authoritative. Durable decisions were folded into the canonical set before archiving.
