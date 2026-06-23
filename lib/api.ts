// Frontend API client for the Civil Engineer AI backend.
//
// Phase 2 strategy: each function fetches from the FastAPI backend when it is
// available and maps the snake_case API payload into the camelCase shapes the
// Phase 1 components already use. If the backend cannot be reached (for example
// during a static build with no server running), it falls back to the local
// seeded data so pages still render. This keeps a single set of component types
// while making the app backend-driven when the API is up.

import { brookside, projectMetrics, type BrooksideProject } from "@/data/brookside";
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

export async function getProject(): Promise<BrooksideProject> {
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

// Phase 3: document chunks and source evidence.
//
// Backend seed data is canonical for evidence starting in Phase 3. To avoid
// drift, the frontend does not duplicate the full chunk set. When the backend
// is unavailable these functions return empty results and the UI shows an
// evidence status note rather than stale data.

export type ChunkItem = {
  chunkId: string;
  documentId: string;
  documentType: string;
  fileName: string;
  pageNumber: number | null;
  sectionHeading: string | null;
  chunkIndex: number;
  content: string;
  keywords: string[];
  relatedChecklistItems: string[];
  relatedFindings: string[];
};

export type EvidenceItem = {
  chunkId: string | null;
  documentId: string;
  fileName: string;
  documentType: string;
  pageNumber: number | null;
  sectionHeading: string | null;
  excerpt: string;
  relevanceReason: string;
  score: number;
  evidenceRole: string | null;
  safetyNote: string;
};

type ApiChunk = {
  chunk_id: string;
  document_id: string;
  document_type: string;
  file_name: string;
  page_number: number | null;
  section_heading: string | null;
  chunk_index: number;
  content: string;
  keywords: string[];
  related_checklist_items: string[];
  related_findings: string[];
};

type ApiEvidence = {
  chunk_id: string | null;
  document_id: string;
  file_name: string;
  document_type: string;
  page_number: number | null;
  section_heading: string | null;
  excerpt: string;
  relevance_reason: string;
  score: number;
  evidence_role: string | null;
  safety_note: string;
};

function mapChunk(c: ApiChunk): ChunkItem {
  return {
    chunkId: c.chunk_id,
    documentId: c.document_id,
    documentType: c.document_type,
    fileName: c.file_name,
    pageNumber: c.page_number,
    sectionHeading: c.section_heading,
    chunkIndex: c.chunk_index,
    content: c.content,
    keywords: c.keywords,
    relatedChecklistItems: c.related_checklist_items,
    relatedFindings: c.related_findings,
  };
}

function mapEvidence(e: ApiEvidence): EvidenceItem {
  return {
    chunkId: e.chunk_id,
    documentId: e.document_id,
    fileName: e.file_name,
    documentType: e.document_type,
    pageNumber: e.page_number,
    sectionHeading: e.section_heading,
    excerpt: e.excerpt,
    relevanceReason: e.relevance_reason,
    score: e.score,
    evidenceRole: e.evidence_role,
    safetyNote: e.safety_note,
  };
}

export async function getProjectChunks(): Promise<ChunkItem[]> {
  const data = await safeFetch<ApiChunk[]>(
    `/api/v1/projects/${PROJECT_ID}/chunks`,
  );
  return data ? data.map(mapChunk) : [];
}

export async function getFindingEvidence(
  findingId: string,
): Promise<EvidenceItem[]> {
  const data = await safeFetch<ApiEvidence[]>(
    `/api/v1/projects/${PROJECT_ID}/findings/${findingId}/evidence`,
  );
  return data ? data.map(mapEvidence) : [];
}

export async function getChecklistEvidence(
  checklistItemId: string,
): Promise<EvidenceItem[]> {
  const data = await safeFetch<ApiEvidence[]>(
    `/api/v1/projects/${PROJECT_ID}/checklist/${checklistItemId}/evidence`,
  );
  return data ? data.map(mapEvidence) : [];
}

export async function searchEvidence(query: string): Promise<EvidenceItem[]> {
  const data = await safeFetch<ApiEvidence[]>(
    `/api/v1/projects/${PROJECT_ID}/search?query=${encodeURIComponent(query)}`,
  );
  return data ? data.map(mapEvidence) : [];
}

// Fetch evidence for many findings in parallel, keyed by finding id.
export async function getEvidenceByFinding(
  findingIds: string[],
): Promise<Record<string, EvidenceItem[]>> {
  const entries = await Promise.all(
    findingIds.map(
      async (id) => [id, await getFindingEvidence(id)] as const,
    ),
  );
  return Object.fromEntries(entries);
}

// Group seeded chunks by document id for the documents page.
export async function getChunksByDocument(): Promise<Record<string, ChunkItem[]>> {
  const chunks = await getProjectChunks();
  const grouped: Record<string, ChunkItem[]> = {};
  for (const chunk of chunks) {
    (grouped[chunk.documentId] ??= []).push(chunk);
  }
  return grouped;
}

// Group chunks by checklist item for the checklist page evidence panels.
export async function getChunksByChecklistItem(): Promise<
  Record<string, ChunkItem[]>
> {
  const chunks = await getProjectChunks();
  const grouped: Record<string, ChunkItem[]> = {};
  for (const chunk of chunks) {
    for (const itemId of chunk.relatedChecklistItems) {
      (grouped[itemId] ??= []).push(chunk);
    }
  }
  return grouped;
}

// Phase 4: AI Review Assistant.
//
// Draft findings are backend-canonical. The AI review page reads and triggers
// runs against the backend. When the backend is unavailable these functions
// return null or empty results and the UI shows a status note.

export type ProviderModeInfo = {
  provider: string;
  mode: string;
  modelName: string;
  liveCallsEnabled: boolean;
  detail: string;
};

export type AiReviewRun = {
  reviewRunId: string;
  projectId: string;
  runType: string;
  provider: string;
  modelName: string;
  status: string;
  promptVersion: string;
  checklistItemCount: number;
  draftFindingsCreated: number;
  safetyFailures: number;
  startedAt: string;
  completedAt: string | null;
};

export type AiDraftFinding = {
  draftFindingId: string;
  reviewRunId: string;
  projectId: string;
  checklistItemId: string;
  findingType: string;
  title: string;
  summary: string;
  riskLevel: string;
  confidence: number;
  status: string;
  recommendedHumanAction: string;
  sourceChunkIds: string[];
  validationStatus: string;
  safetyCheckStatus: string;
  validationErrors: string[];
};

type ApiRun = {
  review_run_id: string;
  project_id: string;
  run_type: string;
  provider: string;
  model_name: string;
  status: string;
  prompt_version: string;
  checklist_item_count: number;
  draft_findings_created: number;
  safety_failures: number;
  started_at: string;
  completed_at: string | null;
};

type ApiDraft = {
  draft_finding_id: string;
  review_run_id: string;
  project_id: string;
  checklist_item_id: string;
  finding_type: string;
  title: string;
  summary: string;
  risk_level: string;
  confidence: number;
  status: string;
  recommended_human_action: string;
  source_chunk_ids: string[];
  validation_status: string;
  safety_check_status: string;
  validation_errors: string[];
};

function mapRun(r: ApiRun): AiReviewRun {
  return {
    reviewRunId: r.review_run_id,
    projectId: r.project_id,
    runType: r.run_type,
    provider: r.provider,
    modelName: r.model_name,
    status: r.status,
    promptVersion: r.prompt_version,
    checklistItemCount: r.checklist_item_count,
    draftFindingsCreated: r.draft_findings_created,
    safetyFailures: r.safety_failures,
    startedAt: r.started_at,
    completedAt: r.completed_at,
  };
}

function mapDraft(d: ApiDraft): AiDraftFinding {
  return {
    draftFindingId: d.draft_finding_id,
    reviewRunId: d.review_run_id,
    projectId: d.project_id,
    checklistItemId: d.checklist_item_id,
    findingType: d.finding_type,
    title: d.title,
    summary: d.summary,
    riskLevel: d.risk_level,
    confidence: d.confidence,
    status: d.status,
    recommendedHumanAction: d.recommended_human_action,
    sourceChunkIds: d.source_chunk_ids,
    validationStatus: d.validation_status,
    safetyCheckStatus: d.safety_check_status,
    validationErrors: d.validation_errors,
  };
}

export async function getProviderMode(): Promise<ProviderModeInfo | null> {
  const data = await safeFetch<{
    provider: string;
    mode: string;
    model_name: string;
    live_calls_enabled: boolean;
    detail: string;
  }>(`/api/v1/projects/${PROJECT_ID}/ai-provider-mode`);
  if (!data) return null;
  return {
    provider: data.provider,
    mode: data.mode,
    modelName: data.model_name,
    liveCallsEnabled: data.live_calls_enabled,
    detail: data.detail,
  };
}

export async function getAiReviewRuns(): Promise<AiReviewRun[]> {
  const data = await safeFetch<ApiRun[]>(
    `/api/v1/projects/${PROJECT_ID}/ai-review-runs`,
  );
  return data ? data.map(mapRun) : [];
}

export async function startAiReviewRun(): Promise<AiReviewRun | null> {
  try {
    const res = await fetch(
      `${API_BASE_URL}/api/v1/projects/${PROJECT_ID}/ai-review-runs`,
      { method: "POST", cache: "no-store" },
    );
    if (!res.ok) return null;
    return mapRun((await res.json()) as ApiRun);
  } catch {
    return null;
  }
}

export async function getRunDraftFindings(
  reviewRunId: string,
): Promise<AiDraftFinding[]> {
  const data = await safeFetch<ApiDraft[]>(
    `/api/v1/ai-review-runs/${reviewRunId}/draft-findings`,
  );
  return data ? data.map(mapDraft) : [];
}

export async function getProjectDraftFindings(): Promise<AiDraftFinding[]> {
  const data = await safeFetch<ApiDraft[]>(
    `/api/v1/projects/${PROJECT_ID}/draft-findings`,
  );
  return data ? data.map(mapDraft) : [];
}

// Phase 5: human review queue, review actions, and evaluation scoring.
//
// Review actions mutate backend state, so they are never faked in
// frontend-only mode. When the backend is unreachable, mutating calls return a
// clear backend-required result instead of pretending an action succeeded.

export type HumanReviewAction = {
  reviewActionId: string;
  draftFindingId: string;
  projectId: string;
  reviewRunId: string;
  reviewerName: string;
  action: string;
  reviewerNote: string;
  editedTitle: string | null;
  editedSummary: string | null;
  editedRecommendedAction: string | null;
  previousStatus: string;
  newStatus: string;
  createdAt: string;
};

export type ReviewActionInput = {
  action: string;
  reviewerName: string;
  reviewerNote: string;
  editedTitle?: string;
  editedSummary?: string;
  editedRecommendedAction?: string;
};

export type ReviewActionResult = {
  ok: boolean;
  status: number;
  backendReachable: boolean;
  action?: HumanReviewAction;
  draftFinding?: AiDraftFinding;
  error?: string;
};

export type EvaluationMatch = {
  evaluationMatchId: string;
  evaluationResultId: string;
  expectedFindingId: string | null;
  draftFindingId: string | null;
  matchType: string;
  matchConfidence: number;
  matchedOn: string | null;
  notes: string | null;
};

export type AiEvaluationResult = {
  evaluationResultId: string;
  projectId: string;
  reviewRunId: string;
  expectedFindingsCount: number;
  draftFindingsCount: number;
  matchedFindingsCount: number;
  unmatchedExpectedCount: number;
  extraDraftFindingsCount: number;
  citationValidityRate: number;
  humanReviewRequiredRate: number;
  prohibitedWordCount: number;
  validationFailureCount: number;
  safetyFailureCount: number;
  recall: number;
  precision: number;
  overallScore: number;
  createdAt: string;
  matches: EvaluationMatch[];
};

export type EvaluationRunResult = {
  ok: boolean;
  status: number;
  backendReachable: boolean;
  result?: AiEvaluationResult;
  error?: string;
};

type ApiReviewAction = {
  review_action_id: string;
  draft_finding_id: string;
  project_id: string;
  review_run_id: string;
  reviewer_name: string;
  action: string;
  reviewer_note: string;
  edited_title: string | null;
  edited_summary: string | null;
  edited_recommended_action: string | null;
  previous_status: string;
  new_status: string;
  created_at: string;
};

type ApiEvaluationMatch = {
  evaluation_match_id: string;
  evaluation_result_id: string;
  expected_finding_id: string | null;
  draft_finding_id: string | null;
  match_type: string;
  match_confidence: number;
  matched_on: string | null;
  notes: string | null;
};

type ApiEvaluationResult = {
  evaluation_result_id: string;
  project_id: string;
  review_run_id: string;
  expected_findings_count: number;
  draft_findings_count: number;
  matched_findings_count: number;
  unmatched_expected_count: number;
  extra_draft_findings_count: number;
  citation_validity_rate: number;
  human_review_required_rate: number;
  prohibited_word_count: number;
  validation_failure_count: number;
  safety_failure_count: number;
  recall: number;
  precision: number;
  overall_score: number;
  created_at: string;
  matches?: ApiEvaluationMatch[];
};

function mapReviewAction(a: ApiReviewAction): HumanReviewAction {
  return {
    reviewActionId: a.review_action_id,
    draftFindingId: a.draft_finding_id,
    projectId: a.project_id,
    reviewRunId: a.review_run_id,
    reviewerName: a.reviewer_name,
    action: a.action,
    reviewerNote: a.reviewer_note,
    editedTitle: a.edited_title,
    editedSummary: a.edited_summary,
    editedRecommendedAction: a.edited_recommended_action,
    previousStatus: a.previous_status,
    newStatus: a.new_status,
    createdAt: a.created_at,
  };
}

function mapEvaluationMatch(m: ApiEvaluationMatch): EvaluationMatch {
  return {
    evaluationMatchId: m.evaluation_match_id,
    evaluationResultId: m.evaluation_result_id,
    expectedFindingId: m.expected_finding_id,
    draftFindingId: m.draft_finding_id,
    matchType: m.match_type,
    matchConfidence: m.match_confidence,
    matchedOn: m.matched_on,
    notes: m.notes,
  };
}

function mapEvaluationResult(r: ApiEvaluationResult): AiEvaluationResult {
  return {
    evaluationResultId: r.evaluation_result_id,
    projectId: r.project_id,
    reviewRunId: r.review_run_id,
    expectedFindingsCount: r.expected_findings_count,
    draftFindingsCount: r.draft_findings_count,
    matchedFindingsCount: r.matched_findings_count,
    unmatchedExpectedCount: r.unmatched_expected_count,
    extraDraftFindingsCount: r.extra_draft_findings_count,
    citationValidityRate: r.citation_validity_rate,
    humanReviewRequiredRate: r.human_review_required_rate,
    prohibitedWordCount: r.prohibited_word_count,
    validationFailureCount: r.validation_failure_count,
    safetyFailureCount: r.safety_failure_count,
    recall: r.recall,
    precision: r.precision,
    overallScore: r.overall_score,
    createdAt: r.created_at,
    matches: (r.matches ?? []).map(mapEvaluationMatch),
  };
}

export async function getHumanReviewQueue(): Promise<AiDraftFinding[]> {
  const data = await safeFetch<ApiDraft[]>(
    `/api/v1/projects/${PROJECT_ID}/human-review-queue`,
  );
  return data ? data.map(mapDraft) : [];
}

export async function getDraftReviewActions(
  draftFindingId: string,
): Promise<HumanReviewAction[]> {
  const data = await safeFetch<ApiReviewAction[]>(
    `/api/v1/draft-findings/${draftFindingId}/review-actions`,
  );
  return data ? data.map(mapReviewAction) : [];
}

export async function getProjectReviewActions(): Promise<HumanReviewAction[]> {
  const data = await safeFetch<ApiReviewAction[]>(
    `/api/v1/projects/${PROJECT_ID}/review-actions`,
  );
  return data ? data.map(mapReviewAction) : [];
}

export async function submitReviewAction(
  draftFindingId: string,
  input: ReviewActionInput,
): Promise<ReviewActionResult> {
  const payload: Record<string, string> = {
    action: input.action,
    reviewer_name: input.reviewerName,
    reviewer_note: input.reviewerNote,
  };
  if (input.editedTitle) payload.edited_title = input.editedTitle;
  if (input.editedSummary) payload.edited_summary = input.editedSummary;
  if (input.editedRecommendedAction)
    payload.edited_recommended_action = input.editedRecommendedAction;

  try {
    const res = await fetch(
      `${API_BASE_URL}/api/v1/draft-findings/${draftFindingId}/review-actions`,
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
        cache: "no-store",
      },
    );
    if (!res.ok) {
      let detail = `Request failed (${res.status}).`;
      try {
        const body = (await res.json()) as { detail?: string };
        if (body.detail) detail = body.detail;
      } catch {
        // Non-JSON error body. Keep the generic message.
      }
      return { ok: false, status: res.status, backendReachable: true, error: detail };
    }
    const body = (await res.json()) as {
      action: ApiReviewAction;
      draft_finding: ApiDraft;
    };
    return {
      ok: true,
      status: res.status,
      backendReachable: true,
      action: mapReviewAction(body.action),
      draftFinding: mapDraft(body.draft_finding),
    };
  } catch {
    return {
      ok: false,
      status: 0,
      backendReachable: false,
      error:
        "The backend is not reachable. Start the API to record review actions. Review actions are never simulated in the browser.",
    };
  }
}

export async function runEvaluation(
  reviewRunId: string,
): Promise<EvaluationRunResult> {
  try {
    const res = await fetch(
      `${API_BASE_URL}/api/v1/ai-review-runs/${reviewRunId}/evaluate`,
      { method: "POST", cache: "no-store" },
    );
    if (!res.ok) {
      let detail = `Request failed (${res.status}).`;
      try {
        const body = (await res.json()) as { detail?: string };
        if (body.detail) detail = body.detail;
      } catch {
        // Keep generic message.
      }
      return { ok: false, status: res.status, backendReachable: true, error: detail };
    }
    return {
      ok: true,
      status: res.status,
      backendReachable: true,
      result: mapEvaluationResult((await res.json()) as ApiEvaluationResult),
    };
  } catch {
    return {
      ok: false,
      status: 0,
      backendReachable: false,
      error:
        "The backend is not reachable. Start the API to run evaluation scoring.",
    };
  }
}

export async function getRunEvaluation(
  reviewRunId: string,
): Promise<AiEvaluationResult | null> {
  const data = await safeFetch<ApiEvaluationResult>(
    `/api/v1/ai-review-runs/${reviewRunId}/evaluation`,
  );
  return data ? mapEvaluationResult(data) : null;
}

export async function getProjectEvaluationResults(): Promise<
  AiEvaluationResult[]
> {
  const data = await safeFetch<ApiEvaluationResult[]>(
    `/api/v1/projects/${PROJECT_ID}/ai-evaluation-results`,
  );
  return data ? data.map(mapEvaluationResult) : [];
}

export async function getEvaluationResult(
  evaluationResultId: string,
): Promise<AiEvaluationResult | null> {
  const data = await safeFetch<ApiEvaluationResult>(
    `/api/v1/ai-evaluation-results/${evaluationResultId}`,
  );
  return data ? mapEvaluationResult(data) : null;
}

// Phase 6: plan sheets, CAD-aware metadata, plan references, and plan
// consistency findings.
//
// Phase 6 data is backend-canonical. The frontend does not duplicate the plan
// set or CAD metadata. When the backend is unavailable these functions return
// empty results (or a backend-required result for the check mutation) and the
// UI shows a status note rather than stale or simulated data.

export type PlanSheet = {
  sheetId: string;
  projectId: string;
  sheetNumber: string;
  sheetTitle: string;
  discipline: string;
  revision: string;
  revisionDate: string | null;
  status: string;
  fileName: string | null;
  sheetPurpose: string;
  relatedDocuments: string[];
  relatedChecklistItems: string[];
  relatedFindings: string[];
};

export type PlanSheetSummary = {
  projectId: string;
  totalSheets: number;
  presentSheets: number;
  missingOrReferencedNotIncluded: number;
  needsReviewerConfirmation: number;
  sheetsWithRelatedFindings: number;
  cadMetadataRecords: number;
  sheetsByDiscipline: Record<string, number>;
  missingSheetIds: string[];
};

export type CadMetadata = {
  cadMetadataId: string;
  projectId: string;
  sheetId: string | null;
  sourceType: string;
  entityType: string;
  entityLabel: string;
  layerName: string | null;
  discipline: string;
  relatedDocumentId: string | null;
  relatedChecklistItemId: string | null;
  relatedFindingId: string | null;
  notes: string | null;
};

export type PlanReference = {
  planReferenceId: string;
  projectId: string;
  sourceType: string;
  sourceId: string;
  targetType: string;
  targetId: string;
  referenceLabel: string;
  referenceContext: string;
  consistencyStatus: string;
  reviewNote: string | null;
};

export type PlanConsistencyFinding = {
  planFindingId: string;
  projectId: string;
  findingType: string;
  title: string;
  summary: string;
  riskLevel: string;
  status: string;
  relatedSheetIds: string[];
  relatedDocumentIds: string[];
  relatedChecklistItems: string[];
  relatedCadMetadataIds: string[];
  recommendedHumanAction: string;
};

export type PlanConsistencySummary = {
  projectId: string;
  totalSheets: number;
  missingSheetCount: number;
  cadMetadataRecords: number;
  totalPlanReferences: number;
  inconsistentReferences: number;
  planConsistencyFindings: number;
  conflictingLabelCount: number;
  missingReferencedSheetCount: number;
  missingPlanReferenceCount: number;
  unclearRevisionCount: number;
  requiresHumanReviewCount: number;
  findingsRequiringHumanReview: number;
};

export type PlanConsistencyCheckResult = {
  ok: boolean;
  status: number;
  backendReachable: boolean;
  summary?: PlanConsistencySummary;
  error?: string;
};

type ApiPlanSheet = {
  sheet_id: string;
  project_id: string;
  sheet_number: string;
  sheet_title: string;
  discipline: string;
  revision: string;
  revision_date: string | null;
  status: string;
  file_name: string | null;
  sheet_purpose: string;
  related_documents: string[];
  related_checklist_items: string[];
  related_findings: string[];
};

type ApiPlanSheetSummary = {
  project_id: string;
  total_sheets: number;
  present_sheets: number;
  missing_or_referenced_not_included: number;
  needs_reviewer_confirmation: number;
  sheets_with_related_findings: number;
  cad_metadata_records: number;
  sheets_by_discipline: Record<string, number>;
  missing_sheet_ids: string[];
};

type ApiCadMetadata = {
  cad_metadata_id: string;
  project_id: string;
  sheet_id: string | null;
  source_type: string;
  entity_type: string;
  entity_label: string;
  layer_name: string | null;
  discipline: string;
  related_document_id: string | null;
  related_checklist_item_id: string | null;
  related_finding_id: string | null;
  notes: string | null;
};

type ApiPlanReference = {
  plan_reference_id: string;
  project_id: string;
  source_type: string;
  source_id: string;
  target_type: string;
  target_id: string;
  reference_label: string;
  reference_context: string;
  consistency_status: string;
  review_note: string | null;
};

type ApiPlanConsistencyFinding = {
  plan_finding_id: string;
  project_id: string;
  finding_type: string;
  title: string;
  summary: string;
  risk_level: string;
  status: string;
  related_sheet_ids: string[];
  related_document_ids: string[];
  related_checklist_items: string[];
  related_cad_metadata_ids: string[];
  recommended_human_action: string;
};

type ApiPlanConsistencySummary = {
  project_id: string;
  total_sheets: number;
  missing_sheet_count: number;
  cad_metadata_records: number;
  total_plan_references: number;
  inconsistent_references: number;
  plan_consistency_findings: number;
  conflicting_label_count: number;
  missing_referenced_sheet_count: number;
  missing_plan_reference_count: number;
  unclear_revision_count: number;
  requires_human_review_count: number;
  findings_requiring_human_review: number;
};

function mapPlanSheet(s: ApiPlanSheet): PlanSheet {
  return {
    sheetId: s.sheet_id,
    projectId: s.project_id,
    sheetNumber: s.sheet_number,
    sheetTitle: s.sheet_title,
    discipline: s.discipline,
    revision: s.revision,
    revisionDate: s.revision_date,
    status: s.status,
    fileName: s.file_name,
    sheetPurpose: s.sheet_purpose,
    relatedDocuments: s.related_documents,
    relatedChecklistItems: s.related_checklist_items,
    relatedFindings: s.related_findings,
  };
}

function mapPlanSheetSummary(s: ApiPlanSheetSummary): PlanSheetSummary {
  return {
    projectId: s.project_id,
    totalSheets: s.total_sheets,
    presentSheets: s.present_sheets,
    missingOrReferencedNotIncluded: s.missing_or_referenced_not_included,
    needsReviewerConfirmation: s.needs_reviewer_confirmation,
    sheetsWithRelatedFindings: s.sheets_with_related_findings,
    cadMetadataRecords: s.cad_metadata_records,
    sheetsByDiscipline: s.sheets_by_discipline,
    missingSheetIds: s.missing_sheet_ids,
  };
}

function mapCadMetadata(c: ApiCadMetadata): CadMetadata {
  return {
    cadMetadataId: c.cad_metadata_id,
    projectId: c.project_id,
    sheetId: c.sheet_id,
    sourceType: c.source_type,
    entityType: c.entity_type,
    entityLabel: c.entity_label,
    layerName: c.layer_name,
    discipline: c.discipline,
    relatedDocumentId: c.related_document_id,
    relatedChecklistItemId: c.related_checklist_item_id,
    relatedFindingId: c.related_finding_id,
    notes: c.notes,
  };
}

function mapPlanReference(r: ApiPlanReference): PlanReference {
  return {
    planReferenceId: r.plan_reference_id,
    projectId: r.project_id,
    sourceType: r.source_type,
    sourceId: r.source_id,
    targetType: r.target_type,
    targetId: r.target_id,
    referenceLabel: r.reference_label,
    referenceContext: r.reference_context,
    consistencyStatus: r.consistency_status,
    reviewNote: r.review_note,
  };
}

function mapPlanConsistencyFinding(
  f: ApiPlanConsistencyFinding,
): PlanConsistencyFinding {
  return {
    planFindingId: f.plan_finding_id,
    projectId: f.project_id,
    findingType: f.finding_type,
    title: f.title,
    summary: f.summary,
    riskLevel: f.risk_level,
    status: f.status,
    relatedSheetIds: f.related_sheet_ids,
    relatedDocumentIds: f.related_document_ids,
    relatedChecklistItems: f.related_checklist_items,
    relatedCadMetadataIds: f.related_cad_metadata_ids,
    recommendedHumanAction: f.recommended_human_action,
  };
}

function mapPlanConsistencySummary(
  s: ApiPlanConsistencySummary,
): PlanConsistencySummary {
  return {
    projectId: s.project_id,
    totalSheets: s.total_sheets,
    missingSheetCount: s.missing_sheet_count,
    cadMetadataRecords: s.cad_metadata_records,
    totalPlanReferences: s.total_plan_references,
    inconsistentReferences: s.inconsistent_references,
    planConsistencyFindings: s.plan_consistency_findings,
    conflictingLabelCount: s.conflicting_label_count,
    missingReferencedSheetCount: s.missing_referenced_sheet_count,
    missingPlanReferenceCount: s.missing_plan_reference_count,
    unclearRevisionCount: s.unclear_revision_count,
    requiresHumanReviewCount: s.requires_human_review_count,
    findingsRequiringHumanReview: s.findings_requiring_human_review,
  };
}

export async function getPlanSheets(): Promise<PlanSheet[]> {
  const data = await safeFetch<ApiPlanSheet[]>(
    `/api/v1/projects/${PROJECT_ID}/plan-sheets`,
  );
  return data ? data.map(mapPlanSheet) : [];
}

export async function getPlanSheetSummary(): Promise<PlanSheetSummary | null> {
  const data = await safeFetch<ApiPlanSheetSummary>(
    `/api/v1/projects/${PROJECT_ID}/plan-sheets/summary`,
  );
  return data ? mapPlanSheetSummary(data) : null;
}

export async function getCadMetadata(
  entityType?: string,
): Promise<CadMetadata[]> {
  const query = entityType
    ? `?entity_type=${encodeURIComponent(entityType)}`
    : "";
  const data = await safeFetch<ApiCadMetadata[]>(
    `/api/v1/projects/${PROJECT_ID}/cad-metadata${query}`,
  );
  return data ? data.map(mapCadMetadata) : [];
}

export async function getCadMetadataBySheet(
  sheetId: string,
): Promise<CadMetadata[]> {
  const data = await safeFetch<ApiCadMetadata[]>(
    `/api/v1/plan-sheets/${sheetId}/cad-metadata`,
  );
  return data ? data.map(mapCadMetadata) : [];
}

export async function getPlanReferences(): Promise<PlanReference[]> {
  const data = await safeFetch<ApiPlanReference[]>(
    `/api/v1/projects/${PROJECT_ID}/plan-references`,
  );
  return data ? data.map(mapPlanReference) : [];
}

export async function getPlanInconsistencies(): Promise<PlanReference[]> {
  const data = await safeFetch<ApiPlanReference[]>(
    `/api/v1/projects/${PROJECT_ID}/plan-references/inconsistencies`,
  );
  return data ? data.map(mapPlanReference) : [];
}

export async function getPlanConsistencyFindings(): Promise<
  PlanConsistencyFinding[]
> {
  const data = await safeFetch<ApiPlanConsistencyFinding[]>(
    `/api/v1/projects/${PROJECT_ID}/plan-consistency-findings`,
  );
  return data ? data.map(mapPlanConsistencyFinding) : [];
}

export async function getPlanConsistencySummary(): Promise<PlanConsistencySummary | null> {
  const data = await safeFetch<ApiPlanConsistencySummary>(
    `/api/v1/projects/${PROJECT_ID}/plan-consistency-summary`,
  );
  return data ? mapPlanConsistencySummary(data) : null;
}

export async function runPlanConsistencyCheck(): Promise<PlanConsistencyCheckResult> {
  try {
    const res = await fetch(
      `${API_BASE_URL}/api/v1/projects/${PROJECT_ID}/plan-consistency-check`,
      { method: "POST", cache: "no-store" },
    );
    if (!res.ok) {
      let detail = `Request failed (${res.status}).`;
      try {
        const body = (await res.json()) as { detail?: string };
        if (body.detail) detail = body.detail;
      } catch {
        // Keep generic message.
      }
      return { ok: false, status: res.status, backendReachable: true, error: detail };
    }
    return {
      ok: true,
      status: res.status,
      backendReachable: true,
      summary: mapPlanConsistencySummary(
        (await res.json()) as ApiPlanConsistencySummary,
      ),
    };
  } catch {
    return {
      ok: false,
      status: 0,
      backendReachable: false,
      error:
        "The backend is not reachable. Start the API to run the plan consistency check. Plan consistency findings are not simulated in the browser.",
    };
  }
}

export { projectMetrics };
