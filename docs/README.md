# Documentation index

The authoritative current-state documents are listed first. Historical phase
and sprint records are preserved for provenance and are not implementation
guidance; where a historical document conflicts with a current-state document,
the current-state document wins.

## Start here

- [PRODUCT_OVERVIEW.md](PRODUCT_OVERVIEW.md): what the product is and who it serves
- [recruiter-walkthrough.md](recruiter-walkthrough.md): the five-minute review path
- [real-vs-mocked.md](real-vs-mocked.md): what is implemented, seeded, simulated, or out of scope
- [100_SCORE_TRANSFORMATION.md](100_SCORE_TRANSFORMATION.md): transformation tracker, baseline, defect register, and validation results

## Product

- [BROOKSIDE_MEADOWS_PROJECT_STORY.md](BROOKSIDE_MEADOWS_PROJECT_STORY.md): the synthetic case study, including the ten planted issues
- [DEMO_WALKTHROUGH.md](DEMO_WALKTHROUGH.md), [recruiter-walkthrough-storyboard.md](recruiter-walkthrough-storyboard.md)
- [SAAS_POSITIONING.md](SAAS_POSITIONING.md), [ROADMAP.md](ROADMAP.md), [REAL_WORLD_PRODUCT_ROADMAP.md](REAL_WORLD_PRODUCT_ROADMAP.md)
- [METRICS_BOUNDARY_AND_LIMITATIONS.md](METRICS_BOUNDARY_AND_LIMITATIONS.md)

## Architecture

- [ARCHITECTURE.md](ARCHITECTURE.md), [architecture-overview.md](architecture-overview.md)
- [ROUTE_ARCHITECTURE.md](ROUTE_ARCHITECTURE.md): every route, classified
- [DOMAIN_MODEL.md](DOMAIN_MODEL.md), [technical-decisions.md](technical-decisions.md)
- Architecture decision records: [adr/](adr/)
  - [0001 Canonical routes and shells](adr/0001-canonical-routes-and-shells.md)
  - [0002 Data-source boundaries](adr/0002-data-source-boundaries.md)
  - [0003 Secure session architecture](adr/0003-secure-session-architecture.md)
  - [0004 OpenAPI type generation](adr/0004-openapi-type-generation.md)
  - [0005 Backend domain decomposition](adr/0005-backend-domain-decomposition.md)
  - [0006 Local guide knowledge and retrieval architecture](adr/0006-local-guide-knowledge-architecture.md)

## Security and professional boundary

- [SECURITY_AND_PROFESSIONAL_BOUNDARY.md](SECURITY_AND_PROFESSIONAL_BOUNDARY.md)
- [security/BFF_PROXY_THREAT_MODEL.md](security/BFF_PROXY_THREAT_MODEL.md): the proxy threat model
- [AUTHENTICATION_AND_ACCESS_CONTROL.md](AUTHENTICATION_AND_ACCESS_CONTROL.md), [AUTH_LIFECYCLE.md](AUTH_LIFECYCLE.md)
- [TENANT_ISOLATION_AUDIT.md](TENANT_ISOLATION_AUDIT.md)
- [COMMENT_LETTER_TEMPLATE_BOUNDARY.md](COMMENT_LETTER_TEMPLATE_BOUNDARY.md)

## API references

`API_AUTH_AND_ACCESS_CONTROL`, `API_CHECKLIST_REVIEW`,
`API_EVIDENCE_RETRIEVAL`, `API_FILE_STORAGE`,
`API_HEALTH_READINESS_AND_DIAGNOSTICS`, `API_OPERATIONAL_METRICS`,
`API_PDF_EVIDENCE_CITATIONS`, `API_REAL_PROJECT_INTAKE`,
`API_RESPONSE_MATRIX_AND_RESUBMITTALS`, `API_RESPONSE_PACKAGES`

## Workflows and features

- [PDF_PAGE_INDEXING_AND_EVIDENCE_CITATIONS.md](PDF_PAGE_INDEXING_AND_EVIDENCE_CITATIONS.md), [EVIDENCE_RETRIEVAL_AND_DRAFT_QUEUE.md](EVIDENCE_RETRIEVAL_AND_DRAFT_QUEUE.md)
- [CHECKLIST_RULE_PACK_FOUNDATION.md](CHECKLIST_RULE_PACK_FOUNDATION.md), [APPLICANT_RESPONSE_MATRIX.md](APPLICANT_RESPONSE_MATRIX.md)
- [RESPONSE_PACKAGE_AND_COMMENT_LETTER_WORKFLOW.md](RESPONSE_PACKAGE_AND_COMMENT_LETTER_WORKFLOW.md), [RESUBMITTAL_COLLABORATION_WORKFLOW.md](RESUBMITTAL_COLLABORATION_WORKFLOW.md)
- [REVIEWER_DASHBOARD_AND_WORKLOAD.md](REVIEWER_DASHBOARD_AND_WORKLOAD.md), [PROJECT_TRACEABILITY_AND_HANDOFF.md](PROJECT_TRACEABILITY_AND_HANDOFF.md)
- [CAD_INTEGRATION_ROADMAP.md](CAD_INTEGRATION_ROADMAP.md), [STORAGE_PROVIDER_ABSTRACTION.md](STORAGE_PROVIDER_ABSTRACTION.md)
- [BILLING_AND_USAGE.md](BILLING_AND_USAGE.md), [STRIPE_BILLING.md](STRIPE_BILLING.md), [EMAIL_DELIVERY.md](EMAIL_DELIVERY.md)

## Demo data

- [SEED_DATA_PLAN.md](SEED_DATA_PLAN.md), [synthetic-demo-data.md](synthetic-demo-data.md)

## Deployment and operations

- [RELEASE_READINESS.md](RELEASE_READINESS.md), [PILOT_RELEASE_CHECKLIST.md](PILOT_RELEASE_CHECKLIST.md), [PILOT_OPERATIONS.md](PILOT_OPERATIONS.md)
- [RAILWAY_DEPLOYMENT_GUIDE.md](RAILWAY_DEPLOYMENT_GUIDE.md), [PRODUCTION_DATABASE.md](PRODUCTION_DATABASE.md)
- [DEPLOYMENT_HARDENING_AND_OBSERVABILITY.md](DEPLOYMENT_HARDENING_AND_OBSERVABILITY.md), [ENVIRONMENT_VALIDATION.md](ENVIRONMENT_VALIDATION.md), [LIVE_SITE_VERIFICATION.md](LIVE_SITE_VERIFICATION.md)

## Testing

- [test-summary.md](test-summary.md)
- [civil-engineer-ai-guide.md](civil-engineer-ai-guide.md): guide architecture, evaluation targets, and freshness gate

## Historical phase and sprint records (archived)

These document the build sequence as it happened. They are not current
implementation guidance.

- Phases: `PHASE_0_FOUNDATION` through `PHASE_14_COMMAND_CENTER_DASHBOARD`
- Sprints: `PRODUCTION_FOUNDATIONS_SPRINT_1` through `PRODUCTION_FOUNDATIONS_SPRINT_10`
- Early planning: `V1_SCOPE`, `RESEARCH_AND_SYSTEM_DESIGN`, `HOMEPAGE_HOTSPOT_PLAN`, `DESIGN_PARTNER_OUTREACH`, `civil-engineer-ai-saas-roadmap`, `civil-engineer-ai-guide`
