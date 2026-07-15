import { requireString } from "../client";
import type {
  ReviewPacket,
  ReviewPacketDetail,
  ReviewPacketEvidenceLink,
  ReviewPacketItem,
  ReviewPacketReviewerAction,
  ReviewPacketSection,
} from "./types";

// Module-internal wire types and mappers shared by the read and mutation
// paths. These are not part of the public @/lib/api surface. Review packets
// are a high-risk domain, so mappers assert identifiers and required fields.

export type ApiEvidenceLink = {
  evidence_link_id: string;
  packet_id: string;
  item_id: string;
  evidence_type: string;
  evidence_id: string;
  relationship: string;
  label: string;
  description: string | null;
};

export type ApiPacketItem = {
  item_id: string;
  packet_id: string;
  section_id: string;
  item_type: string;
  title: string;
  description: string;
  severity: string;
  source_type: string;
  source_id: string | null;
  reviewer_status: string;
  reviewer_note: string | null;
  requires_human_review: boolean;
  display_order: number;
  evidence_links: ApiEvidenceLink[];
};

export type ApiPacketSection = {
  section_id: string;
  packet_id: string;
  title: string;
  section_type: string;
  display_order: number;
  summary: string;
  status: string;
  requires_human_review: boolean;
  items: ApiPacketItem[];
};

export type ApiReviewPacket = {
  packet_id: string;
  project_id: string;
  title: string;
  packet_type: string;
  status: string;
  summary: string;
  generated_from_phase: string;
  created_by: string;
  limitations_note: string;
  created_at: string;
  updated_at: string;
  sections?: ApiPacketSection[];
};

export type ApiPacketAction = {
  action_id: string;
  packet_id: string;
  item_id: string;
  action_type: string;
  reviewer_note: string;
  previous_status: string;
  new_status: string;
  reviewer_name: string;
  created_at: string;
};

export function mapEvidenceLink(l: ApiEvidenceLink): ReviewPacketEvidenceLink {
  return {
    evidenceLinkId: requireString(l.evidence_link_id, "evidence_link_id"),
    packetId: requireString(l.packet_id, "packet_id"),
    itemId: requireString(l.item_id, "item_id"),
    evidenceType: requireString(l.evidence_type, "evidence_type"),
    evidenceId: requireString(l.evidence_id, "evidence_id"),
    relationship: l.relationship,
    label: l.label,
    description: l.description,
  };
}

export function mapPacketItem(i: ApiPacketItem): ReviewPacketItem {
  return {
    itemId: requireString(i.item_id, "item_id"),
    packetId: requireString(i.packet_id, "packet_id"),
    sectionId: requireString(i.section_id, "section_id"),
    itemType: i.item_type,
    title: requireString(i.title, "title"),
    description: i.description,
    severity: i.severity,
    sourceType: i.source_type,
    sourceId: i.source_id,
    reviewerStatus: requireString(i.reviewer_status, "reviewer_status"),
    reviewerNote: i.reviewer_note,
    requiresHumanReview: i.requires_human_review,
    displayOrder: i.display_order,
    evidenceLinks: (i.evidence_links ?? []).map(mapEvidenceLink),
  };
}

export function mapPacketSection(s: ApiPacketSection): ReviewPacketSection {
  return {
    sectionId: requireString(s.section_id, "section_id"),
    packetId: requireString(s.packet_id, "packet_id"),
    title: requireString(s.title, "title"),
    sectionType: s.section_type,
    displayOrder: s.display_order,
    summary: s.summary,
    status: s.status,
    requiresHumanReview: s.requires_human_review,
    items: (s.items ?? []).map(mapPacketItem),
  };
}

export function mapReviewPacket(p: ApiReviewPacket): ReviewPacket {
  return {
    packetId: requireString(p.packet_id, "packet_id"),
    projectId: requireString(p.project_id, "project_id"),
    title: requireString(p.title, "title"),
    packetType: requireString(p.packet_type, "packet_type"),
    status: requireString(p.status, "status"),
    summary: p.summary,
    generatedFromPhase: p.generated_from_phase,
    createdBy: p.created_by,
    limitationsNote: p.limitations_note,
    createdAt: p.created_at,
    updatedAt: p.updated_at,
  };
}

export function mapReviewPacketDetail(p: ApiReviewPacket): ReviewPacketDetail {
  return {
    ...mapReviewPacket(p),
    sections: (p.sections ?? []).map(mapPacketSection),
  };
}

export function mapPacketAction(a: ApiPacketAction): ReviewPacketReviewerAction {
  return {
    actionId: a.action_id,
    packetId: a.packet_id,
    itemId: a.item_id,
    actionType: a.action_type,
    reviewerNote: a.reviewer_note,
    previousStatus: a.previous_status,
    newStatus: a.new_status,
    reviewerName: a.reviewer_name,
    createdAt: a.created_at,
  };
}
