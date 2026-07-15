import {
  PROJECT_ID,
  apiGetMapped,
  requireArray,
  requireString,
  type ApiResult,
} from "../client";
import {
  mapAction,
  mapAttachment,
  mapItem,
  mapPackage,
  mapPackageDetail,
  type ApiAction,
  type ApiAttachment,
  type ApiItem,
  type ApiPackage,
} from "./mappers";
import type {
  ResponsePackage,
  ResponsePackageAttachment,
  ResponsePackageDetail,
  ResponsePackageHistory,
  ResponsePackagePrintView,
  ResponsePackageSummary,
} from "./types";

// Read calls return a typed ApiResult that preserves the status and failure
// category.

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
