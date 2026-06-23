// Seeded audit trail for the Brookside Meadows review fixture.
// Phase 1 shows a static, plausible audit timeline to demonstrate
// traceability. Later phases will record real system and human actions.

export type AuditActorType = "system" | "reviewer" | "evaluator";

export type AuditEvent = {
  auditEventId: string;
  eventType: string;
  actorType: AuditActorType;
  relatedEntity: string;
  timestamp: string; // ISO 8601
  description: string;
};

export const auditEvents: AuditEvent[] = [
  {
    auditEventId: "audit_001",
    eventType: "project_fixture_loaded",
    actorType: "system",
    relatedEntity: "proj_brookside_meadows",
    timestamp: "2026-06-22T13:02:11Z",
    description:
      "Brookside Meadows review fixture loaded with project metadata and known constraints.",
  },
  {
    auditEventId: "audit_002",
    eventType: "document_package_seeded",
    actorType: "system",
    relatedEntity: "review_package_initial_submission",
    timestamp: "2026-06-22T13:02:14Z",
    description:
      "Initial submission package registered: 19 document records (present, partial, missing, referenced, and not-yet-submitted).",
  },
  {
    auditEventId: "audit_003",
    eventType: "checklist_applied",
    actorType: "system",
    relatedEntity: "stormwater_checklist_v1",
    timestamp: "2026-06-22T13:02:18Z",
    description:
      "19 stormwater checklist items applied to the project based on applicability flags (infiltration practice, detention basin, downstream structure).",
  },
  {
    auditEventId: "audit_004",
    eventType: "evidence_mapped",
    actorType: "system",
    relatedEntity: "chk_infiltration_testing",
    timestamp: "2026-06-22T13:02:23Z",
    description:
      "Expected evidence for the infiltration-testing item mapped to supporting document types; no infiltration testing log located in the package.",
  },
  {
    auditEventId: "audit_005",
    eventType: "finding_generated",
    actorType: "system",
    relatedEntity: "find_infiltration_missing",
    timestamp: "2026-06-22T13:02:25Z",
    description:
      "Review-support finding drafted: infiltration testing not found for proposed infiltration basin. Status: missing. Routed to human review.",
  },
  {
    auditEventId: "audit_006",
    eventType: "finding_generated",
    actorType: "system",
    relatedEntity: "find_storm_conflict",
    timestamp: "2026-06-22T13:02:27Z",
    description:
      "Review-support finding drafted: design-storm assumption conflicts with town standard. Status: conflicting. Routed to human review.",
  },
  {
    auditEventId: "audit_007",
    eventType: "safety_wording_validation",
    actorType: "system",
    relatedEntity: "review_run_001",
    timestamp: "2026-06-22T13:02:31Z",
    description:
      "Safety wording validation passed for all drafted findings: no prohibited terms (approved, certified, compliant, safe) detected.",
  },
  {
    auditEventId: "audit_008",
    eventType: "human_review_action",
    actorType: "reviewer",
    relatedEntity: "find_infiltration_missing",
    timestamp: "2026-06-22T15:41:05Z",
    description:
      "Reviewer (Town Engineer) opened the infiltration-testing finding and inspected the mapped evidence. Action pending applicant response.",
  },
  {
    auditEventId: "audit_009",
    eventType: "human_review_action",
    actorType: "reviewer",
    relatedEntity: "find_basin_naming",
    timestamp: "2026-06-22T15:48:52Z",
    description:
      "Reviewer noted the Pond A / Basin 1 naming conflict for inclusion in the comment letter. Requires reviewer confirmation before issuance.",
  },
  {
    auditEventId: "audit_010",
    eventType: "evaluation_case_scored",
    actorType: "evaluator",
    relatedEntity: "eval_infiltration_missing",
    timestamp: "2026-06-22T16:10:00Z",
    description:
      "Evaluation case scored: expected missing-infiltration-testing finding detected with valid source mapping. Recorded for the evaluation dashboard.",
  },
];
