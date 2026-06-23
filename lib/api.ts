// Frontend API client for the Civil Engineer AI backend.
//
// Phase 2 strategy: each function fetches from the FastAPI backend when it is
// available and maps the snake_case API payload into the camelCase shapes the
// Phase 1 components already use. If the backend cannot be reached (for example
// during a static build with no server running), it falls back to the local
// seeded data so pages still render. This keeps a single set of component types
// while making the app backend-driven when the API is up.

import { brookside, projectMetrics, type BooksideProject } from "@/data/brookside";
import { documents as staticDocuments, type ReviewDocument } from "@/data/documents";
import { checklist as staticChecklist, type ChecklistItem } from "@/data/checklist";
import { findings as staticFindings, type Finding } from "@/data/findings";
import { auditEvents as staticAuditEvents, type AuditEvent } from "@/data/auditEvents";
import {
  evaluationCases as staticEvaluationCases,
  evaluationSummary as staticEvaluationSummary,
  type EvaluationCase,
} from "@/data/evaluationCases";
import { hotspots as staticHotspots, type Hotspot } from "@/data/hotspots";

export const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

export const PROJECT_ID = "proj_brookside_meadows";

async function safeFetch<T>(path: string): Promise<T | null> {
  try {
    const res = await fetch(`${API_BASE_URL}${path}`, { cache: "no-store" });
    if (!res.ok) return null;
    return (await res.json()) as T;
  } catch {
    // Backend unavailable. Callers fall back to static seed data.
    return null;
  }
}

// Backend payload shapes (snake_case), kept local to the mapping layer.

type ApiProject = {
  project_id: string;
  project_name: string;
  project_type: string;
  location_context: string;
  jurisdiction: string;
  review_type: string;
  review_domain: string;
  acreage: number;
  disturbed_area: number;
  proposed_lots: number;
  status: string;
  summary: string;
  site_conditions: { type: string; label: string; description: string }[];
  proposed_improvements: {
    type: string;
    label: string;
    aliases: string[];
    description: string;
  }[];
  known_constraints: string[];
};

type ApiDocument = {
  document_id: string;
  file_name: string;
  document_type: string;
  status: ReviewDocument["status"];
  purpose: string;
  expected_key_information: string;
  intentionally_missing_or_conflicting_information: string | null;
};

type ApiChecklistItem = {
  checklist_item_id: string;
  category: string;
  requirement: string;
  expected_evidence: string;
  supporting_documents: string[];
  risk_level: ChecklistItem["riskLevel"];
  applies_when: string;
  expected_status_for_brookside_meadows: ChecklistItem["expectedStatus"];
  planted_issue: string | null;
};

type ApiFinding = {
  finding_id: string;
  planted_issue: string;
  title: string;
  category: string;
  risk_level: Finding["riskLevel"];
  expected_status: Finding["expectedStatus"];
  evidence_to_find: string;
  reason_it_matters: string;
  recommended_human_action: string;
  human_review_status: string;
  related_checklist_items: string[];
  related_documents: string[];
};

type ApiAuditEvent = {
  audit_event_id: string;
  event_type: string;
  actor_type: AuditEvent["actorType"];
  related_entity_type: string;
  related_entity_id: string;
  description: string;
  timestamp: string;
};

type ApiEvaluationCase = {
  eval_case_id: string;
  name: string;
  input_documents: string[];
  expected_findings: string[];
  expected_risk_level: EvaluationCase["expectedRiskLevel"];
  evaluation_metric: string;
  seeded_result: {
    expected_findings_detected: string;
    source_citation_accuracy: number;
    false_positives: number;
    false_negatives: number;
    unsupported_claims: number;
    prohibited_wording_count: number;
    human_review_required: number;
    passed: boolean;
  };
};

type ApiHotspot = {
  hotspot_id: string;
  name: string;
  category: Hotspot["category"];
  short_description: string;
  civil_purpose: string;
  related_checklist_items: string[];
  related_planted_issues: string[];
  future_drilldown: string;
  position_x_percent: number;
  position_y_percent: number;
};

export async function getProject(): Promise<BooksideProject> {
  const data = await safeFetch<ApiProject>(`/api/v1/projects/${PROJECT_ID}`);
  if (!data) return brookside;
  return {
    projectId: data.project_id,
    projectName: data.project_name,
    projectType: data.project_type,
    locationContext: data.location_context,
    jurisdiction: data.jurisdiction,
    reviewType: data.review_type,
    reviewDomain: data.review_domain,
    acreage: data.acreage,
    disturbedAcres: data.disturbed_area,
    proposedLots: data.proposed_lots,
    status: data.status,
    hasInfiltrationPractice: brookside.hasInfiltrationPractice,
    hasDetentionBasin: brookside.hasDetentionBasin,
    summary: data.summary,
    siteConditions: data.site_conditions,
    proposedImprovements: data.proposed_improvements,
    knownConstraints: data.known_constraints,
  };
}

export async function getDocuments(): Promise<ReviewDocument[]> {
  const data = await safeFetch<ApiDocument[]>(
    `/api/v1/projects/${PROJECT_ID}/documents`,
  );
  if (!data) return staticDocuments;
  return data.map((d) => ({
    documentId: d.document_id,
    fileName: d.file_name,
    documentType: d.document_type,
    status: d.status,
    purpose: d.purpose,
    expectedKeyInformation: d.expected_key_information,
    knownIssue: d.intentionally_missing_or_conflicting_information,
  }));
}

export async function getChecklist(): Promise<ChecklistItem[]> {
  const data = await safeFetch<ApiChecklistItem[]>(
    `/api/v1/projects/${PROJECT_ID}/checklist`,
  );
  if (!data) return staticChecklist;
  return data.map((c) => ({
    checklistItemId: c.checklist_item_id,
    category: c.category,
    requirement: c.requirement,
    expectedEvidence: c.expected_evidence,
    supportingDocuments: c.supporting_documents.join(", "),
    riskLevel: c.risk_level,
    appliesWhen: c.applies_when,
    expectedStatus: c.expected_status_for_brookside_meadows,
    plantedIssue: c.planted_issue,
  }));
}

export async function getFindings(): Promise<Finding[]> {
  const data = await safeFetch<ApiFinding[]>(
    `/api/v1/projects/${PROJECT_ID}/findings`,
  );
  if (!data) return staticFindings;
  return data.map((f) => ({
    findingId: f.finding_id,
    plantedIssue: f.planted_issue,
    title: f.title,
    category: f.category,
    riskLevel: f.risk_level,
    expectedStatus: f.expected_status,
    checklistItemId: f.related_checklist_items[0] ?? "",
    evidenceToFind: f.evidence_to_find,
    whyItMatters: f.reason_it_matters,
    recommendedHumanAction: f.recommended_human_action,
    // Phase 1 uses "pending" for an unactioned finding; the backend expresses
    // the same state as "requires_human_review".
    humanReviewState: "pending",
  }));
}

export async function getAuditEvents(): Promise<AuditEvent[]> {
  const data = await safeFetch<ApiAuditEvent[]>(
    `/api/v1/projects/${PROJECT_ID}/audit-events`,
  );
  if (!data) return staticAuditEvents;
  return data.map((e) => ({
    auditEventId: e.audit_event_id,
    eventType: e.event_type,
    actorType: e.actor_type,
    relatedEntity: e.related_entity_id,
    timestamp: e.timestamp,
    description: e.description,
  }));
}

function mapEvaluationCase(c: ApiEvaluationCase): EvaluationCase {
  const r = c.seeded_result;
  return {
    evalCaseId: c.eval_case_id,
    name: c.name,
    inputDocuments: c.input_documents,
    expectedFindingId: c.expected_findings[0] ?? null,
    expectedRiskLevel: c.expected_risk_level,
    primaryMetric: c.evaluation_metric,
    expectedFindingsDetected: r.expected_findings_detected,
    sourceCitationAccuracy: r.source_citation_accuracy,
    falsePositives: r.false_positives,
    falseNegatives: r.false_negatives,
    unsupportedClaims: r.unsupported_claims,
    prohibitedWordingCount: r.prohibited_wording_count,
    humanReviewRequired: r.human_review_required,
    passed: r.passed,
  };
}

export type EvaluationData = {
  cases: EvaluationCase[];
  summary: typeof staticEvaluationSummary;
};

export async function getEvaluationData(): Promise<EvaluationData> {
  const data = await safeFetch<ApiEvaluationCase[]>("/api/v1/evaluation-cases");
  if (!data) {
    return { cases: staticEvaluationCases, summary: staticEvaluationSummary };
  }
  const cases = data.map(mapEvaluationCase);
  const summary = {
    totalCases: cases.length,
    casesPassed: cases.filter((c) => c.passed).length,
    expectedFindingsDetected: `${cases.filter(
      (c) => c.expectedFindingId !== null,
    ).length} / ${cases.filter((c) => c.expectedFindingId !== null).length}`,
    averageSourceCitationAccuracy:
      cases.reduce((n, c) => n + c.sourceCitationAccuracy, 0) / cases.length,
    totalFalsePositives: cases.reduce((n, c) => n + c.falsePositives, 0),
    totalFalseNegatives: cases.reduce((n, c) => n + c.falseNegatives, 0),
    totalUnsupportedClaims: cases.reduce((n, c) => n + c.unsupportedClaims, 0),
    prohibitedWordingCount: cases.reduce(
      (n, c) => n + c.prohibitedWordingCount,
      0,
    ),
    humanReviewRequired: cases.reduce((n, c) => n + c.humanReviewRequired, 0),
  };
  return { cases, summary };
}

export async function getHotspots(): Promise<Hotspot[]> {
  const data = await safeFetch<ApiHotspot[]>(
    `/api/v1/projects/${PROJECT_ID}/hotspots`,
  );
  if (!data) return staticHotspots;
  return data.map((h) => ({
    id: h.hotspot_id,
    name: h.name,
    category: h.category,
    shortDescription: h.short_description,
    civilPurpose: h.civil_purpose,
    relatedChecklistItems: h.related_checklist_items,
    relatedPlantedIssues: h.related_planted_issues,
    futureDrilldown: h.future_drilldown,
    position: { xPercent: h.position_x_percent, yPercent: h.position_y_percent },
  }));
}

export { projectMetrics };
