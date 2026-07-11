import {
  API_BASE_URL,
  PROJECT_ID,
  apiGetMapped,
  authHeaders,
  requireArray,
  requireString,
  type ApiResult,
} from "./client";

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

type ApiEvidenceLink = {
  evidence_link_id: string;
  packet_id: string;
  item_id: string;
  evidence_type: string;
  evidence_id: string;
  relationship: string;
  label: string;
  description: string | null;
};

type ApiPacketItem = {
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

type ApiPacketSection = {
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

type ApiReviewPacket = {
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

function mapEvidenceLink(l: ApiEvidenceLink): ReviewPacketEvidenceLink {
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

function mapPacketItem(i: ApiPacketItem): ReviewPacketItem {
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

function mapPacketSection(s: ApiPacketSection): ReviewPacketSection {
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

function mapReviewPacket(p: ApiReviewPacket): ReviewPacket {
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

function mapReviewPacketDetail(p: ApiReviewPacket): ReviewPacketDetail {
  return {
    ...mapReviewPacket(p),
    sections: (p.sections ?? []).map(mapPacketSection),
  };
}

type ApiPacketAction = {
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

function mapPacketAction(a: ApiPacketAction): ReviewPacketReviewerAction {
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

export async function getReviewPackets(
  projectId: string = PROJECT_ID,
): Promise<ReviewPacket[]> {
  const data = await safeFetch<ApiReviewPacket[]>(
    `/api/v1/projects/${projectId}/review-packets`,
  );
  return data ? data.map(mapReviewPacket) : [];
}

export async function getReviewPacket(
  packetId: string,
): Promise<ReviewPacketDetail | null> {
  const data = await safeFetch<ApiReviewPacket>(
    `/api/v1/review-packets/${packetId}`,
  );
  return data ? mapReviewPacketDetail(data) : null;
}

export async function getReviewPacketTraceability(
  packetId: string,
): Promise<ReviewPacketTraceability | null> {
  const data = await safeFetch<{
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
  if (!data) return null;
  return {
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
  };
}

export async function getReviewPacketPrintView(
  packetId: string,
): Promise<ReviewPacketPrintView | null> {
  const data = await safeFetch<{
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
  if (!data) return null;
  return {
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
  };
}

export async function getReviewPacketSummary(
  packetId: string,
): Promise<ReviewPacketSummary | null> {
  const data = await safeFetch<{
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
  if (!data) return null;
  return {
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
  };
}

export async function generateReviewPacket(
  projectId: string = PROJECT_ID,
): Promise<{
  ok: boolean;
  backendReachable: boolean;
  packet?: ReviewPacketDetail;
  error?: string;
}> {
  try {
    const res = await fetch(
      `${API_BASE_URL}/api/v1/projects/${projectId}/review-packets/generate`,
      { method: "POST", headers: authHeaders(), cache: "no-store" },
    );
    if (!res.ok) {
      return {
        ok: false,
        backendReachable: true,
        error: `Request failed (${res.status}).`,
      };
    }
    return {
      ok: true,
      backendReachable: true,
      packet: mapReviewPacketDetail((await res.json()) as ApiReviewPacket),
    };
  } catch {
    return {
      ok: false,
      backendReachable: false,
      error:
        "The backend is not reachable. Start the API to generate a review packet. Packet data is not simulated in the browser.",
    };
  }
}

export async function createReviewPacketReviewerAction(
  packetId: string,
  itemId: string,
  input: ReviewPacketActionInput,
): Promise<ReviewPacketMutationResult> {
  try {
    const res = await fetch(
      `${API_BASE_URL}/api/v1/review-packets/${packetId}/items/${itemId}/review-actions`,
      {
        method: "POST",
        headers: authHeaders({ "Content-Type": "application/json" }),
        body: JSON.stringify({
          action_type: input.actionType,
          reviewer_note: input.reviewerNote,
          reviewer_name: input.reviewerName,
        }),
        cache: "no-store",
      },
    );
    if (!res.ok) {
      let detail = `Request failed (${res.status}).`;
      try {
        const body = (await res.json()) as { detail?: string };
        if (body.detail) detail = body.detail;
      } catch {
        // Keep generic message.
      }
      return { ok: false, status: res.status, backendReachable: true, error: detail };
    }
    const body = (await res.json()) as {
      action: ApiPacketAction;
      item: ApiPacketItem;
    };
    return {
      ok: true,
      status: res.status,
      backendReachable: true,
      action: mapPacketAction(body.action),
      item: mapPacketItem(body.item),
    };
  } catch {
    return {
      ok: false,
      status: 0,
      backendReachable: false,
      error:
        "The backend is not reachable. Start the API to record a reviewer action. Packet actions are not simulated in the browser.",
    };
  }
}

export async function updateReviewPacketItemStatus(
  packetId: string,
  itemId: string,
  newStatus: string,
  reviewerNote?: string,
  reviewerName?: string,
): Promise<ReviewPacketMutationResult> {
  try {
    const res = await fetch(
      `${API_BASE_URL}/api/v1/review-packets/${packetId}/items/${itemId}/status`,
      {
        method: "PATCH",
        headers: authHeaders({ "Content-Type": "application/json" }),
        body: JSON.stringify({
          new_status: newStatus,
          reviewer_note: reviewerNote,
          reviewer_name: reviewerName,
        }),
        cache: "no-store",
      },
    );
    if (!res.ok) {
      let detail = `Request failed (${res.status}).`;
      try {
        const body = (await res.json()) as { detail?: string };
        if (body.detail) detail = body.detail;
      } catch {
        // Keep generic message.
      }
      return { ok: false, status: res.status, backendReachable: true, error: detail };
    }
    return {
      ok: true,
      status: res.status,
      backendReachable: true,
      item: mapPacketItem((await res.json()) as ApiPacketItem),
    };
  } catch {
    return {
      ok: false,
      status: 0,
      backendReachable: false,
      error:
        "The backend is not reachable. Start the API to update a packet item status.",
    };
  }
}
