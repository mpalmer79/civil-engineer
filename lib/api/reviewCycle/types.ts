// Phase 13: multi-round resubmittal, revision comparison, and applicant response
// cycle. Data is backend-canonical. The frontend does not simulate review cycle
// data. Read calls return a typed ApiResult that preserves the failure category,
// and mutating calls return a clear backend-required result.

export type ReviewCycle = {
  reviewCycleId: string;
  projectId: string;
  cycleNumber: number;
  cycleName: string;
  status: string;
  startedAt: string;
  completedAt: string | null;
  sourceResponsePackageId: string | null;
  sourceWorkflowBoardId: string | null;
  summary: string;
  requiresHumanReview: boolean;
  createdAt: string;
  updatedAt: string;
};

export type ResubmittalDocument = {
  resubmittalDocumentId: string;
  projectId: string;
  reviewCycleId: string;
  resubmittalPackageId: string;
  documentType: string;
  sourceType: string;
  sourceId: string | null;
  fileName: string | null;
  description: string;
  status: string;
  createdAt: string;
};

export type ApplicantResponse = {
  applicantResponseId: string;
  projectId: string;
  reviewCycleId: string;
  resubmittalPackageId: string;
  responseText: string;
  responseTopic: string;
  submittedBy: string;
  targetResponseItemId: string | null;
  targetWorkflowItemId: string | null;
  status: string;
  reviewerNote: string | null;
  requiresHumanReview: boolean;
  createdAt: string;
  updatedAt: string;
};

export type ResubmittalPackage = {
  resubmittalPackageId: string;
  projectId: string;
  reviewCycleId: string;
  packageName: string;
  submittedBy: string;
  submittedAt: string | null;
  receivedAt: string;
  status: string;
  summary: string;
  reviewerNote: string | null;
  requiresHumanReview: boolean;
  createdAt: string;
  updatedAt: string;
  documents?: ResubmittalDocument[];
  applicantResponses?: ApplicantResponse[];
};

export type ApplicantResponseMapping = {
  mappingId: string;
  projectId: string;
  reviewCycleId: string;
  applicantResponseId: string;
  responsePackageItemId: string | null;
  workflowItemId: string | null;
  responseResolutionRecordId: string | null;
  mappingConfidence: string;
  mappingReason: string;
  requiresHumanReview: boolean;
  createdAt: string;
};

export type RevisionComparisonRun = {
  comparisonRunId: string;
  projectId: string;
  reviewCycleId: string;
  resubmittalPackageId: string | null;
  previousParseRunId: string;
  currentParseRunId: string;
  status: string;
  startedAt: string;
  completedAt: string | null;
  comparedLayerCount: number;
  comparedTextCount: number;
  addedCount: number;
  removedCount: number;
  changedCount: number;
  unchangedCount: number;
  warningCount: number;
  summary: string;
  limitationsNote: string;
  requiresHumanReview: boolean;
};

export type RevisionChangeRecord = {
  changeRecordId: string;
  projectId: string;
  reviewCycleId: string;
  comparisonRunId: string;
  changeType: string;
  sourceCategory: string;
  previousValue: string | null;
  currentValue: string | null;
  normalizedKey: string;
  layerName: string | null;
  referenceType: string | null;
  severity: string;
  linkedCadReviewFindingId: string | null;
  linkedWorkflowItemId: string | null;
  reviewerStatus: string;
  reviewerNote: string | null;
  requiresHumanReview: boolean;
  createdAt: string;
};

export type IssueCarryForward = {
  carryForwardId: string;
  projectId: string;
  reviewCycleId: string;
  sourceWorkflowItemId: string | null;
  sourceResponseItemId: string | null;
  sourceCadFindingId: string | null;
  sourceRevisionChangeId: string | null;
  title: string;
  reason: string;
  carriedForwardStatus: string;
  targetWorkflowItemId: string | null;
  createdAt: string;
  reviewerName: string;
  reviewerNote: string | null;
  requiresHumanReview: boolean;
};

export type ResponseResolutionRecord = {
  resolutionRecordId: string;
  projectId: string;
  reviewCycleId: string;
  responsePackageItemId: string | null;
  workflowItemId: string | null;
  applicantResponseId: string | null;
  revisionChangeRecordId: string | null;
  status: string;
  reviewerNote: string | null;
  reviewerName: string;
  createdAt: string;
  updatedAt: string;
  requiresHumanReview: boolean;
};

export type NextCyclePreparation = {
  nextCyclePreparationId: string;
  projectId: string;
  reviewCycleId: string;
  status: string;
  summary: string;
  carriedForwardCount: number;
  needsMoreInformationCount: number;
  reviewerCheckedCount: number;
  nextResponsePackageReady: boolean;
  createdAt: string;
  updatedAt: string;
  requiresHumanReview: boolean;
};

export type ReviewCycleDashboard = {
  projectId: string;
  cycleCount: number;
  activeCycleId: string | null;
  activeCycleNumber: number | null;
  reviewCycles: ReviewCycle[];
  resubmittalCount: number;
  resubmittalStatuses: Record<string, number>;
  applicantResponseCount: number;
  unmappedResponseCount: number;
  comparisonRunCount: number;
  revisionChangeCount: number;
  carryForwardCount: number;
  resolutionCount: number;
  resolutionStatuses: Record<string, number>;
  openItemCount: number;
  nextCycleReady: boolean;
  limitationsNote: string;
};

export type ResponseMappingSummary = {
  reviewCycleId: string;
  projectId: string;
  responseCount: number;
  mappedCount: number;
  unmappedCount: number;
  suggestedCount: number;
  confidenceCounts: Record<string, number>;
  note: string;
};

export type RevisionComparisonSummary = {
  comparisonRunId: string;
  projectId: string;
  reviewCycleId: string;
  status: string;
  addedCount: number;
  removedCount: number;
  changedCount: number;
  unchangedCount: number;
  carriedForwardCount: number;
  changesByCategory: Record<string, number>;
  changesByType: Record<string, number>;
  limitationsNote: string;
  note: string;
};

export type CarryForwardSummary = {
  reviewCycleId: string;
  projectId: string;
  total: number;
  statuses: Record<string, number>;
  note: string;
};

export type ResolutionSummary = {
  reviewCycleId: string;
  projectId: string;
  total: number;
  statuses: Record<string, number>;
  note: string;
};
