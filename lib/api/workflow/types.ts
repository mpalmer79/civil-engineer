// Phase 9: reviewer workflow board and issue resolution tracking.
//
// Phase 9 data is backend-canonical. The frontend does not simulate workflow
// data. These are the public types for the module; the wire types and mappers
// in mappers.ts are module-internal and not re-exported.

export type WorkflowEvidenceLink = {
  evidenceLinkId: string;
  itemId: string;
  evidenceType: string;
  evidenceId: string;
  relationship: string;
  label: string;
  description: string | null;
};

export type WorkflowAction = {
  actionId: string;
  workflowItemId: string;
  projectId: string;
  actionType: string;
  previousStatus: string;
  newStatus: string;
  reviewerNote: string;
  reviewerName: string;
  createdAt: string;
};

export type WorkflowFollowUp = {
  followUpId: string;
  workflowItemId: string;
  projectId: string;
  requestedFrom: string;
  requestReason: string;
  requestedInformation: string;
  targetDate: string | null;
  status: string;
  reviewerName: string;
  createdAt: string;
  updatedAt: string;
};

export type WorkflowItem = {
  workflowItemId: string;
  projectId: string;
  packetId: string | null;
  packetItemId: string | null;
  title: string;
  description: string;
  sourceType: string;
  sourceId: string | null;
  severity: string;
  status: string;
  assignedRole: string;
  reviewerNote: string | null;
  targetDate: string | null;
  sectionType: string;
  evidenceTypes: string[];
  requiresHumanReview: boolean;
  createdAt: string;
  updatedAt: string;
};

export type WorkflowItemDetail = WorkflowItem & {
  evidenceLinks: WorkflowEvidenceLink[];
  followUps: WorkflowFollowUp[];
  actions: WorkflowAction[];
};

export type WorkflowItemHistory = {
  workflowItemId: string;
  projectId: string;
  actions: WorkflowAction[];
  followUps: WorkflowFollowUp[];
  note: string;
};

export type WorkflowBoardSummary = {
  projectId: string;
  totalItems: number;
  itemsByStatus: Record<string, number>;
  itemsBySeverity: Record<string, number>;
  itemsBySectionType: Record<string, number>;
  itemsByAssignedRole: Record<string, number>;
  itemsRequiringHumanReview: number;
  openFollowUpCount: number;
  readyForHandoffCount: number;
  note: string;
};

export type ReadyForHandoffSummary = {
  projectId: string;
  totalItems: number;
  readyCount: number;
  outstandingFollowUpCount: number;
  items: WorkflowItem[];
  note: string;
};

export type WorkflowMutationResult = {
  ok: boolean;
  status: number;
  backendReachable: boolean;
  item?: WorkflowItem;
  followUp?: WorkflowFollowUp;
  error?: string;
};
