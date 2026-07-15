// Phase 8: review packet builder and evidence traceability.
//
// Phase 8 data is backend-canonical. The frontend does not simulate packet
// data. Read calls return a typed ApiResult that preserves the status and
// failure category, and the mutating calls return a clear backend-required
// result. Review packets are a high-risk domain, so mappers assert identifiers
// and required fields; a structurally invalid payload surfaces as an
// invalid_response failure instead of undefined fields in the UI.

export type ReviewPacketEvidenceLink = {
  evidenceLinkId: string;
  packetId: string;
  itemId: string;
  evidenceType: string;
  evidenceId: string;
  relationship: string;
  label: string;
  description: string | null;
};

export type ReviewPacketItem = {
  itemId: string;
  packetId: string;
  sectionId: string;
  itemType: string;
  title: string;
  description: string;
  severity: string;
  sourceType: string;
  sourceId: string | null;
  reviewerStatus: string;
  reviewerNote: string | null;
  requiresHumanReview: boolean;
  displayOrder: number;
  evidenceLinks: ReviewPacketEvidenceLink[];
};

export type ReviewPacketSection = {
  sectionId: string;
  packetId: string;
  title: string;
  sectionType: string;
  displayOrder: number;
  summary: string;
  status: string;
  requiresHumanReview: boolean;
  items: ReviewPacketItem[];
};

export type ReviewPacket = {
  packetId: string;
  projectId: string;
  title: string;
  packetType: string;
  status: string;
  summary: string;
  generatedFromPhase: string;
  createdBy: string;
  limitationsNote: string;
  createdAt: string;
  updatedAt: string;
};

export type ReviewPacketDetail = ReviewPacket & {
  sections: ReviewPacketSection[];
};

export type ReviewPacketReviewerAction = {
  actionId: string;
  packetId: string;
  itemId: string;
  actionType: string;
  reviewerNote: string;
  previousStatus: string;
  newStatus: string;
  reviewerName: string;
  createdAt: string;
};

export type TraceabilityRow = {
  sectionType: string;
  itemId: string;
  itemTitle: string;
  itemType: string;
  sourceType: string;
  sourceId: string | null;
  evidenceType: string;
  evidenceId: string;
  relationship: string;
  label: string;
};

export type ReviewPacketTraceability = {
  packetId: string;
  projectId: string;
  totalRows: number;
  rows: TraceabilityRow[];
  note: string;
};

export type ReviewPacketPrintSection = {
  title: string;
  sectionType: string;
  summary: string;
  items: ReviewPacketItem[];
};

export type ReviewPacketTraceabilityReviewRow = {
  traceabilityRowKey: string;
  checklistTitle: string | null;
  checklistRequirement: string | null;
  relationshipType: string;
  reviewActionType: string | null;
  reviewerNote: string | null;
  createdBy: string | null;
  requiresReviewerConfirmation: boolean;
};

export type ReviewPacketPrintView = {
  packetId: string;
  projectId: string;
  title: string;
  packetType: string;
  status: string;
  summary: string;
  generatedFromPhase: string;
  createdBy: string;
  createdAt: string;
  limitationsNote: string;
  professionalLimitations: string;
  draftNotice: string;
  sections: ReviewPacketPrintSection[];
  traceabilityReviewRows: ReviewPacketTraceabilityReviewRow[];
  traceabilityNote: string | null;
};

export type ReviewPacketSummary = {
  packetId: string;
  projectId: string;
  status: string;
  totalSections: number;
  totalItems: number;
  totalEvidenceLinks: number;
  itemsBySectionType: Record<string, number>;
  itemsByStatus: Record<string, number>;
  itemsBySeverity: Record<string, number>;
  itemsRequiringHumanReview: number;
};

export type ReviewPacketActionInput = {
  actionType: string;
  reviewerNote: string;
  reviewerName: string;
};

export type ReviewPacketMutationResult = {
  ok: boolean;
  status: number;
  backendReachable: boolean;
  item?: ReviewPacketItem;
  action?: ReviewPacketReviewerAction;
  error?: string;
};
