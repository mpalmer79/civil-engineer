import { API_BASE_URL, PROJECT_ID, safeFetch } from "./client";

// Phase 10: external review response package.
//
// Phase 10 data is backend-canonical. The frontend does not simulate response
// package data. Read calls return null or empty results when the backend is
// unavailable, and the mutating calls return a clear backend-required result.

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

type ApiEvidenceLink = {
  evidence_link_id: string;
  response_package_id: string;
  response_item_id: string;
  evidence_type: string;
  evidence_id: string;
  relationship: string;
  label: string;
  description: string | null;
};

type ApiItem = {
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

type ApiSection = {
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

type ApiAttachment = {
  attachment_id: string;
  response_package_id: string;
  label: string;
  attachment_type: string;
  source_type: string;
  source_id: string | null;
  included: boolean;
  description: string | null;
};

type ApiPackage = {
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

type ApiAction = {
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

function mapEvidenceLink(l: ApiEvidenceLink): ResponsePackageEvidenceLink {
  return {
    evidenceLinkId: l.evidence_link_id,
    responsePackageId: l.response_package_id,
    responseItemId: l.response_item_id,
    evidenceType: l.evidence_type,
    evidenceId: l.evidence_id,
    relationship: l.relationship,
    label: l.label,
    description: l.description,
  };
}

function mapItem(i: ApiItem): ResponsePackageItem {
  return {
    itemId: i.item_id,
    responsePackageId: i.response_package_id,
    sectionId: i.section_id,
    workflowItemId: i.workflow_item_id,
    packetItemId: i.packet_item_id,
    title: i.title,
    draftText: i.draft_text,
    reviewerNote: i.reviewer_note,
    severity: i.severity,
    status: i.status,
    sourceType: i.source_type,
    sourceId: i.source_id,
    assignedRole: i.assigned_role,
    requiresHumanReview: i.requires_human_review,
    displayOrder: i.display_order,
    evidenceLinks: (i.evidence_links ?? []).map(mapEvidenceLink),
  };
}

function mapSection(s: ApiSection): ResponsePackageSection {
  return {
    sectionId: s.section_id,
    responsePackageId: s.response_package_id,
    title: s.title,
    sectionType: s.section_type,
    displayOrder: s.display_order,
    summary: s.summary,
    status: s.status,
    requiresHumanReview: s.requires_human_review,
    items: (s.items ?? []).map(mapItem),
  };
}

function mapAttachment(a: ApiAttachment): ResponsePackageAttachment {
  return {
    attachmentId: a.attachment_id,
    responsePackageId: a.response_package_id,
    label: a.label,
    attachmentType: a.attachment_type,
    sourceType: a.source_type,
    sourceId: a.source_id,
    included: a.included,
    description: a.description,
  };
}

function mapPackage(p: ApiPackage): ResponsePackage {
  return {
    responsePackageId: p.response_package_id,
    projectId: p.project_id,
    sourcePacketId: p.source_packet_id,
    title: p.title,
    audienceType: p.audience_type,
    status: p.status,
    summary: p.summary,
    draftIntro: p.draft_intro,
    draftClosing: p.draft_closing,
    limitationsNote: p.limitations_note,
    createdBy: p.created_by,
    createdAt: p.created_at,
    updatedAt: p.updated_at,
  };
}

function mapPackageDetail(p: ApiPackage): ResponsePackageDetail {
  return {
    ...mapPackage(p),
    sections: (p.sections ?? []).map(mapSection),
    attachments: (p.attachments ?? []).map(mapAttachment),
  };
}

function mapAction(a: ApiAction): ResponsePackageAction {
  return {
    actionId: a.action_id,
    responsePackageId: a.response_package_id,
    responseItemId: a.response_item_id,
    actionType: a.action_type,
    previousStatus: a.previous_status,
    newStatus: a.new_status,
    reviewerNote: a.reviewer_note,
    reviewerName: a.reviewer_name,
    createdAt: a.created_at,
  };
}

export async function getResponsePackages(): Promise<ResponsePackage[]> {
  const data = await safeFetch<ApiPackage[]>(
    `/api/v1/projects/${PROJECT_ID}/response-packages`,
  );
  return data ? data.map(mapPackage) : [];
}

export async function getResponsePackage(
  responsePackageId: string,
): Promise<ResponsePackageDetail | null> {
  const data = await safeFetch<ApiPackage>(
    `/api/v1/response-packages/${responsePackageId}`,
  );
  return data ? mapPackageDetail(data) : null;
}

export async function getResponsePackageAttachments(
  responsePackageId: string,
): Promise<ResponsePackageAttachment[]> {
  const data = await safeFetch<ApiAttachment[]>(
    `/api/v1/response-packages/${responsePackageId}/attachments`,
  );
  return data ? data.map(mapAttachment) : [];
}

export async function getResponsePackageHistory(
  responsePackageId: string,
): Promise<ResponsePackageHistory | null> {
  const data = await safeFetch<{
    response_package_id: string;
    project_id: string;
    actions: ApiAction[];
    note: string;
  }>(`/api/v1/response-packages/${responsePackageId}/history`);
  if (!data) return null;
  return {
    responsePackageId: data.response_package_id,
    projectId: data.project_id,
    actions: (data.actions ?? []).map(mapAction),
    note: data.note,
  };
}

export async function getResponsePackageSummary(
  responsePackageId: string,
): Promise<ResponsePackageSummary | null> {
  const data = await safeFetch<{
    response_package_id: string;
    project_id: string;
    status: string;
    audience_type: string;
    total_sections: number;
    total_items: number;
    total_attachments: number;
    total_evidence_links: number;
    items_by_section_type: Record<string, number>;
    items_by_status: Record<string, number>;
    items_by_severity: Record<string, number>;
    items_requiring_human_review: number;
  }>(`/api/v1/response-packages/${responsePackageId}/summary`);
  if (!data) return null;
  return {
    responsePackageId: data.response_package_id,
    projectId: data.project_id,
    status: data.status,
    audienceType: data.audience_type,
    totalSections: data.total_sections,
    totalItems: data.total_items,
    totalAttachments: data.total_attachments,
    totalEvidenceLinks: data.total_evidence_links,
    itemsBySectionType: data.items_by_section_type,
    itemsByStatus: data.items_by_status,
    itemsBySeverity: data.items_by_severity,
    itemsRequiringHumanReview: data.items_requiring_human_review,
  };
}

export async function getResponsePackagePrintView(
  responsePackageId: string,
): Promise<ResponsePackagePrintView | null> {
  const data = await safeFetch<{
    response_package_id: string;
    project_id: string;
    title: string;
    audience_type: string;
    status: string;
    summary: string;
    draft_intro: string;
    draft_closing: string;
    created_by: string;
    created_at: string;
    limitations_note: string;
    external_communication_boundary: string;
    draft_notice: string;
    sections: {
      title: string;
      section_type: string;
      summary: string;
      items: ApiItem[];
    }[];
    attachments: ApiAttachment[];
    signoff_checklist: {
      label: string;
      detail: string;
      confirmed: boolean;
    }[];
  }>(`/api/v1/response-packages/${responsePackageId}/print-view`);
  if (!data) return null;
  return {
    responsePackageId: data.response_package_id,
    projectId: data.project_id,
    title: data.title,
    audienceType: data.audience_type,
    status: data.status,
    summary: data.summary,
    draftIntro: data.draft_intro,
    draftClosing: data.draft_closing,
    createdBy: data.created_by,
    createdAt: data.created_at,
    limitationsNote: data.limitations_note,
    externalCommunicationBoundary: data.external_communication_boundary,
    draftNotice: data.draft_notice,
    sections: data.sections.map((s) => ({
      title: s.title,
      sectionType: s.section_type,
      summary: s.summary,
      items: (s.items ?? []).map(mapItem),
    })),
    attachments: (data.attachments ?? []).map(mapAttachment),
    signoffChecklist: (data.signoff_checklist ?? []).map((c) => ({
      label: c.label,
      detail: c.detail,
      confirmed: c.confirmed,
    })),
  };
}

export async function generateResponsePackage(): Promise<{
  ok: boolean;
  backendReachable: boolean;
  package?: ResponsePackageDetail;
  error?: string;
}> {
  try {
    const res = await fetch(
      `${API_BASE_URL}/api/v1/projects/${PROJECT_ID}/response-packages/generate`,
      { method: "POST", cache: "no-store" },
    );
    if (!res.ok) {
      let detail = `Request failed (${res.status}).`;
      try {
        const body = (await res.json()) as { detail?: string };
        if (body.detail) detail = body.detail;
      } catch {
        // Keep generic message.
      }
      return { ok: false, backendReachable: true, error: detail };
    }
    return {
      ok: true,
      backendReachable: true,
      package: mapPackageDetail((await res.json()) as ApiPackage),
    };
  } catch {
    return {
      ok: false,
      backendReachable: false,
      error:
        "The backend is not reachable. Start the API to generate a response package. Response package data is not simulated in the browser.",
    };
  }
}

async function mutate(
  path: string,
  method: "POST" | "PATCH",
  body: Record<string, unknown>,
  unreachableMessage: string,
): Promise<{ ok: boolean; status: number; backendReachable: boolean; data?: unknown; error?: string }> {
  try {
    const res = await fetch(`${API_BASE_URL}${path}`, {
      method,
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
      cache: "no-store",
    });
    if (!res.ok) {
      let detail = `Request failed (${res.status}).`;
      try {
        const errBody = (await res.json()) as { detail?: string };
        if (errBody.detail) detail = errBody.detail;
      } catch {
        // Keep generic message.
      }
      return { ok: false, status: res.status, backendReachable: true, error: detail };
    }
    return { ok: true, status: res.status, backendReachable: true, data: await res.json() };
  } catch {
    return { ok: false, status: 0, backendReachable: false, error: unreachableMessage };
  }
}

export async function updateResponsePackageStatus(
  responsePackageId: string,
  newStatus: string,
  reviewerNote?: string,
  reviewerName?: string,
): Promise<ResponsePackageMutationResult> {
  const result = await mutate(
    `/api/v1/response-packages/${responsePackageId}/status`,
    "PATCH",
    { new_status: newStatus, reviewer_note: reviewerNote, reviewer_name: reviewerName },
    "The backend is not reachable. Start the API to update the package status.",
  );
  return {
    ok: result.ok,
    status: result.status,
    backendReachable: result.backendReachable,
    package: result.data ? mapPackage(result.data as ApiPackage) : undefined,
    error: result.error,
  };
}

export async function updateResponseItemStatus(
  responsePackageId: string,
  responseItemId: string,
  newStatus: string,
  reviewerNote?: string,
  reviewerName?: string,
): Promise<ResponsePackageMutationResult> {
  const result = await mutate(
    `/api/v1/response-packages/${responsePackageId}/items/${responseItemId}/status`,
    "PATCH",
    { new_status: newStatus, reviewer_note: reviewerNote, reviewer_name: reviewerName },
    "The backend is not reachable. Start the API to update the item status.",
  );
  return {
    ok: result.ok,
    status: result.status,
    backendReachable: result.backendReachable,
    item: result.data ? mapItem(result.data as ApiItem) : undefined,
    error: result.error,
  };
}

export async function updateResponseItemDraftText(
  responsePackageId: string,
  responseItemId: string,
  draftText: string,
  reviewerNote?: string,
  reviewerName?: string,
): Promise<ResponsePackageMutationResult> {
  const result = await mutate(
    `/api/v1/response-packages/${responsePackageId}/items/${responseItemId}/draft-text`,
    "PATCH",
    { draft_text: draftText, reviewer_note: reviewerNote, reviewer_name: reviewerName },
    "The backend is not reachable. Start the API to edit the draft text.",
  );
  return {
    ok: result.ok,
    status: result.status,
    backendReachable: result.backendReachable,
    item: result.data ? mapItem(result.data as ApiItem) : undefined,
    error: result.error,
  };
}

export async function addResponsePackageNote(
  responsePackageId: string,
  responseItemId: string,
  reviewerNote: string,
  reviewerName: string,
): Promise<ResponsePackageMutationResult> {
  const result = await mutate(
    `/api/v1/response-packages/${responsePackageId}/items/${responseItemId}/notes`,
    "POST",
    { reviewer_note: reviewerNote, reviewer_name: reviewerName },
    "The backend is not reachable. Start the API to add a reviewer note.",
  );
  return {
    ok: result.ok,
    status: result.status,
    backendReachable: result.backendReachable,
    action: result.data ? mapAction(result.data as ApiAction) : undefined,
    error: result.error,
  };
}
