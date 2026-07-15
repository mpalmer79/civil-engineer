// Phase 10: external review response package.
//
// Phase 10 data is backend-canonical. The frontend does not simulate response
// package data. Read calls return a typed ApiResult that preserves the status
// and failure category, and the mutating calls return a clear backend-required
// result. Response packages are a high-risk domain, so mappers assert
// identifiers and required fields; a structurally invalid payload surfaces as
// an invalid_response failure instead of undefined fields in the UI.

export type ResponsePackageEvidenceLink = {
  evidenceLinkId: string;
  responsePackageId: string;
  responseItemId: string;
  evidenceType: string;
  evidenceId: string;
  relationship: string;
  label: string;
  description: string | null;
};

export type ResponsePackageItem = {
  itemId: string;
  responsePackageId: string;
  sectionId: string;
  workflowItemId: string | null;
  packetItemId: string | null;
  title: string;
  draftText: string;
  reviewerNote: string | null;
  severity: string;
  status: string;
  sourceType: string;
  sourceId: string | null;
  assignedRole: string;
  requiresHumanReview: boolean;
  displayOrder: number;
  evidenceLinks: ResponsePackageEvidenceLink[];
};

export type ResponsePackageSection = {
  sectionId: string;
  responsePackageId: string;
  title: string;
  sectionType: string;
  displayOrder: number;
  summary: string;
  status: string;
  requiresHumanReview: boolean;
  items: ResponsePackageItem[];
};

export type ResponsePackageAttachment = {
  attachmentId: string;
  responsePackageId: string;
  label: string;
  attachmentType: string;
  sourceType: string;
  sourceId: string | null;
  included: boolean;
  description: string | null;
};

export type ResponsePackage = {
  responsePackageId: string;
  projectId: string;
  sourcePacketId: string | null;
  title: string;
  audienceType: string;
  status: string;
  summary: string;
  draftIntro: string;
  draftClosing: string;
  limitationsNote: string;
  createdBy: string;
  createdAt: string;
  updatedAt: string;
};

export type ResponsePackageDetail = ResponsePackage & {
  sections: ResponsePackageSection[];
  attachments: ResponsePackageAttachment[];
};

export type ResponsePackageAction = {
  actionId: string;
  responsePackageId: string;
  responseItemId: string | null;
  actionType: string;
  previousStatus: string;
  newStatus: string;
  reviewerNote: string;
  reviewerName: string;
  createdAt: string;
};

export type ResponsePackageSignoffCheckItem = {
  label: string;
  detail: string;
  confirmed: boolean;
};

export type ResponsePackagePrintView = {
  responsePackageId: string;
  projectId: string;
  title: string;
  audienceType: string;
  status: string;
  summary: string;
  draftIntro: string;
  draftClosing: string;
  createdBy: string;
  createdAt: string;
  limitationsNote: string;
  externalCommunicationBoundary: string;
  draftNotice: string;
  sections: {
    title: string;
    sectionType: string;
    summary: string;
    items: ResponsePackageItem[];
  }[];
  attachments: ResponsePackageAttachment[];
  signoffChecklist: ResponsePackageSignoffCheckItem[];
};

export type ResponsePackageSummary = {
  responsePackageId: string;
  projectId: string;
  status: string;
  audienceType: string;
  totalSections: number;
  totalItems: number;
  totalAttachments: number;
  totalEvidenceLinks: number;
  itemsBySectionType: Record<string, number>;
  itemsByStatus: Record<string, number>;
  itemsBySeverity: Record<string, number>;
  itemsRequiringHumanReview: number;
};

export type ResponsePackageHistory = {
  responsePackageId: string;
  projectId: string;
  actions: ResponsePackageAction[];
  note: string;
};

export type ResponsePackageMutationResult = {
  ok: boolean;
  status: number;
  backendReachable: boolean;
  package?: ResponsePackage;
  item?: ResponsePackageItem;
  action?: ResponsePackageAction;
  error?: string;
};
