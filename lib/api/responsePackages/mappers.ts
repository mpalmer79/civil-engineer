import { requireString } from "../client";
import type {
  ResponsePackage,
  ResponsePackageAction,
  ResponsePackageAttachment,
  ResponsePackageDetail,
  ResponsePackageEvidenceLink,
  ResponsePackageItem,
  ResponsePackageSection,
} from "./types";

// Module-internal wire types and mappers shared by the read and mutation
// paths. These are not part of the public @/lib/api surface. Response packages
// are a high-risk domain, so mappers assert identifiers and required fields.

export type ApiEvidenceLink = {
  evidence_link_id: string;
  response_package_id: string;
  response_item_id: string;
  evidence_type: string;
  evidence_id: string;
  relationship: string;
  label: string;
  description: string | null;
};

export type ApiItem = {
  item_id: string;
  response_package_id: string;
  section_id: string;
  workflow_item_id: string | null;
  packet_item_id: string | null;
  title: string;
  draft_text: string;
  reviewer_note: string | null;
  severity: string;
  status: string;
  source_type: string;
  source_id: string | null;
  assigned_role: string;
  requires_human_review: boolean;
  display_order: number;
  evidence_links: ApiEvidenceLink[];
};

export type ApiSection = {
  section_id: string;
  response_package_id: string;
  title: string;
  section_type: string;
  display_order: number;
  summary: string;
  status: string;
  requires_human_review: boolean;
  items: ApiItem[];
};

export type ApiAttachment = {
  attachment_id: string;
  response_package_id: string;
  label: string;
  attachment_type: string;
  source_type: string;
  source_id: string | null;
  included: boolean;
  description: string | null;
};

export type ApiPackage = {
  response_package_id: string;
  project_id: string;
  source_packet_id: string | null;
  title: string;
  audience_type: string;
  status: string;
  summary: string;
  draft_intro: string;
  draft_closing: string;
  limitations_note: string;
  created_by: string;
  created_at: string;
  updated_at: string;
  sections?: ApiSection[];
  attachments?: ApiAttachment[];
};

export type ApiAction = {
  action_id: string;
  response_package_id: string;
  response_item_id: string | null;
  action_type: string;
  previous_status: string;
  new_status: string;
  reviewer_note: string;
  reviewer_name: string;
  created_at: string;
};

export function mapEvidenceLink(
  l: ApiEvidenceLink,
): ResponsePackageEvidenceLink {
  return {
    evidenceLinkId: requireString(l.evidence_link_id, "evidence_link_id"),
    responsePackageId: requireString(
      l.response_package_id,
      "response_package_id",
    ),
    responseItemId: requireString(l.response_item_id, "response_item_id"),
    evidenceType: requireString(l.evidence_type, "evidence_type"),
    evidenceId: requireString(l.evidence_id, "evidence_id"),
    relationship: l.relationship,
    label: l.label,
    description: l.description,
  };
}

export function mapItem(i: ApiItem): ResponsePackageItem {
  return {
    itemId: requireString(i.item_id, "item_id"),
    responsePackageId: requireString(
      i.response_package_id,
      "response_package_id",
    ),
    sectionId: requireString(i.section_id, "section_id"),
    workflowItemId: i.workflow_item_id,
    packetItemId: i.packet_item_id,
    title: requireString(i.title, "title"),
    draftText: requireString(i.draft_text, "draft_text"),
    reviewerNote: i.reviewer_note,
    severity: i.severity,
    status: requireString(i.status, "status"),
    sourceType: i.source_type,
    sourceId: i.source_id,
    assignedRole: i.assigned_role,
    requiresHumanReview: i.requires_human_review,
    displayOrder: i.display_order,
    evidenceLinks: (i.evidence_links ?? []).map(mapEvidenceLink),
  };
}

export function mapSection(s: ApiSection): ResponsePackageSection {
  return {
    sectionId: requireString(s.section_id, "section_id"),
    responsePackageId: requireString(
      s.response_package_id,
      "response_package_id",
    ),
    title: requireString(s.title, "title"),
    sectionType: s.section_type,
    displayOrder: s.display_order,
    summary: s.summary,
    status: s.status,
    requiresHumanReview: s.requires_human_review,
    items: (s.items ?? []).map(mapItem),
  };
}

export function mapAttachment(a: ApiAttachment): ResponsePackageAttachment {
  return {
    attachmentId: requireString(a.attachment_id, "attachment_id"),
    responsePackageId: requireString(
      a.response_package_id,
      "response_package_id",
    ),
    label: requireString(a.label, "label"),
    attachmentType: a.attachment_type,
    sourceType: a.source_type,
    sourceId: a.source_id,
    included: a.included,
    description: a.description,
  };
}

export function mapPackage(p: ApiPackage): ResponsePackage {
  return {
    responsePackageId: requireString(
      p.response_package_id,
      "response_package_id",
    ),
    projectId: requireString(p.project_id, "project_id"),
    sourcePacketId: p.source_packet_id,
    title: requireString(p.title, "title"),
    audienceType: requireString(p.audience_type, "audience_type"),
    status: requireString(p.status, "status"),
    summary: p.summary,
    draftIntro: p.draft_intro,
    draftClosing: p.draft_closing,
    limitationsNote: p.limitations_note,
    createdBy: p.created_by,
    createdAt: p.created_at,
    updatedAt: p.updated_at,
  };
}

export function mapPackageDetail(p: ApiPackage): ResponsePackageDetail {
  return {
    ...mapPackage(p),
    sections: (p.sections ?? []).map(mapSection),
    attachments: (p.attachments ?? []).map(mapAttachment),
  };
}

export function mapAction(a: ApiAction): ResponsePackageAction {
  return {
    actionId: requireString(a.action_id, "action_id"),
    responsePackageId: requireString(
      a.response_package_id,
      "response_package_id",
    ),
    responseItemId: a.response_item_id,
    actionType: a.action_type,
    previousStatus: a.previous_status,
    newStatus: a.new_status,
    reviewerNote: a.reviewer_note,
    reviewerName: a.reviewer_name,
    createdAt: a.created_at,
  };
}
