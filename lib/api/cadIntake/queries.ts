import {
  PROJECT_ID,
  apiGetMapped,
  requireArray,
  requireRecord,
  requireString,
  type ApiResult,
} from "../client";
import {
  mapBlock,
  mapCadFile,
  mapCandidate,
  mapEntity,
  mapFinding,
  mapLayer,
  mapParseRun,
  mapSummary,
  mapText,
  type ApiBlock,
  type ApiCadFile,
  type ApiCandidate,
  type ApiEntity,
  type ApiFinding,
  type ApiLayer,
  type ApiParseRun,
  type ApiSummary,
  type ApiText,
} from "./mappers";
import type {
  CadBlockExtract,
  CadEntityExtract,
  CadFileReviewContext,
  CadFileUpload,
  CadIntakeDashboard,
  CadLayerExtract,
  CadParseQueueItem,
  CadParseRun,
  CadParseSummary,
  CadReferenceCandidate,
  CadReviewFinding,
  CadTextExtract,
  CadUploadLimits,
  UnpromotedCadFinding,
} from "./types";

// Read calls return a typed ApiResult so callers can render explicit failure
// states instead of substituting simulated CAD data.

export async function getCadFiles(
  projectId: string = PROJECT_ID,
): Promise<ApiResult<CadFileUpload[]>> {
  return apiGetMapped<ApiCadFile[], CadFileUpload[]>(
    `/api/v1/projects/${projectId}/cad-files`,
    (data) =>
      requireArray(data, "cad_files").map((f) => mapCadFile(f as ApiCadFile)),
  );
}

export async function getCadParseRuns(
  projectId: string = PROJECT_ID,
): Promise<ApiResult<CadParseRun[]>> {
  return apiGetMapped<ApiParseRun[], CadParseRun[]>(
    `/api/v1/projects/${projectId}/cad-parse-runs`,
    (data) =>
      requireArray(data, "cad_parse_runs").map((r) =>
        mapParseRun(r as ApiParseRun),
      ),
  );
}

export async function getCadParseRun(
  parseRunId: string,
): Promise<ApiResult<CadParseRun>> {
  return apiGetMapped<ApiParseRun, CadParseRun>(
    `/api/v1/cad-parse-runs/${parseRunId}`,
    mapParseRun,
  );
}

export async function getCadParseSummary(
  parseRunId: string,
): Promise<ApiResult<CadParseSummary>> {
  return apiGetMapped<ApiSummary, CadParseSummary>(
    `/api/v1/cad-parse-runs/${parseRunId}/summary`,
    mapSummary,
  );
}

export async function getCadLayers(
  parseRunId: string,
): Promise<ApiResult<CadLayerExtract[]>> {
  return apiGetMapped<ApiLayer[], CadLayerExtract[]>(
    `/api/v1/cad-parse-runs/${parseRunId}/layers`,
    (data) => requireArray(data, "layers").map((l) => mapLayer(l as ApiLayer)),
  );
}

export async function getCadEntities(
  parseRunId: string,
): Promise<ApiResult<CadEntityExtract[]>> {
  return apiGetMapped<ApiEntity[], CadEntityExtract[]>(
    `/api/v1/cad-parse-runs/${parseRunId}/entities`,
    (data) =>
      requireArray(data, "entities").map((e) => mapEntity(e as ApiEntity)),
  );
}

export async function getCadBlocks(
  parseRunId: string,
): Promise<ApiResult<CadBlockExtract[]>> {
  return apiGetMapped<ApiBlock[], CadBlockExtract[]>(
    `/api/v1/cad-parse-runs/${parseRunId}/blocks`,
    (data) => requireArray(data, "blocks").map((b) => mapBlock(b as ApiBlock)),
  );
}

export async function getCadText(
  parseRunId: string,
): Promise<ApiResult<CadTextExtract[]>> {
  return apiGetMapped<ApiText[], CadTextExtract[]>(
    `/api/v1/cad-parse-runs/${parseRunId}/text`,
    (data) => requireArray(data, "text").map((t) => mapText(t as ApiText)),
  );
}

export async function getCadReferenceCandidates(
  parseRunId: string,
): Promise<ApiResult<CadReferenceCandidate[]>> {
  return apiGetMapped<ApiCandidate[], CadReferenceCandidate[]>(
    `/api/v1/cad-parse-runs/${parseRunId}/reference-candidates`,
    (data) =>
      requireArray(data, "reference_candidates").map((c) =>
        mapCandidate(c as ApiCandidate),
      ),
  );
}

export async function getCadReviewFindings(
  projectId: string = PROJECT_ID,
): Promise<ApiResult<CadReviewFinding[]>> {
  return apiGetMapped<ApiFinding[], CadReviewFinding[]>(
    `/api/v1/projects/${projectId}/cad-review-findings`,
    (data) =>
      requireArray(data, "cad_review_findings").map((f) =>
        mapFinding(f as ApiFinding),
      ),
  );
}

export async function getCadFileReviewContext(
  cadFileId: string,
): Promise<ApiResult<CadFileReviewContext>> {
  return apiGetMapped<
    {
      cad_file: ApiCadFile;
      parse_run: ApiParseRun | null;
      summary: ApiSummary | null;
      layers: ApiLayer[];
      reference_candidates: ApiCandidate[];
      findings: ApiFinding[];
      note: string;
    },
    CadFileReviewContext
  >(`/api/v1/cad-files/${cadFileId}/review-context`, (data) => ({
    cadFile: mapCadFile(requireRecord(data.cad_file, "cad_file") as ApiCadFile),
    parseRun: data.parse_run ? mapParseRun(data.parse_run) : null,
    summary: data.summary ? mapSummary(data.summary) : null,
    layers: requireArray(data.layers ?? [], "layers").map((l) =>
      mapLayer(l as ApiLayer),
    ),
    referenceCandidates: requireArray(
      data.reference_candidates ?? [],
      "reference_candidates",
    ).map((c) => mapCandidate(c as ApiCandidate)),
    findings: requireArray(data.findings ?? [], "findings").map((f) =>
      mapFinding(f as ApiFinding),
    ),
    note: data.note,
  }));
}

// Phase 12: upload limits, parse queue, dashboard, and unpromoted findings.

export async function getCadUploadLimits(): Promise<ApiResult<CadUploadLimits>> {
  return apiGetMapped<{
    supported_extensions: string[];
    supported_file_types: string[];
    max_file_size_bytes: number;
    max_file_size_mb: number;
    allowed_validation_statuses: string[];
    allowed_queue_statuses: string[];
    note: string;
  }, CadUploadLimits>(`/api/v1/cad-upload-limits`, (data) => ({
    supportedExtensions: data.supported_extensions ?? [],
    supportedFileTypes: data.supported_file_types ?? [],
    maxFileSizeBytes: data.max_file_size_bytes,
    maxFileSizeMb: data.max_file_size_mb,
    allowedValidationStatuses: data.allowed_validation_statuses ?? [],
    allowedQueueStatuses: data.allowed_queue_statuses ?? [],
    note: data.note,
  }));
}

export async function getCadParseQueue(projectId: string = PROJECT_ID): Promise<ApiResult<CadParseQueueItem[]>> {
  return apiGetMapped<
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
    }[],
    CadParseQueueItem[]
  >(`/api/v1/projects/${projectId}/cad-parse-queue`, (data) => data.map((r) => ({
    cadFileId: requireString(r.cad_file_id, "cad_file_id"),
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
  })));
}

export async function getCadIntakeDashboard(projectId: string = PROJECT_ID): Promise<ApiResult<CadIntakeDashboard>> {
  return apiGetMapped<{
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
  }, CadIntakeDashboard>(`/api/v1/projects/${projectId}/cad-intake/dashboard`, (data) => ({
    projectId: requireString(data.project_id, "project_id"),
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
  }));
}

export async function getUnpromotedCadFindings(projectId: string = PROJECT_ID): Promise<ApiResult<UnpromotedCadFinding[]>> {
  return apiGetMapped<ApiFinding[], UnpromotedCadFinding[]>(
    `/api/v1/projects/${projectId}/cad-review-findings/unpromoted`,
    (data) => data.map(mapFinding),
  );
}
