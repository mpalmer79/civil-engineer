// Production Foundations Sprint 1: real project intake and persistent review
// records. This data is backend-canonical. The frontend does not simulate real
// project records. These are the public types for the module; the wire types
// and mappers in mappers.ts are module-internal and not re-exported.

export type ProjectSourceMode = "demo_fixture" | "user_created";

export type ProjectDetail = {
  projectId: string;
  projectName: string;
  projectType: string;
  locationContext: string;
  jurisdiction: string;
  reviewType: string;
  reviewDomain: string;
  acreage: number;
  disturbedArea: number;
  proposedLots: number;
  status: string;
  summary: string;
  sourceMode: string;
  createdByName: string | null;
  applicantName: string | null;
  applicantOrganization: string | null;
  designEngineerName: string | null;
  designFirm: string | null;
  submissionReference: string | null;
  reviewRoundCurrent: number;
  parcelIds: string[];
  assignedReviewerUserId: string | null;
  assignedReviewerName: string | null;
  reviewPriority: string | null;
  reviewDueDate: string | null;
  lastReviewerActivityAt: string | null;
  createdAt: string | null;
  updatedAt: string | null;
  documentCount: number;
  findingCount: number;
  auditEventCount: number;
};

export type ProjectDocument = {
  documentId: string;
  projectId: string;
  fileName: string;
  originalFileName: string | null;
  documentType: string;
  status: string;
  purpose: string;
  expectedKeyInformation: string;
  sourceMode: string;
  uploadStatus: string | null;
  processingStatus: string | null;
  contentType: string | null;
  fileSizeBytes: number | null;
  checksumSha256: string | null;
  revisionLabel: string | null;
  revisionDate: string | null;
  uploadedByName: string | null;
  uploadedAt: string | null;
  registeredAt: string | null;
  pageCount: number | null;
  indexedAt: string | null;
  textExtractionStatus: string | null;
  textExtractionSummary: string | null;
  extractionWarningCount: number;
  storageProvider: string | null;
  fileAvailable: boolean;
  downloadCount: number;
  lastDownloadedAt: string | null;
};

export type ReviewerFinding = {
  findingId: string;
  projectId: string;
  title: string;
  category: string;
  riskLevel: string;
  evidenceStatus: string | null;
  evidenceToFind: string;
  reasonItMatters: string;
  recommendedHumanAction: string;
  humanReviewStatus: string;
  relatedDocuments: string[];
  relatedChecklistItems: string[];
  sourceMode: string;
  findingOrigin: string;
  reviewerNotes: string | null;
  createdByName: string | null;
  createdAt: string | null;
};

export type ProjectAuditEvent = {
  auditEventId: string;
  projectId: string;
  eventType: string;
  actorType: string;
  actorDisplayName: string | null;
  relatedEntityType: string;
  relatedEntityId: string;
  description: string;
  timestamp: string;
  eventMetadata: Record<string, unknown>;
};

export type CreateProjectInput = {
  projectName: string;
  projectType?: string;
  jurisdiction?: string;
  reviewType?: string;
  reviewDomain?: string;
  locationContext?: string;
  acreage?: number | null;
  disturbedArea?: number | null;
  proposedLots?: number | null;
  summary?: string;
  applicantName?: string;
  applicantOrganization?: string;
  designEngineerName?: string;
  designFirm?: string;
  submissionReference?: string;
  parcelIds?: string[];
};

export type RegisterDocumentInput = {
  originalFileName: string;
  documentType?: string;
  purpose?: string;
  expectedKeyInformation?: string;
  contentType?: string;
  fileSizeBytes?: number | null;
  revisionLabel?: string;
  revisionDate?: string;
};

export type CreateFindingInput = {
  title: string;
  category?: string;
  riskLevel?: string;
  evidenceStatus?: string;
  evidenceToFind?: string;
  reasonItMatters?: string;
  recommendedHumanAction?: string;
  relatedDocuments?: string[];
  reviewerNotes?: string;
  humanReviewStatus?: string;
};

export type CreateEvidenceReferenceInput = {
  documentId: string;
  reviewerNote: string;
  pageNumber?: number | null;
  sheetNumber?: string;
  sectionLabel?: string;
};
