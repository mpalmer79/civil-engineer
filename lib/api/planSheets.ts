import {
  API_BASE_URL,
  PROJECT_ID,
  apiGetMapped,
  authHeaders,
  requireArray,
  requireRecord,
  requireString,
  type ApiResult,
} from "./client";
import {
  mapCadMetadata,
  mapPlanConsistencyFinding,
  mapPlanReference,
  type ApiCadMetadata,
  type ApiPlanConsistencyFinding,
  type ApiPlanReference,
  type CadMetadata,
  type PlanConsistencyFinding,
  type PlanReference,
} from "./cad";

// Phase 6: plan sheets.
//
// Phase 6 data is backend-canonical. The frontend does not duplicate the plan
// set or CAD metadata. Read calls return a typed ApiResult so callers can
// render explicit failure states instead of stale or simulated data.

export type PlanSheet = {
  sheetId: string;
  projectId: string;
  sheetNumber: string;
  sheetTitle: string;
  discipline: string;
  revision: string;
  revisionDate: string | null;
  status: string;
  fileName: string | null;
  sheetPurpose: string;
  relatedDocuments: string[];
  relatedChecklistItems: string[];
  relatedFindings: string[];
};

export type PlanSheetSummary = {
  projectId: string;
  totalSheets: number;
  presentSheets: number;
  missingOrReferencedNotIncluded: number;
  needsReviewerConfirmation: number;
  sheetsWithRelatedFindings: number;
  cadMetadataRecords: number;
  sheetsByDiscipline: Record<string, number>;
  missingSheetIds: string[];
};

type ApiPlanSheet = {
  sheet_id: string;
  project_id: string;
  sheet_number: string;
  sheet_title: string;
  discipline: string;
  revision: string;
  revision_date: string | null;
  status: string;
  file_name: string | null;
  sheet_purpose: string;
  related_documents: string[];
  related_checklist_items: string[];
  related_findings: string[];
};

type ApiPlanSheetSummary = {
  project_id: string;
  total_sheets: number;
  present_sheets: number;
  missing_or_referenced_not_included: number;
  needs_reviewer_confirmation: number;
  sheets_with_related_findings: number;
  cad_metadata_records: number;
  sheets_by_discipline: Record<string, number>;
  missing_sheet_ids: string[];
};

function mapPlanSheet(s: ApiPlanSheet): PlanSheet {
  return {
    sheetId: requireString(s.sheet_id, "sheet_id"),
    projectId: requireString(s.project_id, "project_id"),
    sheetNumber: requireString(s.sheet_number, "sheet_number"),
    sheetTitle: s.sheet_title,
    discipline: s.discipline,
    revision: s.revision,
    revisionDate: s.revision_date,
    status: s.status,
    fileName: s.file_name,
    sheetPurpose: s.sheet_purpose,
    relatedDocuments: s.related_documents,
    relatedChecklistItems: s.related_checklist_items,
    relatedFindings: s.related_findings,
  };
}

function mapPlanSheetSummary(s: ApiPlanSheetSummary): PlanSheetSummary {
  return {
    projectId: requireString(s.project_id, "project_id"),
    totalSheets: s.total_sheets,
    presentSheets: s.present_sheets,
    missingOrReferencedNotIncluded: s.missing_or_referenced_not_included,
    needsReviewerConfirmation: s.needs_reviewer_confirmation,
    sheetsWithRelatedFindings: s.sheets_with_related_findings,
    cadMetadataRecords: s.cad_metadata_records,
    sheetsByDiscipline: s.sheets_by_discipline,
    missingSheetIds: s.missing_sheet_ids,
  };
}

export async function getPlanSheets(
  projectId: string = PROJECT_ID,
): Promise<ApiResult<PlanSheet[]>> {
  return apiGetMapped<ApiPlanSheet[], PlanSheet[]>(
    `/api/v1/projects/${projectId}/plan-sheets`,
    (data) =>
      requireArray(data, "plan_sheets").map((s) =>
        mapPlanSheet(s as ApiPlanSheet),
      ),
  );
}

export async function getPlanSheetSummary(
  projectId: string = PROJECT_ID,
): Promise<ApiResult<PlanSheetSummary>> {
  return apiGetMapped<ApiPlanSheetSummary, PlanSheetSummary>(
    `/api/v1/projects/${projectId}/plan-sheets/summary`,
    mapPlanSheetSummary,
  );
}

// Phase 7: plan sheet viewer, sheet hotspots, and plan consistency review
// actions.
//
// Phase 7 data is backend-canonical, consistent with Phase 6. The frontend does
// not simulate hotspots or review actions. Read calls return a typed ApiResult
// with an explicit failure state, and the review action mutation returns a
// clear backend-required result.

export type PlanSheetHotspot = {
  hotspotId: string;
  projectId: string;
  sheetId: string;
  hotspotType: string;
  label: string;
  description: string;
  xPercent: number;
  yPercent: number;
  widthPercent: number;
  heightPercent: number;
  severity: string;
  relatedPlanReferenceIds: string[];
  relatedCadMetadataIds: string[];
  relatedPlanFindingIds: string[];
  relatedDocumentIds: string[];
  relatedChecklistItemIds: string[];
  reviewNote: string | null;
  requiresHumanReview: boolean;
};

export type SheetViewerContext = {
  sheet: PlanSheet;
  hotspots: PlanSheetHotspot[];
  cadMetadata: CadMetadata[];
  planReferences: PlanReference[];
  planConsistencyFindings: PlanConsistencyFinding[];
  previewNote: string;
};

export type PlanConsistencyReviewAction = {
  reviewActionId: string;
  planFindingId: string;
  projectId: string;
  reviewerName: string;
  action: string;
  reviewerNote: string;
  previousStatus: string;
  newStatus: string;
  createdAt: string;
};

export type PlanReviewActionInput = {
  action: string;
  reviewerName: string;
  reviewerNote: string;
};

export type PlanReviewActionResult = {
  ok: boolean;
  status: number;
  backendReachable: boolean;
  action?: PlanConsistencyReviewAction;
  finding?: PlanConsistencyFinding;
  error?: string;
};

type ApiPlanSheetHotspot = {
  hotspot_id: string;
  project_id: string;
  sheet_id: string;
  hotspot_type: string;
  label: string;
  description: string;
  x_percent: number;
  y_percent: number;
  width_percent: number;
  height_percent: number;
  severity: string;
  related_plan_reference_ids: string[];
  related_cad_metadata_ids: string[];
  related_plan_finding_ids: string[];
  related_document_ids: string[];
  related_checklist_item_ids: string[];
  review_note: string | null;
  requires_human_review: boolean;
};

type ApiSheetViewerContext = {
  sheet: ApiPlanSheet;
  hotspots: ApiPlanSheetHotspot[];
  cad_metadata: ApiCadMetadata[];
  plan_references: ApiPlanReference[];
  plan_consistency_findings: ApiPlanConsistencyFinding[];
  preview_note: string;
};

type ApiPlanReviewAction = {
  review_action_id: string;
  plan_finding_id: string;
  project_id: string;
  reviewer_name: string;
  action: string;
  reviewer_note: string;
  previous_status: string;
  new_status: string;
  created_at: string;
};

function mapSheetHotspot(h: ApiPlanSheetHotspot): PlanSheetHotspot {
  return {
    hotspotId: requireString(h.hotspot_id, "hotspot_id"),
    projectId: requireString(h.project_id, "project_id"),
    sheetId: requireString(h.sheet_id, "sheet_id"),
    hotspotType: h.hotspot_type,
    label: requireString(h.label, "label"),
    description: h.description,
    xPercent: h.x_percent,
    yPercent: h.y_percent,
    widthPercent: h.width_percent,
    heightPercent: h.height_percent,
    severity: h.severity,
    relatedPlanReferenceIds: h.related_plan_reference_ids,
    relatedCadMetadataIds: h.related_cad_metadata_ids,
    relatedPlanFindingIds: h.related_plan_finding_ids,
    relatedDocumentIds: h.related_document_ids,
    relatedChecklistItemIds: h.related_checklist_item_ids,
    reviewNote: h.review_note,
    requiresHumanReview: h.requires_human_review,
  };
}

function mapPlanReviewAction(
  a: ApiPlanReviewAction,
): PlanConsistencyReviewAction {
  return {
    reviewActionId: requireString(a.review_action_id, "review_action_id"),
    planFindingId: requireString(a.plan_finding_id, "plan_finding_id"),
    projectId: requireString(a.project_id, "project_id"),
    reviewerName: a.reviewer_name,
    action: a.action,
    reviewerNote: a.reviewer_note,
    previousStatus: a.previous_status,
    newStatus: a.new_status,
    createdAt: a.created_at,
  };
}

export async function getSheetHotspots(
  projectId: string = PROJECT_ID,
): Promise<ApiResult<PlanSheetHotspot[]>> {
  return apiGetMapped<ApiPlanSheetHotspot[], PlanSheetHotspot[]>(
    `/api/v1/projects/${projectId}/sheet-hotspots`,
    (data) =>
      requireArray(data, "sheet_hotspots").map((h) =>
        mapSheetHotspot(h as ApiPlanSheetHotspot),
      ),
  );
}

export async function getSheetHotspotsForSheet(
  sheetId: string,
): Promise<ApiResult<PlanSheetHotspot[]>> {
  return apiGetMapped<ApiPlanSheetHotspot[], PlanSheetHotspot[]>(
    `/api/v1/plan-sheets/${sheetId}/sheet-hotspots`,
    (data) =>
      requireArray(data, "sheet_hotspots").map((h) =>
        mapSheetHotspot(h as ApiPlanSheetHotspot),
      ),
  );
}

export async function getSheetViewerContext(
  sheetId: string,
): Promise<ApiResult<SheetViewerContext>> {
  return apiGetMapped<ApiSheetViewerContext, SheetViewerContext>(
    `/api/v1/plan-sheets/${sheetId}/viewer-context`,
    (data) => ({
      sheet: mapPlanSheet(requireRecord(data.sheet, "sheet") as ApiPlanSheet),
      hotspots: requireArray(data.hotspots, "hotspots").map((h) =>
        mapSheetHotspot(h as ApiPlanSheetHotspot),
      ),
      cadMetadata: requireArray(data.cad_metadata, "cad_metadata").map((m) =>
        mapCadMetadata(m as ApiCadMetadata),
      ),
      planReferences: requireArray(data.plan_references, "plan_references").map(
        (r) => mapPlanReference(r as ApiPlanReference),
      ),
      planConsistencyFindings: requireArray(
        data.plan_consistency_findings,
        "plan_consistency_findings",
      ).map((f) => mapPlanConsistencyFinding(f as ApiPlanConsistencyFinding)),
      previewNote: data.preview_note,
    }),
  );
}

export async function getPlanConsistencyReviewActions(
  planFindingId?: string,
  projectId: string = PROJECT_ID,
): Promise<ApiResult<PlanConsistencyReviewAction[]>> {
  const query = planFindingId
    ? `?plan_finding_id=${encodeURIComponent(planFindingId)}`
    : "";
  return apiGetMapped<ApiPlanReviewAction[], PlanConsistencyReviewAction[]>(
    `/api/v1/projects/${projectId}/plan-consistency-review-actions${query}`,
    (data) =>
      requireArray(data, "plan_consistency_review_actions").map((a) =>
        mapPlanReviewAction(a as ApiPlanReviewAction),
      ),
  );
}

export async function createPlanConsistencyReviewAction(
  planFindingId: string,
  input: PlanReviewActionInput,
): Promise<PlanReviewActionResult> {
  try {
    const res = await fetch(
      `${API_BASE_URL}/api/v1/plan-consistency-findings/${planFindingId}/review-actions`,
      {
        method: "POST",
        headers: authHeaders({ "Content-Type": "application/json" }),
        body: JSON.stringify({
          action: input.action,
          reviewer_name: input.reviewerName,
          reviewer_note: input.reviewerNote,
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
      action: ApiPlanReviewAction;
      finding: ApiPlanConsistencyFinding;
    };
    return {
      ok: true,
      status: res.status,
      backendReachable: true,
      action: mapPlanReviewAction(body.action),
      finding: mapPlanConsistencyFinding(body.finding),
    };
  } catch {
    return {
      ok: false,
      status: 0,
      backendReachable: false,
      error:
        "The backend is not reachable. Start the API to record a plan review action. Review actions are not simulated in the browser.",
    };
  }
}
