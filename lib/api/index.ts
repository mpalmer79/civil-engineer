export {
  API_BASE_URL,
  PROJECT_ID,
  getAuthToken,
  setAuthToken,
  clearAuthToken,
  authHeaders,
} from "./client";
export * from "./auth";
export * from "./diagnostics";
export * from "./fileStorage";
export * from "./responseMatrix";
export * from "./resubmittals";
export * from "./reviewerResponsePackages";
export * from "./commentLetters";
export * from "./project";
export * from "./documents";
export * from "./checklist";
export * from "./findings";
export * from "./audit";
export * from "./evaluation";
export * from "./hotspots";
export * from "./retrieval";
export * from "./humanReview";
export * from "./planSheets";
export * from "./reviewPackets";
export * from "./workflow";
export * from "./responsePackages";
export * from "./cadIntake";
export * from "./reviewCycle";
export * from "./commandCenter";
export * from "./realProjects";
export * from "./pdfEvidence";
export * from "./evidenceRetrieval";
export * from "./checklistReview";
export {
  getReviewerDashboard,
  getReviewerQueue,
  getReviewerDashboardProjects,
  getOrganizationDashboard,
  getOrganizationWorkload,
  getOrganizationReviewerWorkload,
  updateProjectAssignment,
  updateProjectPriority,
  type DashboardMetrics,
  type DashboardAggregate,
  type DashboardProjectSummary,
  type ReviewerQueueItem,
  type ReviewerDashboard,
  type ReviewerQueue,
  type OrganizationDashboard,
  type OrganizationWorkload,
  type OrganizationReviewerWorkload,
  type OrganizationReviewerWorkloadResult,
  type ReadResult,
} from "./dashboard";
export {
  getProjectWorkloadSummary,
  getProjectPendingActions,
  type ProjectWorkloadSummary,
  type ProjectPendingActions,
} from "./operationalMetrics";
// aiReview and cad export a few internal mappers and snake_case Api types for
// cross-module use (humanReview and planSheets import them). Re-export only
// their public names here so the mapping-layer internals stay out of the
// public @/lib/api surface.
export {
  getProviderMode,
  getAiReviewRuns,
  startAiReviewRun,
  getRunDraftFindings,
  getProjectDraftFindings,
  type ProviderModeInfo,
  type AiReviewRun,
  type AiDraftFinding,
} from "./aiReview";
export {
  getCadMetadata,
  getCadMetadataBySheet,
  getPlanReferences,
  getPlanInconsistencies,
  getPlanConsistencyFindings,
  getPlanConsistencySummary,
  runPlanConsistencyCheck,
  type CadMetadata,
  type PlanReference,
  type PlanConsistencyFinding,
  type PlanConsistencySummary,
  type PlanConsistencyCheckResult,
} from "./cad";
export { projectMetrics } from "@/data/brookside";
