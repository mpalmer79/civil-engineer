import {
  PROJECT_ID,
  apiFetch,
  type ApiResult,
} from "../client";
import {
  mapPacketItem,
  mapReviewPacket,
  mapReviewPacketDetail,
  type ApiPacketItem,
  type ApiReviewPacket,
} from "./mappers";
import type {
  ReviewPacket,
  ReviewPacketDetail,
  ReviewPacketPrintView,
  ReviewPacketSummary,
  ReviewPacketTraceability,
} from "./types";

// Read calls return a typed ApiResult that preserves the status and failure
// category.

export async function getReviewPackets(
  projectId: string = PROJECT_ID,
): Promise<ApiResult<ReviewPacket[]>> {
  const result = await apiFetch<ApiReviewPacket[]>(
    `/api/v1/projects/${projectId}/review-packets`,
  );
  if (!result.ok) return result;
  const data = result.data;
  return { ...result, data: data.map(mapReviewPacket) };
}

export async function getReviewPacket(
  packetId: string,
): Promise<ApiResult<ReviewPacketDetail>> {
  const result = await apiFetch<ApiReviewPacket>(
    `/api/v1/review-packets/${packetId}`,
  );
  if (!result.ok) return result;
  const data = result.data;
  return { ...result, data: mapReviewPacketDetail(data) };
}

export async function getReviewPacketTraceability(
  packetId: string,
): Promise<ApiResult<ReviewPacketTraceability>> {
  const result = await apiFetch<{
    packet_id: string;
    project_id: string;
    total_rows: number;
    rows: {
      section_type: string;
      item_id: string;
      item_title: string;
      item_type: string;
      source_type: string;
      source_id: string | null;
      evidence_type: string;
      evidence_id: string;
      relationship: string;
      label: string;
    }[];
    note: string;
  }>(`/api/v1/review-packets/${packetId}/traceability`);
  if (!result.ok) return result;
  const data = result.data;
  return {
    ...result,
    data: {
    packetId: data.packet_id,
    projectId: data.project_id,
    totalRows: data.total_rows,
    rows: data.rows.map((r) => ({
      sectionType: r.section_type,
      itemId: r.item_id,
      itemTitle: r.item_title,
      itemType: r.item_type,
      sourceType: r.source_type,
      sourceId: r.source_id,
      evidenceType: r.evidence_type,
      evidenceId: r.evidence_id,
      relationship: r.relationship,
      label: r.label,
    })),
    note: data.note,
    },
  };
}

export async function getReviewPacketPrintView(
  packetId: string,
): Promise<ApiResult<ReviewPacketPrintView>> {
  const result = await apiFetch<{
    packet_id: string;
    project_id: string;
    title: string;
    packet_type: string;
    status: string;
    summary: string;
    generated_from_phase: string;
    created_by: string;
    created_at: string;
    limitations_note: string;
    professional_limitations: string;
    draft_notice: string;
    sections: {
      title: string;
      section_type: string;
      summary: string;
      items: ApiPacketItem[];
    }[];
    traceability_review_rows?: {
      traceability_row_key: string;
      checklist_title: string | null;
      checklist_requirement: string | null;
      relationship_type: string;
      review_action_type: string | null;
      reviewer_note: string | null;
      created_by: string | null;
      requires_reviewer_confirmation: boolean;
    }[];
    traceability_note?: string | null;
  }>(`/api/v1/review-packets/${packetId}/print-view`);
  if (!result.ok) return result;
  const data = result.data;
  return {
    ...result,
    data: {
    packetId: data.packet_id,
    projectId: data.project_id,
    title: data.title,
    packetType: data.packet_type,
    status: data.status,
    summary: data.summary,
    generatedFromPhase: data.generated_from_phase,
    createdBy: data.created_by,
    createdAt: data.created_at,
    limitationsNote: data.limitations_note,
    professionalLimitations: data.professional_limitations,
    draftNotice: data.draft_notice,
    sections: data.sections.map((s) => ({
      title: s.title,
      sectionType: s.section_type,
      summary: s.summary,
      items: (s.items ?? []).map(mapPacketItem),
    })),
    traceabilityReviewRows: (data.traceability_review_rows ?? []).map((r) => ({
      traceabilityRowKey: r.traceability_row_key,
      checklistTitle: r.checklist_title,
      checklistRequirement: r.checklist_requirement,
      relationshipType: r.relationship_type,
      reviewActionType: r.review_action_type,
      reviewerNote: r.reviewer_note,
      createdBy: r.created_by,
      requiresReviewerConfirmation: r.requires_reviewer_confirmation,
    })),
    traceabilityNote: data.traceability_note ?? null,
    },
  };
}

export async function getReviewPacketSummary(
  packetId: string,
): Promise<ApiResult<ReviewPacketSummary>> {
  const result = await apiFetch<{
    packet_id: string;
    project_id: string;
    status: string;
    total_sections: number;
    total_items: number;
    total_evidence_links: number;
    items_by_section_type: Record<string, number>;
    items_by_status: Record<string, number>;
    items_by_severity: Record<string, number>;
    items_requiring_human_review: number;
  }>(`/api/v1/review-packets/${packetId}/summary`);
  if (!result.ok) return result;
  const data = result.data;
  return {
    ...result,
    data: {
    packetId: data.packet_id,
    projectId: data.project_id,
    status: data.status,
    totalSections: data.total_sections,
    totalItems: data.total_items,
    totalEvidenceLinks: data.total_evidence_links,
    itemsBySectionType: data.items_by_section_type,
    itemsByStatus: data.items_by_status,
    itemsBySeverity: data.items_by_severity,
    itemsRequiringHumanReview: data.items_requiring_human_review,
    },
  };
}
