import { API_BASE_URL, PROJECT_ID, safeFetch } from "./client";

// Phase 11: real CAD (DXF) intake and parsing.
//
// Phase 11 data is backend-canonical. The frontend does not simulate parsed CAD
// data. Read calls return null or empty results when the backend is
// unavailable, and the mutating calls return a clear backend-required result.

export type CadFileUpload = {
  cadFileId: string;
  projectId: string;
  fileName: string;
  fileType: string;
  fileSizeBytes: number;
  storagePath: string;
  uploadStatus: string;
  uploadedBy: string;
  limitationsNote: string;
  originalFileName: string | null;
  storedFileName: string | null;
  contentType: string | null;
  uploadSource: string;
  validationStatus: string | null;
  validationMessage: string | null;
  maxFileSizeBytes: number;
  parseRequestedAt: string | null;
  parseCompletedAt: string | null;
  createdAt: string;
};

export type CadParseRun = {
  parseRunId: string;
  cadFileId: string;
  projectId: string;
  parserName: string;
  parserVersion: string;
  status: string;
  startedAt: string;
  completedAt: string | null;
  entityCount: number;
  layerCount: number;
  blockCount: number;
  textCount: number;
  warningCount: number;
  errorMessage: string | null;
  limitationsNote: string;
};

export type CadLayerExtract = {
  layerExtractId: string;
  parseRunId: string;
  cadFileId: string;
  projectId: string;
  layerName: string;
  entityCount: number;
  hasText: boolean;
  hasGeometry: boolean;
  reviewCategory: string;
  requiresHumanReview: boolean;
};

export type CadEntityExtract = {
  entityExtractId: string;
  parseRunId: string;
  cadFileId: string;
  projectId: string;
  entityType: string;
  layerName: string | null;
  blockName: string | null;
  handle: string | null;
  textValue: string | null;
  xMin: number | null;
  yMin: number | null;
  xMax: number | null;
  yMax: number | null;
  reviewCategory: string;
  requiresHumanReview: boolean;
};

export type CadBlockExtract = {
  blockExtractId: string;
  parseRunId: string;
  cadFileId: string;
  projectId: string;
  blockName: string;
  insertCount: number;
  layerNames: string[];
  textValues: string[];
  reviewCategory: string;
  requiresHumanReview: boolean;
};

export type CadTextExtract = {
  textExtractId: string;
  parseRunId: string;
  cadFileId: string;
  projectId: string;
  textValue: string;
  normalizedText: string;
  entityType: string;
  layerName: string | null;
  blockName: string | null;
  handle: string | null;
  x: number | null;
  y: number | null;
  reviewCategory: string;
  referenceType: string;
  requiresHumanReview: boolean;
};

export type CadReferenceCandidate = {
  candidateId: string;
  parseRunId: string;
  cadFileId: string;
  projectId: string;
  referenceText: string;
  normalizedReference: string;
  referenceType: string;
  sourceEntityId: string | null;
  sourceTextId: string | null;
  matchedPlanSheetId: string | null;
  matchedPlanReferenceId: string | null;
  confidenceLabel: string;
  matchReason: string;
  requiresHumanReview: boolean;
};

export type CadReviewFinding = {
  cadReviewFindingId: string;
  parseRunId: string;
  cadFileId: string;
  projectId: string;
  findingType: string;
  title: string;
  description: string;
  severity: string;
  sourceReferenceCandidateId: string | null;
  sourceLayerExtractId: string | null;
  sourceTextExtractId: string | null;
  linkedPlanSheetId: string | null;
  linkedWorkflowItemId: string | null;
  promotedToWorkflow: boolean;
  promotedWorkflowItemId: string | null;
  status: string;
  requiresHumanReview: boolean;
  createdAt: string;
};

export type CadParseSummary = {
  parseRunId: string;
  cadFileId: string;
  projectId: string;
  status: string;
  entityCount: number;
  layerCount: number;
  blockCount: number;
  textCount: number;
  warningCount: number;
  referenceCandidateCount: number;
  findingCount: number;
  layersByCategory: Record<string, number>;
  referencesByType: Record<string, number>;
  referencesByConfidence: Record<string, number>;
  findingsByType: Record<string, number>;
  limitationsNote: string;
};

export type CadPlanSheetComparisonRow = {
  candidateId: string;
  referenceText: string;
  normalizedReference: string;
  referenceType: string;
  matchedPlanSheetId: string | null;
  matchedSheetNumber: string | null;
  confidenceLabel: string;
  matchReason: string;
};

export type CadPlanSheetComparison = {
  parseRunId: string;
  projectId: string;
  totalCandidates: number;
  matchedCount: number;
  unmatchedCount: number;
  rows: CadPlanSheetComparisonRow[];
  findings: CadReviewFinding[];
  note: string;
};

export type CadFileReviewContext = {
  cadFile: CadFileUpload;
  parseRun: CadParseRun | null;
  summary: CadParseSummary | null;
  layers: CadLayerExtract[];
  referenceCandidates: CadReferenceCandidate[];
  findings: CadReviewFinding[];
  note: string;
};

export type CadWorkflowItemsResult = {
  ok: boolean;
  backendReachable: boolean;
  createdCount?: number;
  workflowItemIds?: string[];
  note?: string;
  error?: string;
};

type ApiCadFile = {
  cad_file_id: string;
  project_id: string;
  file_name: string;
  file_type: string;
  file_size_bytes: number;
  storage_path: string;
  upload_status: string;
  uploaded_by: string;
  limitations_note: string;
  original_file_name: string | null;
  stored_file_name: string | null;
  content_type: string | null;
  upload_source: string;
  validation_status: string | null;
  validation_message: string | null;
  max_file_size_bytes: number;
  parse_requested_at: string | null;
  parse_completed_at: string | null;
  created_at: string;
};

type ApiParseRun = {
  parse_run_id: string;
  cad_file_id: string;
  project_id: string;
  parser_name: string;
  parser_version: string;
  status: string;
  started_at: string;
  completed_at: string | null;
  entity_count: number;
  layer_count: number;
  block_count: number;
  text_count: number;
  warning_count: number;
  error_message: string | null;
  limitations_note: string;
};

type ApiLayer = {
  layer_extract_id: string;
  parse_run_id: string;
  cad_file_id: string;
  project_id: string;
  layer_name: string;
  entity_count: number;
  has_text: boolean;
  has_geometry: boolean;
  review_category: string;
  requires_human_review: boolean;
};

type ApiEntity = {
  entity_extract_id: string;
  parse_run_id: string;
  cad_file_id: string;
  project_id: string;
  entity_type: string;
  layer_name: string | null;
  block_name: string | null;
  handle: string | null;
  text_value: string | null;
  x_min: number | null;
  y_min: number | null;
  x_max: number | null;
  y_max: number | null;
  review_category: string;
  requires_human_review: boolean;
};

type ApiBlock = {
  block_extract_id: string;
  parse_run_id: string;
  cad_file_id: string;
  project_id: string;
  block_name: string;
  insert_count: number;
  layer_names: string[];
  text_values: string[];
  review_category: string;
  requires_human_review: boolean;
};

type ApiText = {
  text_extract_id: string;
  parse_run_id: string;
  cad_file_id: string;
  project_id: string;
  text_value: string;
  normalized_text: string;
  entity_type: string;
  layer_name: string | null;
  block_name: string | null;
  handle: string | null;
  x: number | null;
  y: number | null;
  review_category: string;
  reference_type: string;
  requires_human_review: boolean;
};

type ApiCandidate = {
  candidate_id: string;
  parse_run_id: string;
  cad_file_id: string;
  project_id: string;
  reference_text: string;
  normalized_reference: string;
  reference_type: string;
  source_entity_id: string | null;
  source_text_id: string | null;
  matched_plan_sheet_id: string | null;
  matched_plan_reference_id: string | null;
  confidence_label: string;
  match_reason: string;
  requires_human_review: boolean;
};

type ApiFinding = {
  cad_review_finding_id: string;
  parse_run_id: string;
  cad_file_id: string;
  project_id: string;
  finding_type: string;
  title: string;
  description: string;
  severity: string;
  source_reference_candidate_id: string | null;
  source_layer_extract_id: string | null;
  source_text_extract_id: string | null;
  linked_plan_sheet_id: string | null;
  linked_workflow_item_id: string | null;
  promoted_to_workflow: boolean;
  promoted_workflow_item_id: string | null;
  status: string;
  requires_human_review: boolean;
  created_at: string;
};

type ApiSummary = {
  parse_run_id: string;
  cad_file_id: string;
  project_id: string;
  status: string;
  entity_count: number;
  layer_count: number;
  block_count: number;
  text_count: number;
  warning_count: number;
  reference_candidate_count: number;
  finding_count: number;
  layers_by_category: Record<string, number>;
  references_by_type: Record<string, number>;
  references_by_confidence: Record<string, number>;
  findings_by_type: Record<string, number>;
  limitations_note: string;
};

function mapCadFile(f: ApiCadFile): CadFileUpload {
  return {
    cadFileId: f.cad_file_id,
    projectId: f.project_id,
    fileName: f.file_name,
    fileType: f.file_type,
    fileSizeBytes: f.file_size_bytes,
    storagePath: f.storage_path,
    uploadStatus: f.upload_status,
    uploadedBy: f.uploaded_by,
    limitationsNote: f.limitations_note,
    originalFileName: f.original_file_name ?? null,
    storedFileName: f.stored_file_name ?? null,
    contentType: f.content_type ?? null,
    uploadSource: f.upload_source ?? "sample",
    validationStatus: f.validation_status ?? null,
    validationMessage: f.validation_message ?? null,
    maxFileSizeBytes: f.max_file_size_bytes ?? 0,
    parseRequestedAt: f.parse_requested_at ?? null,
    parseCompletedAt: f.parse_completed_at ?? null,
    createdAt: f.created_at,
  };
}

function mapParseRun(r: ApiParseRun): CadParseRun {
  return {
    parseRunId: r.parse_run_id,
    cadFileId: r.cad_file_id,
    projectId: r.project_id,
    parserName: r.parser_name,
    parserVersion: r.parser_version,
    status: r.status,
    startedAt: r.started_at,
    completedAt: r.completed_at,
    entityCount: r.entity_count,
    layerCount: r.layer_count,
    blockCount: r.block_count,
    textCount: r.text_count,
    warningCount: r.warning_count,
    errorMessage: r.error_message,
    limitationsNote: r.limitations_note,
  };
}

function mapLayer(l: ApiLayer): CadLayerExtract {
  return {
    layerExtractId: l.layer_extract_id,
    parseRunId: l.parse_run_id,
    cadFileId: l.cad_file_id,
    projectId: l.project_id,
    layerName: l.layer_name,
    entityCount: l.entity_count,
    hasText: l.has_text,
    hasGeometry: l.has_geometry,
    reviewCategory: l.review_category,
    requiresHumanReview: l.requires_human_review,
  };
}

function mapEntity(e: ApiEntity): CadEntityExtract {
  return {
    entityExtractId: e.entity_extract_id,
    parseRunId: e.parse_run_id,
    cadFileId: e.cad_file_id,
    projectId: e.project_id,
    entityType: e.entity_type,
    layerName: e.layer_name,
    blockName: e.block_name,
    handle: e.handle,
    textValue: e.text_value,
    xMin: e.x_min,
    yMin: e.y_min,
    xMax: e.x_max,
    yMax: e.y_max,
    reviewCategory: e.review_category,
    requiresHumanReview: e.requires_human_review,
  };
}

function mapBlock(b: ApiBlock): CadBlockExtract {
  return {
    blockExtractId: b.block_extract_id,
    parseRunId: b.parse_run_id,
    cadFileId: b.cad_file_id,
    projectId: b.project_id,
    blockName: b.block_name,
    insertCount: b.insert_count,
    layerNames: b.layer_names ?? [],
    textValues: b.text_values ?? [],
    reviewCategory: b.review_category,
    requiresHumanReview: b.requires_human_review,
  };
}

function mapText(t: ApiText): CadTextExtract {
  return {
    textExtractId: t.text_extract_id,
    parseRunId: t.parse_run_id,
    cadFileId: t.cad_file_id,
    projectId: t.project_id,
    textValue: t.text_value,
    normalizedText: t.normalized_text,
    entityType: t.entity_type,
    layerName: t.layer_name,
    blockName: t.block_name,
    handle: t.handle,
    x: t.x,
    y: t.y,
    reviewCategory: t.review_category,
    referenceType: t.reference_type,
    requiresHumanReview: t.requires_human_review,
  };
}

function mapCandidate(c: ApiCandidate): CadReferenceCandidate {
  return {
    candidateId: c.candidate_id,
    parseRunId: c.parse_run_id,
    cadFileId: c.cad_file_id,
    projectId: c.project_id,
    referenceText: c.reference_text,
    normalizedReference: c.normalized_reference,
    referenceType: c.reference_type,
    sourceEntityId: c.source_entity_id,
    sourceTextId: c.source_text_id,
    matchedPlanSheetId: c.matched_plan_sheet_id,
    matchedPlanReferenceId: c.matched_plan_reference_id,
    confidenceLabel: c.confidence_label,
    matchReason: c.match_reason,
    requiresHumanReview: c.requires_human_review,
  };
}

function mapFinding(f: ApiFinding): CadReviewFinding {
  return {
    cadReviewFindingId: f.cad_review_finding_id,
    parseRunId: f.parse_run_id,
    cadFileId: f.cad_file_id,
    projectId: f.project_id,
    findingType: f.finding_type,
    title: f.title,
    description: f.description,
    severity: f.severity,
    sourceReferenceCandidateId: f.source_reference_candidate_id,
    sourceLayerExtractId: f.source_layer_extract_id,
    sourceTextExtractId: f.source_text_extract_id,
    linkedPlanSheetId: f.linked_plan_sheet_id,
    linkedWorkflowItemId: f.linked_workflow_item_id,
    promotedToWorkflow: f.promoted_to_workflow ?? false,
    promotedWorkflowItemId: f.promoted_workflow_item_id ?? null,
    status: f.status,
    requiresHumanReview: f.requires_human_review,
    createdAt: f.created_at,
  };
}

function mapSummary(s: ApiSummary): CadParseSummary {
  return {
    parseRunId: s.parse_run_id,
    cadFileId: s.cad_file_id,
    projectId: s.project_id,
    status: s.status,
    entityCount: s.entity_count,
    layerCount: s.layer_count,
    blockCount: s.block_count,
    textCount: s.text_count,
    warningCount: s.warning_count,
    referenceCandidateCount: s.reference_candidate_count,
    findingCount: s.finding_count,
    layersByCategory: s.layers_by_category,
    referencesByType: s.references_by_type,
    referencesByConfidence: s.references_by_confidence,
    findingsByType: s.findings_by_type,
    limitationsNote: s.limitations_note,
  };
}

export async function getCadFiles(projectId: string = PROJECT_ID): Promise<CadFileUpload[]> {
  const data = await safeFetch<ApiCadFile[]>(
    `/api/v1/projects/${projectId}/cad-files`,
  );
  return data ? data.map(mapCadFile) : [];
}

export async function getCadParseRuns(projectId: string = PROJECT_ID): Promise<CadParseRun[]> {
  const data = await safeFetch<ApiParseRun[]>(
    `/api/v1/projects/${projectId}/cad-parse-runs`,
  );
  return data ? data.map(mapParseRun) : [];
}

export async function getCadParseRun(
  parseRunId: string,
): Promise<CadParseRun | null> {
  const data = await safeFetch<ApiParseRun>(
    `/api/v1/cad-parse-runs/${parseRunId}`,
  );
  return data ? mapParseRun(data) : null;
}

export async function getCadParseSummary(
  parseRunId: string,
): Promise<CadParseSummary | null> {
  const data = await safeFetch<ApiSummary>(
    `/api/v1/cad-parse-runs/${parseRunId}/summary`,
  );
  return data ? mapSummary(data) : null;
}

export async function getCadLayers(
  parseRunId: string,
): Promise<CadLayerExtract[]> {
  const data = await safeFetch<ApiLayer[]>(
    `/api/v1/cad-parse-runs/${parseRunId}/layers`,
  );
  return data ? data.map(mapLayer) : [];
}

export async function getCadEntities(
  parseRunId: string,
): Promise<CadEntityExtract[]> {
  const data = await safeFetch<ApiEntity[]>(
    `/api/v1/cad-parse-runs/${parseRunId}/entities`,
  );
  return data ? data.map(mapEntity) : [];
}

export async function getCadBlocks(
  parseRunId: string,
): Promise<CadBlockExtract[]> {
  const data = await safeFetch<ApiBlock[]>(
    `/api/v1/cad-parse-runs/${parseRunId}/blocks`,
  );
  return data ? data.map(mapBlock) : [];
}

export async function getCadText(parseRunId: string): Promise<CadTextExtract[]> {
  const data = await safeFetch<ApiText[]>(
    `/api/v1/cad-parse-runs/${parseRunId}/text`,
  );
  return data ? data.map(mapText) : [];
}

export async function getCadReferenceCandidates(
  parseRunId: string,
): Promise<CadReferenceCandidate[]> {
  const data = await safeFetch<ApiCandidate[]>(
    `/api/v1/cad-parse-runs/${parseRunId}/reference-candidates`,
  );
  return data ? data.map(mapCandidate) : [];
}

export async function getCadReviewFindings(projectId: string = PROJECT_ID): Promise<CadReviewFinding[]> {
  const data = await safeFetch<ApiFinding[]>(
    `/api/v1/projects/${projectId}/cad-review-findings`,
  );
  return data ? data.map(mapFinding) : [];
}

export async function getCadFileReviewContext(
  cadFileId: string,
): Promise<CadFileReviewContext | null> {
  const data = await safeFetch<{
    cad_file: ApiCadFile;
    parse_run: ApiParseRun | null;
    summary: ApiSummary | null;
    layers: ApiLayer[];
    reference_candidates: ApiCandidate[];
    findings: ApiFinding[];
    note: string;
  }>(`/api/v1/cad-files/${cadFileId}/review-context`);
  if (!data) return null;
  return {
    cadFile: mapCadFile(data.cad_file),
    parseRun: data.parse_run ? mapParseRun(data.parse_run) : null,
    summary: data.summary ? mapSummary(data.summary) : null,
    layers: (data.layers ?? []).map(mapLayer),
    referenceCandidates: (data.reference_candidates ?? []).map(mapCandidate),
    findings: (data.findings ?? []).map(mapFinding),
    note: data.note,
  };
}

export async function createCadFileRecord(
  sampleKey = "brookside_meadows",
  uploadedBy = "reviewer",
  projectId: string = PROJECT_ID,
): Promise<{
  ok: boolean;
  backendReachable: boolean;
  cadFile?: CadFileUpload;
  error?: string;
}> {
  try {
    const res = await fetch(
      `${API_BASE_URL}/api/v1/projects/${projectId}/cad-files`,
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ sample_key: sampleKey, uploaded_by: uploadedBy }),
        cache: "no-store",
      },
    );
    if (!res.ok) {
      let detail = `Request failed (${res.status}).`;
      try {
        const body = (await res.json()) as { detail?: string };
        if (body.detail) detail = body.detail;
      } catch {
        // Keep generic message.
      }
      return { ok: false, backendReachable: true, error: detail };
    }
    return {
      ok: true,
      backendReachable: true,
      cadFile: mapCadFile((await res.json()) as ApiCadFile),
    };
  } catch {
    return {
      ok: false,
      backendReachable: false,
      error:
        "The backend is not reachable. Start the API to register and parse a DXF file. CAD data is not simulated in the browser.",
    };
  }
}

export async function parseCadFile(cadFileId: string): Promise<{
  ok: boolean;
  backendReachable: boolean;
  run?: CadParseRun;
  error?: string;
}> {
  try {
    const res = await fetch(
      `${API_BASE_URL}/api/v1/cad-files/${cadFileId}/parse`,
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
      return { ok: false, backendReachable: true, error: detail };
    }
    return {
      ok: true,
      backendReachable: true,
      run: mapParseRun((await res.json()) as ApiParseRun),
    };
  } catch {
    return {
      ok: false,
      backendReachable: false,
      error: "The backend is not reachable. Start the API to parse the DXF file.",
    };
  }
}

export async function compareCadReferencesToPlanSheets(
  parseRunId: string,
): Promise<CadPlanSheetComparison | null> {
  try {
    const res = await fetch(
      `${API_BASE_URL}/api/v1/cad-parse-runs/${parseRunId}/compare-plan-sheets`,
      { method: "POST", cache: "no-store" },
    );
    if (!res.ok) return null;
    const data = (await res.json()) as {
      parse_run_id: string;
      project_id: string;
      total_candidates: number;
      matched_count: number;
      unmatched_count: number;
      rows: {
        candidate_id: string;
        reference_text: string;
        normalized_reference: string;
        reference_type: string;
        matched_plan_sheet_id: string | null;
        matched_sheet_number: string | null;
        confidence_label: string;
        match_reason: string;
      }[];
      findings: ApiFinding[];
      note: string;
    };
    return {
      parseRunId: data.parse_run_id,
      projectId: data.project_id,
      totalCandidates: data.total_candidates,
      matchedCount: data.matched_count,
      unmatchedCount: data.unmatched_count,
      rows: data.rows.map((r) => ({
        candidateId: r.candidate_id,
        referenceText: r.reference_text,
        normalizedReference: r.normalized_reference,
        referenceType: r.reference_type,
        matchedPlanSheetId: r.matched_plan_sheet_id,
        matchedSheetNumber: r.matched_sheet_number,
        confidenceLabel: r.confidence_label,
        matchReason: r.match_reason,
      })),
      findings: (data.findings ?? []).map(mapFinding),
      note: data.note,
    };
  } catch {
    return null;
  }
}

// Phase 12: browser DXF upload, parse queue, dashboard, and finding promotion.

export type CadUploadLimits = {
  supportedExtensions: string[];
  supportedFileTypes: string[];
  maxFileSizeBytes: number;
  maxFileSizeMb: number;
  allowedValidationStatuses: string[];
  allowedQueueStatuses: string[];
  note: string;
};

export type CadUploadResponse = {
  ok: boolean;
  backendReachable: boolean;
  cadFile?: CadFileUpload;
  validationStatus?: string;
  validationMessage?: string;
  nextAction?: string;
  note?: string;
  error?: string;
};

export type CadParseQueueItem = {
  cadFileId: string;
  projectId: string;
  fileName: string;
  uploadSource: string;
  uploadStatus: string;
  validationStatus: string | null;
  validationMessage: string | null;
  queueStatus: string;
  parseRunId: string | null;
  parseStatus: string | null;
  warningCount: number;
  errorMessage: string | null;
  findingCount: number;
  parseRequestedAt: string | null;
  parseCompletedAt: string | null;
  requiresHumanReview: boolean;
};

export type CadIntakeDashboard = {
  projectId: string;
  totalFiles: number;
  filesNeedingParse: number;
  filesWithParseFailures: number;
  parseRunsNeedingHumanReview: number;
  totalFindings: number;
  unpromotedFindingsCount: number;
  promotedFindingsCount: number;
  queueStatusCounts: Record<string, number>;
  validationStatusCounts: Record<string, number>;
  parseStatusCounts: Record<string, number>;
  limitationsNote: string;
};

export type UnpromotedCadFinding = CadReviewFinding;

export type CadFindingPromotionResponse = {
  ok: boolean;
  backendReachable: boolean;
  cadReviewFindingId?: string;
  workflowItemId?: string | null;
  created?: boolean;
  alreadyPromoted?: boolean;
  note?: string;
  error?: string;
};

export type CadSelectedPromotionResult = {
  ok: boolean;
  backendReachable: boolean;
  requestedCount?: number;
  createdCount?: number;
  alreadyPromotedCount?: number;
  notFoundCount?: number;
  workflowItemIds?: string[];
  note?: string;
  error?: string;
};

export async function getCadUploadLimits(): Promise<CadUploadLimits | null> {
  const data = await safeFetch<{
    supported_extensions: string[];
    supported_file_types: string[];
    max_file_size_bytes: number;
    max_file_size_mb: number;
    allowed_validation_statuses: string[];
    allowed_queue_statuses: string[];
    note: string;
  }>(`/api/v1/cad-upload-limits`);
  if (!data) return null;
  return {
    supportedExtensions: data.supported_extensions ?? [],
    supportedFileTypes: data.supported_file_types ?? [],
    maxFileSizeBytes: data.max_file_size_bytes,
    maxFileSizeMb: data.max_file_size_mb,
    allowedValidationStatuses: data.allowed_validation_statuses ?? [],
    allowedQueueStatuses: data.allowed_queue_statuses ?? [],
    note: data.note,
  };
}

export async function uploadCadFile(
  file: File,
  uploadedBy = "reviewer",
  projectId: string = PROJECT_ID,
): Promise<CadUploadResponse> {
  // Client-side extension guard before sending. The backend validation remains
  // authoritative; this only avoids an obviously wrong request.
  if (!file.name.toLowerCase().endsWith(".dxf")) {
    return {
      ok: false,
      backendReachable: true,
      validationStatus: "rejected",
      error:
        "Only DXF files are supported in this phase. Select a .dxf file. DWG parsing is future work.",
    };
  }
  try {
    const form = new FormData();
    form.append("file", file);
    form.append("uploaded_by", uploadedBy);
    const res = await fetch(
      `${API_BASE_URL}/api/v1/projects/${projectId}/cad-files/upload`,
      { method: "POST", body: form, cache: "no-store" },
    );
    if (!res.ok) {
      let detail = `Request failed (${res.status}).`;
      try {
        const body = (await res.json()) as { detail?: string };
        if (body.detail) detail = body.detail;
      } catch {
        // Keep generic message.
      }
      return {
        ok: false,
        backendReachable: true,
        validationStatus: "rejected",
        error: detail,
      };
    }
    const data = (await res.json()) as {
      cad_file: ApiCadFile;
      validation_status: string;
      validation_message: string;
      next_action: string;
      note: string;
    };
    return {
      ok: true,
      backendReachable: true,
      cadFile: mapCadFile(data.cad_file),
      validationStatus: data.validation_status,
      validationMessage: data.validation_message,
      nextAction: data.next_action,
      note: data.note,
    };
  } catch {
    return {
      ok: false,
      backendReachable: false,
      error:
        "The backend is not reachable. Start the API to upload a DXF file. CAD data is not simulated in the browser.",
    };
  }
}

export async function requestCadParse(cadFileId: string): Promise<{
  ok: boolean;
  backendReachable: boolean;
  run?: CadParseRun;
  error?: string;
}> {
  try {
    const res = await fetch(
      `${API_BASE_URL}/api/v1/cad-files/${cadFileId}/request-parse`,
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
      return { ok: false, backendReachable: true, error: detail };
    }
    return {
      ok: true,
      backendReachable: true,
      run: mapParseRun((await res.json()) as ApiParseRun),
    };
  } catch {
    return {
      ok: false,
      backendReachable: false,
      error:
        "The backend is not reachable. Start the API to request a parse.",
    };
  }
}

export async function getCadParseQueue(projectId: string = PROJECT_ID): Promise<CadParseQueueItem[]> {
  const data = await safeFetch<
    {
      cad_file_id: string;
      project_id: string;
      file_name: string;
      upload_source: string;
      upload_status: string;
      validation_status: string | null;
      validation_message: string | null;
      queue_status: string;
      parse_run_id: string | null;
      parse_status: string | null;
      warning_count: number;
      error_message: string | null;
      finding_count: number;
      parse_requested_at: string | null;
      parse_completed_at: string | null;
      requires_human_review: boolean;
    }[]
  >(`/api/v1/projects/${projectId}/cad-parse-queue`);
  if (!data) return [];
  return data.map((r) => ({
    cadFileId: r.cad_file_id,
    projectId: r.project_id,
    fileName: r.file_name,
    uploadSource: r.upload_source,
    uploadStatus: r.upload_status,
    validationStatus: r.validation_status,
    validationMessage: r.validation_message,
    queueStatus: r.queue_status,
    parseRunId: r.parse_run_id,
    parseStatus: r.parse_status,
    warningCount: r.warning_count,
    errorMessage: r.error_message,
    findingCount: r.finding_count,
    parseRequestedAt: r.parse_requested_at,
    parseCompletedAt: r.parse_completed_at,
    requiresHumanReview: r.requires_human_review,
  }));
}

export async function getCadIntakeDashboard(projectId: string = PROJECT_ID): Promise<CadIntakeDashboard | null> {
  const data = await safeFetch<{
    project_id: string;
    total_files: number;
    files_needing_parse: number;
    files_with_parse_failures: number;
    parse_runs_needing_human_review: number;
    total_findings: number;
    unpromoted_findings_count: number;
    promoted_findings_count: number;
    queue_status_counts: Record<string, number>;
    validation_status_counts: Record<string, number>;
    parse_status_counts: Record<string, number>;
    limitations_note: string;
  }>(`/api/v1/projects/${projectId}/cad-intake/dashboard`);
  if (!data) return null;
  return {
    projectId: data.project_id,
    totalFiles: data.total_files,
    filesNeedingParse: data.files_needing_parse,
    filesWithParseFailures: data.files_with_parse_failures,
    parseRunsNeedingHumanReview: data.parse_runs_needing_human_review,
    totalFindings: data.total_findings,
    unpromotedFindingsCount: data.unpromoted_findings_count,
    promotedFindingsCount: data.promoted_findings_count,
    queueStatusCounts: data.queue_status_counts ?? {},
    validationStatusCounts: data.validation_status_counts ?? {},
    parseStatusCounts: data.parse_status_counts ?? {},
    limitationsNote: data.limitations_note,
  };
}

export async function getUnpromotedCadFindings(projectId: string = PROJECT_ID): Promise<UnpromotedCadFinding[]> {
  const data = await safeFetch<ApiFinding[]>(
    `/api/v1/projects/${projectId}/cad-review-findings/unpromoted`,
  );
  return data ? data.map(mapFinding) : [];
}

export async function promoteCadFindingToWorkflow(
  cadReviewFindingId: string,
  reviewerName = "reviewer",
  reviewerNote?: string,
): Promise<CadFindingPromotionResponse> {
  try {
    const res = await fetch(
      `${API_BASE_URL}/api/v1/cad-review-findings/${cadReviewFindingId}/promote-to-workflow`,
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          reviewer_name: reviewerName,
          reviewer_note: reviewerNote ?? null,
        }),
        cache: "no-store",
      },
    );
    if (!res.ok) {
      return {
        ok: false,
        backendReachable: true,
        error: `Request failed (${res.status}).`,
      };
    }
    const data = (await res.json()) as {
      cad_review_finding_id: string;
      workflow_item_id: string | null;
      created: boolean;
      already_promoted: boolean;
      note: string;
    };
    return {
      ok: true,
      backendReachable: true,
      cadReviewFindingId: data.cad_review_finding_id,
      workflowItemId: data.workflow_item_id,
      created: data.created,
      alreadyPromoted: data.already_promoted,
      note: data.note,
    };
  } catch {
    return {
      ok: false,
      backendReachable: false,
      error:
        "The backend is not reachable. Start the API to promote a CAD finding.",
    };
  }
}

export async function promoteSelectedCadFindingsToWorkflow(
  cadReviewFindingIds: string[],
  reviewerName = "reviewer",
  reviewerNote?: string,
  projectId: string = PROJECT_ID,
): Promise<CadSelectedPromotionResult> {
  try {
    const res = await fetch(
      `${API_BASE_URL}/api/v1/projects/${projectId}/cad-review-findings/promote-selected`,
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          cad_review_finding_ids: cadReviewFindingIds,
          reviewer_name: reviewerName,
          reviewer_note: reviewerNote ?? null,
        }),
        cache: "no-store",
      },
    );
    if (!res.ok) {
      return {
        ok: false,
        backendReachable: true,
        error: `Request failed (${res.status}).`,
      };
    }
    const data = (await res.json()) as {
      requested_count: number;
      created_count: number;
      already_promoted_count: number;
      not_found_count: number;
      workflow_item_ids: string[];
      note: string;
    };
    return {
      ok: true,
      backendReachable: true,
      requestedCount: data.requested_count,
      createdCount: data.created_count,
      alreadyPromotedCount: data.already_promoted_count,
      notFoundCount: data.not_found_count,
      workflowItemIds: data.workflow_item_ids,
      note: data.note,
    };
  } catch {
    return {
      ok: false,
      backendReachable: false,
      error:
        "The backend is not reachable. Start the API to promote CAD findings.",
    };
  }
}

export async function createWorkflowItemsFromCadFindings(projectId: string = PROJECT_ID): Promise<CadWorkflowItemsResult> {
  try {
    const res = await fetch(
      `${API_BASE_URL}/api/v1/projects/${projectId}/workflow-items/from-cad-findings`,
      { method: "POST", cache: "no-store" },
    );
    if (!res.ok) {
      return {
        ok: false,
        backendReachable: true,
        error: `Request failed (${res.status}).`,
      };
    }
    const data = (await res.json()) as {
      created_count: number;
      workflow_item_ids: string[];
      note: string;
    };
    return {
      ok: true,
      backendReachable: true,
      createdCount: data.created_count,
      workflowItemIds: data.workflow_item_ids,
      note: data.note,
    };
  } catch {
    return {
      ok: false,
      backendReachable: false,
      error:
        "The backend is not reachable. Start the API to create workflow items from CAD findings.",
    };
  }
}
