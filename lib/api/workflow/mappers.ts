import type {
  WorkflowAction,
  WorkflowEvidenceLink,
  WorkflowFollowUp,
  WorkflowItem,
  WorkflowItemDetail,
} from "./types";

// Module-internal wire types and mappers shared by the read and mutation
// paths. These are not part of the public @/lib/api surface.

export type ApiWorkflowItem = {
  workflow_item_id: string;
  project_id: string;
  packet_id: string | null;
  packet_item_id: string | null;
  title: string;
  description: string;
  source_type: string;
  source_id: string | null;
  severity: string;
  status: string;
  assigned_role: string;
  reviewer_note: string | null;
  target_date: string | null;
  section_type: string;
  evidence_types: string[];
  requires_human_review: boolean;
  created_at: string;
  updated_at: string;
};

export type ApiEvidenceLink = {
  evidence_link_id: string;
  item_id: string;
  evidence_type: string;
  evidence_id: string;
  relationship: string;
  label: string;
  description: string | null;
};

export type ApiWorkflowAction = {
  action_id: string;
  workflow_item_id: string;
  project_id: string;
  action_type: string;
  previous_status: string;
  new_status: string;
  reviewer_note: string;
  reviewer_name: string;
  created_at: string;
};

export type ApiFollowUp = {
  follow_up_id: string;
  workflow_item_id: string;
  project_id: string;
  requested_from: string;
  request_reason: string;
  requested_information: string;
  target_date: string | null;
  status: string;
  reviewer_name: string;
  created_at: string;
  updated_at: string;
};

export type ApiWorkflowItemDetail = ApiWorkflowItem & {
  evidence_links: ApiEvidenceLink[];
  follow_ups: ApiFollowUp[];
  actions: ApiWorkflowAction[];
};

export function mapItem(i: ApiWorkflowItem): WorkflowItem {
  return {
    workflowItemId: i.workflow_item_id,
    projectId: i.project_id,
    packetId: i.packet_id,
    packetItemId: i.packet_item_id,
    title: i.title,
    description: i.description,
    sourceType: i.source_type,
    sourceId: i.source_id,
    severity: i.severity,
    status: i.status,
    assignedRole: i.assigned_role,
    reviewerNote: i.reviewer_note,
    targetDate: i.target_date,
    sectionType: i.section_type,
    evidenceTypes: i.evidence_types ?? [],
    requiresHumanReview: i.requires_human_review,
    createdAt: i.created_at,
    updatedAt: i.updated_at,
  };
}

export function mapEvidenceLink(l: ApiEvidenceLink): WorkflowEvidenceLink {
  return {
    evidenceLinkId: l.evidence_link_id,
    itemId: l.item_id,
    evidenceType: l.evidence_type,
    evidenceId: l.evidence_id,
    relationship: l.relationship,
    label: l.label,
    description: l.description,
  };
}

export function mapAction(a: ApiWorkflowAction): WorkflowAction {
  return {
    actionId: a.action_id,
    workflowItemId: a.workflow_item_id,
    projectId: a.project_id,
    actionType: a.action_type,
    previousStatus: a.previous_status,
    newStatus: a.new_status,
    reviewerNote: a.reviewer_note,
    reviewerName: a.reviewer_name,
    createdAt: a.created_at,
  };
}

export function mapFollowUp(f: ApiFollowUp): WorkflowFollowUp {
  return {
    followUpId: f.follow_up_id,
    workflowItemId: f.workflow_item_id,
    projectId: f.project_id,
    requestedFrom: f.requested_from,
    requestReason: f.request_reason,
    requestedInformation: f.requested_information,
    targetDate: f.target_date,
    status: f.status,
    reviewerName: f.reviewer_name,
    createdAt: f.created_at,
    updatedAt: f.updated_at,
  };
}

export function mapItemDetail(i: ApiWorkflowItemDetail): WorkflowItemDetail {
  return {
    ...mapItem(i),
    evidenceLinks: (i.evidence_links ?? []).map(mapEvidenceLink),
    followUps: (i.follow_ups ?? []).map(mapFollowUp),
    actions: (i.actions ?? []).map(mapAction),
  };
}
