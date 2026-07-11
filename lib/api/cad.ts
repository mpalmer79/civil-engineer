import {
  API_BASE_URL,
  PROJECT_ID,
  apiGetMapped,
  authHeaders,
  requireArray,
  requireString,
  type ApiResult,
} from "./client";

// Phase 6: CAD-aware metadata, plan references, and plan consistency findings.
//
// Phase 6 data is backend-canonical. The frontend does not duplicate the plan
// set or CAD metadata. Read calls return a typed ApiResult so callers can
// render explicit failure states (sign-in required, forbidden, missing,
// unavailable) instead of stale or simulated data. The check mutation keeps
// its backend-required result shape.

export type CadMetadata = {
  cadMetadataId: string;
  projectId: string;
  sheetId: string | null;
  sourceType: string;
  entityType: string;
  entityLabel: string;
  layerName: string | null;
  discipline: string;
  relatedDocumentId: string | null;
  relatedChecklistItemId: string | null;
  relatedFindingId: string | null;
  notes: string | null;
};

export type PlanReference = {
  planReferenceId: string;
  projectId: string;
  sourceType: string;
  sourceId: string;
  targetType: string;
  targetId: string;
  referenceLabel: string;
  referenceContext: string;
  consistencyStatus: string;
  reviewNote: string | null;
};

export type PlanConsistencyFinding = {
  planFindingId: string;
  projectId: string;
  findingType: string;
  title: string;
  summary: string;
  riskLevel: string;
  status: string;
  relatedSheetIds: string[];
  relatedDocumentIds: string[];
  relatedChecklistItems: string[];
  relatedCadMetadataIds: string[];
  recommendedHumanAction: string;
};

export type PlanConsistencySummary = {
  projectId: string;
  totalSheets: number;
  missingSheetCount: number;
  cadMetadataRecords: number;
  totalPlanReferences: number;
  inconsistentReferences: number;
  planConsistencyFindings: number;
  conflictingLabelCount: number;
  missingReferencedSheetCount: number;
  missingPlanReferenceCount: number;
  unclearRevisionCount: number;
  requiresHumanReviewCount: number;
  findingsRequiringHumanReview: number;
};

export type PlanConsistencyCheckResult = {
  ok: boolean;
  status: number;
  backendReachable: boolean;
  summary?: PlanConsistencySummary;
  error?: string;
};

export type ApiCadMetadata = {
  cad_metadata_id: string;
  project_id: string;
  sheet_id: string | null;
  source_type: string;
  entity_type: string;
  entity_label: string;
  layer_name: string | null;
  discipline: string;
  related_document_id: string | null;
  related_checklist_item_id: string | null;
  related_finding_id: string | null;
  notes: string | null;
};

export type ApiPlanReference = {
  plan_reference_id: string;
  project_id: string;
  source_type: string;
  source_id: string;
  target_type: string;
  target_id: string;
  reference_label: string;
  reference_context: string;
  consistency_status: string;
  review_note: string | null;
};

export type ApiPlanConsistencyFinding = {
  plan_finding_id: string;
  project_id: string;
  finding_type: string;
  title: string;
  summary: string;
  risk_level: string;
  status: string;
  related_sheet_ids: string[];
  related_document_ids: string[];
  related_checklist_items: string[];
  related_cad_metadata_ids: string[];
  recommended_human_action: string;
};

type ApiPlanConsistencySummary = {
  project_id: string;
  total_sheets: number;
  missing_sheet_count: number;
  cad_metadata_records: number;
  total_plan_references: number;
  inconsistent_references: number;
  plan_consistency_findings: number;
  conflicting_label_count: number;
  missing_referenced_sheet_count: number;
  missing_plan_reference_count: number;
  unclear_revision_count: number;
  requires_human_review_count: number;
  findings_requiring_human_review: number;
};

export function mapCadMetadata(c: ApiCadMetadata): CadMetadata {
  return {
    cadMetadataId: requireString(c.cad_metadata_id, "cad_metadata_id"),
    projectId: requireString(c.project_id, "project_id"),
    sheetId: c.sheet_id,
    sourceType: c.source_type,
    entityType: c.entity_type,
    entityLabel: c.entity_label,
    layerName: c.layer_name,
    discipline: c.discipline,
    relatedDocumentId: c.related_document_id,
    relatedChecklistItemId: c.related_checklist_item_id,
    relatedFindingId: c.related_finding_id,
    notes: c.notes,
  };
}

export function mapPlanReference(r: ApiPlanReference): PlanReference {
  return {
    planReferenceId: requireString(r.plan_reference_id, "plan_reference_id"),
    projectId: requireString(r.project_id, "project_id"),
    sourceType: r.source_type,
    sourceId: r.source_id,
    targetType: r.target_type,
    targetId: r.target_id,
    referenceLabel: r.reference_label,
    referenceContext: r.reference_context,
    consistencyStatus: r.consistency_status,
    reviewNote: r.review_note,
  };
}

export function mapPlanConsistencyFinding(
  f: ApiPlanConsistencyFinding,
): PlanConsistencyFinding {
  return {
    planFindingId: requireString(f.plan_finding_id, "plan_finding_id"),
    projectId: requireString(f.project_id, "project_id"),
    findingType: f.finding_type,
    title: requireString(f.title, "title"),
    summary: f.summary,
    riskLevel: f.risk_level,
    status: f.status,
    relatedSheetIds: f.related_sheet_ids,
    relatedDocumentIds: f.related_document_ids,
    relatedChecklistItems: f.related_checklist_items,
    relatedCadMetadataIds: f.related_cad_metadata_ids,
    recommendedHumanAction: f.recommended_human_action,
  };
}

function mapPlanConsistencySummary(
  s: ApiPlanConsistencySummary,
): PlanConsistencySummary {
  return {
    projectId: requireString(s.project_id, "project_id"),
    totalSheets: s.total_sheets,
    missingSheetCount: s.missing_sheet_count,
    cadMetadataRecords: s.cad_metadata_records,
    totalPlanReferences: s.total_plan_references,
    inconsistentReferences: s.inconsistent_references,
    planConsistencyFindings: s.plan_consistency_findings,
    conflictingLabelCount: s.conflicting_label_count,
    missingReferencedSheetCount: s.missing_referenced_sheet_count,
    missingPlanReferenceCount: s.missing_plan_reference_count,
    unclearRevisionCount: s.unclear_revision_count,
    requiresHumanReviewCount: s.requires_human_review_count,
    findingsRequiringHumanReview: s.findings_requiring_human_review,
  };
}

export async function getCadMetadata(
  entityType?: string,
): Promise<ApiResult<CadMetadata[]>> {
  const query = entityType
    ? `?entity_type=${encodeURIComponent(entityType)}`
    : "";
  return apiGetMapped<ApiCadMetadata[], CadMetadata[]>(
    `/api/v1/projects/${PROJECT_ID}/cad-metadata${query}`,
    (data) =>
      requireArray(data, "cad_metadata").map((m) =>
        mapCadMetadata(m as ApiCadMetadata),
      ),
  );
}

export async function getCadMetadataBySheet(
  sheetId: string,
): Promise<ApiResult<CadMetadata[]>> {
  return apiGetMapped<ApiCadMetadata[], CadMetadata[]>(
    `/api/v1/plan-sheets/${sheetId}/cad-metadata`,
    (data) =>
      requireArray(data, "cad_metadata").map((m) =>
        mapCadMetadata(m as ApiCadMetadata),
      ),
  );
}

export async function getPlanReferences(): Promise<ApiResult<PlanReference[]>> {
  return apiGetMapped<ApiPlanReference[], PlanReference[]>(
    `/api/v1/projects/${PROJECT_ID}/plan-references`,
    (data) =>
      requireArray(data, "plan_references").map((r) =>
        mapPlanReference(r as ApiPlanReference),
      ),
  );
}

export async function getPlanInconsistencies(): Promise<
  ApiResult<PlanReference[]>
> {
  return apiGetMapped<ApiPlanReference[], PlanReference[]>(
    `/api/v1/projects/${PROJECT_ID}/plan-references/inconsistencies`,
    (data) =>
      requireArray(data, "plan_references").map((r) =>
        mapPlanReference(r as ApiPlanReference),
      ),
  );
}

export async function getPlanConsistencyFindings(
  projectId: string = PROJECT_ID,
): Promise<ApiResult<PlanConsistencyFinding[]>> {
  return apiGetMapped<ApiPlanConsistencyFinding[], PlanConsistencyFinding[]>(
    `/api/v1/projects/${projectId}/plan-consistency-findings`,
    (data) =>
      requireArray(data, "plan_consistency_findings").map((f) =>
        mapPlanConsistencyFinding(f as ApiPlanConsistencyFinding),
      ),
  );
}

export async function getPlanConsistencySummary(
  projectId: string = PROJECT_ID,
): Promise<ApiResult<PlanConsistencySummary>> {
  return apiGetMapped<ApiPlanConsistencySummary, PlanConsistencySummary>(
    `/api/v1/projects/${projectId}/plan-consistency-summary`,
    mapPlanConsistencySummary,
  );
}

export async function runPlanConsistencyCheck(
  projectId: string = PROJECT_ID,
): Promise<PlanConsistencyCheckResult> {
  try {
    const res = await fetch(
      `${API_BASE_URL}/api/v1/projects/${projectId}/plan-consistency-check`,
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
      return { ok: false, status: res.status, backendReachable: true, error: detail };
    }
    return {
      ok: true,
      status: res.status,
      backendReachable: true,
      summary: mapPlanConsistencySummary(
        (await res.json()) as ApiPlanConsistencySummary,
      ),
    };
  } catch {
    return {
      ok: false,
      status: 0,
      backendReachable: false,
      error:
        "The backend is not reachable. Start the API to run the plan consistency check. Plan consistency findings are not simulated in the browser.",
    };
  }
}
