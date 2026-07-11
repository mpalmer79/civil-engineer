import {
  API_BASE_URL,
  PROJECT_ID,
  apiGetMapped,
  authHeaders,
  requireArray,
  requireString,
  type ApiResult,
} from "./client";

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

function mapItem(i: ApiItem): ResponsePackageItem {
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

function mapSection(s: ApiSection): ResponsePackageSection {
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

function mapAttachment(a: ApiAttachment): ResponsePackageAttachment {
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

function mapPackage(p: ApiPackage): ResponsePackage {
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

function mapPackageDetail(p: ApiPackage): ResponsePackageDetail {
  return {
    ...mapPackage(p),
    sections: (p.sections ?? []).map(mapSection),
    attachments: (p.attachments ?? []).map(mapAttachment),
  };
}

function mapAction(a: ApiAction): ResponsePackageAction {
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

export async function getResponsePackages(): Promise<
  ApiResult<ResponsePackage[]>
> {
  return apiGetMapped<ApiPackage[], ResponsePackage[]>(
    `/api/v1/projects/${PROJECT_ID}/response-packages`,
    (data) =>
      requireArray(data, "response_packages").map((p) =>
        mapPackage(p as ApiPackage),
      ),
  );
}

export async function getResponsePackage(
  responsePackageId: string,
): Promise<ApiResult<ResponsePackageDetail>> {
  return apiGetMapped<ApiPackage, ResponsePackageDetail>(
    `/api/v1/response-packages/${responsePackageId}`,
    mapPackageDetail,
  );
}

export async function getResponsePackageAttachments(
  responsePackageId: string,
): Promise<ApiResult<ResponsePackageAttachment[]>> {
  return apiGetMapped<ApiAttachment[], ResponsePackageAttachment[]>(
    `/api/v1/response-packages/${responsePackageId}/attachments`,
    (data) =>
      requireArray(data, "attachments").map((a) =>
        mapAttachment(a as ApiAttachment),
      ),
  );
}

export async function getResponsePackageHistory(
  responsePackageId: string,
): Promise<ApiResult<ResponsePackageHistory>> {
  return apiGetMapped<
    {
      response_package_id: string;
      project_id: string;
      actions: ApiAction[];
      note: string;
    },
    ResponsePackageHistory
  >(`/api/v1/response-packages/${responsePackageId}/history`, (data) => ({
    responsePackageId: requireString(
      data.response_package_id,
      "response_package_id",
    ),
    projectId: requireString(data.project_id, "project_id"),
    actions: (data.actions ?? []).map(mapAction),
    note: data.note,
  }));
}

export async function getResponsePackageSummary(
  responsePackageId: string,
): Promise<ApiResult<ResponsePackageSummary>> {
  return apiGetMapped<
    {
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
    },
    ResponsePackageSummary
  >(`/api/v1/response-packages/${responsePackageId}/summary`, (data) => ({
    responsePackageId: requireString(
      data.response_package_id,
      "response_package_id",
    ),
    projectId: requireString(data.project_id, "project_id"),
    status: requireString(data.status, "status"),
    audienceType: data.audience_type,
    totalSections: data.total_sections,
    totalItems: data.total_items,
    totalAttachments: data.total_attachments,
    totalEvidenceLinks: data.total_evidence_links,
    itemsBySectionType: data.items_by_section_type,
    itemsByStatus: data.items_by_status,
    itemsBySeverity: data.items_by_severity,
    itemsRequiringHumanReview: data.items_requiring_human_review,
  }));
}

export async function getResponsePackagePrintView(
  responsePackageId: string,
): Promise<ApiResult<ResponsePackagePrintView>> {
  return apiGetMapped<
    {
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
    },
    ResponsePackagePrintView
  >(`/api/v1/response-packages/${responsePackageId}/print-view`, (data) => ({
    responsePackageId: requireString(
      data.response_package_id,
      "response_package_id",
    ),
    projectId: requireString(data.project_id, "project_id"),
    title: requireString(data.title, "title"),
    audienceType: data.audience_type,
    status: requireString(data.status, "status"),
    summary: data.summary,
    draftIntro: data.draft_intro,
    draftClosing: data.draft_closing,
    createdBy: data.created_by,
    createdAt: data.created_at,
    limitationsNote: data.limitations_note,
    externalCommunicationBoundary: data.external_communication_boundary,
    draftNotice: data.draft_notice,
    sections: requireArray(data.sections, "sections").map((raw) => {
      const s = raw as {
        title: string;
        section_type: string;
        summary: string;
        items: ApiItem[];
      };
      return {
        title: requireString(s.title, "sections[].title"),
        sectionType: s.section_type,
        summary: s.summary,
        items: (s.items ?? []).map(mapItem),
      };
    }),
    attachments: (data.attachments ?? []).map(mapAttachment),
    signoffChecklist: (data.signoff_checklist ?? []).map((c) => ({
      label: c.label,
      detail: c.detail,
      confirmed: c.confirmed,
    })),
  }));
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
      { method: "POST", headers: authHeaders(), cache: "no-store" },
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
      headers: authHeaders({ "Content-Type": "application/json" }),
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
