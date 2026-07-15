// Phase 11: real CAD (DXF) intake and parsing.
//
// Phase 11 data is backend-canonical. The frontend does not simulate parsed CAD
// data. Read calls return a typed ApiResult so callers can render explicit
// failure states, and the mutating calls return a clear backend-required
// result. CAD intake is a high-risk mapping surface, so the mappers assert
// identifiers and required fields; a malformed payload surfaces as an
// invalid_response failure instead of propagating undefined fields.

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
