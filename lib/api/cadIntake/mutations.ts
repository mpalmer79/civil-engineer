import { API_BASE_URL, PROJECT_ID, apiMutate, authHeaders } from "../client";
import {
  mapCadFile,
  mapFinding,
  mapParseRun,
  type ApiCadFile,
  type ApiFinding,
  type ApiParseRun,
} from "./mappers";
import type {
  CadFileUpload,
  CadFindingPromotionResponse,
  CadParseRun,
  CadPlanSheetComparison,
  CadSelectedPromotionResult,
  CadUploadResponse,
  CadWorkflowItemsResult,
} from "./types";

// Mutating calls return a clear backend-required result. CAD data is not
// simulated in the browser, so an unreachable backend surfaces as
// backendReachable: false with a reviewer-facing message.

export async function createCadFileRecord(
  sampleKey = "brookside_meadows",
  uploadedBy = "reviewer",
  projectId: string = PROJECT_ID,
): Promise<{
  ok: boolean;
  backendReachable: boolean;
  cadFile?: CadFileUpload;
  error?: string;
}> {
  const result = await apiMutate<CadFileUpload>(
    "POST",
    `/api/v1/projects/${projectId}/cad-files`,
    {
      body: { sample_key: sampleKey, uploaded_by: uploadedBy },
      map: (raw) => mapCadFile(raw as unknown as ApiCadFile),
      unavailableMessage:
        "The backend is not reachable. Start the API to register and parse a DXF file. CAD data is not simulated in the browser.",
    },
  );
  return {
    ok: result.ok,
    backendReachable: result.backendReachable,
    cadFile: result.data,
    error: result.error,
  };
}

export async function parseCadFile(cadFileId: string): Promise<{
  ok: boolean;
  backendReachable: boolean;
  run?: CadParseRun;
  error?: string;
}> {
  const result = await apiMutate<CadParseRun>(
    "POST",
    `/api/v1/cad-files/${cadFileId}/parse`,
    {
      map: (raw) => mapParseRun(raw as unknown as ApiParseRun),
      unavailableMessage:
        "The backend is not reachable. Start the API to parse the DXF file.",
    },
  );
  return {
    ok: result.ok,
    backendReachable: result.backendReachable,
    run: result.data,
    error: result.error,
  };
}

export async function compareCadReferencesToPlanSheets(
  parseRunId: string,
): Promise<CadPlanSheetComparison | null> {
  const result = await apiMutate<CadPlanSheetComparison>(
    "POST",
    `/api/v1/cad-parse-runs/${parseRunId}/compare-plan-sheets`,
    {
      map: (raw) => {
        const data = raw as unknown as {
          parse_run_id: string;
          project_id: string;
          total_candidates: number;
          matched_count: number;
          unmatched_count: number;
          rows: {
            candidate_id: string;
            reference_text: string;
            normalized_reference: string;
            reference_type: string;
            matched_plan_sheet_id: string | null;
            matched_sheet_number: string | null;
            confidence_label: string;
            match_reason: string;
          }[];
          findings: ApiFinding[];
          note: string;
        };
        return {
          parseRunId: data.parse_run_id,
          projectId: data.project_id,
          totalCandidates: data.total_candidates,
          matchedCount: data.matched_count,
          unmatchedCount: data.unmatched_count,
          rows: data.rows.map((r) => ({
            candidateId: r.candidate_id,
            referenceText: r.reference_text,
            normalizedReference: r.normalized_reference,
            referenceType: r.reference_type,
            matchedPlanSheetId: r.matched_plan_sheet_id,
            matchedSheetNumber: r.matched_sheet_number,
            confidenceLabel: r.confidence_label,
            matchReason: r.match_reason,
          })),
          findings: (data.findings ?? []).map(mapFinding),
          note: data.note,
        };
      },
    },
  );
  return result.ok && result.data ? result.data : null;
}

// Phase 12: browser DXF upload, parse queue, and finding promotion.

export async function uploadCadFile(
  file: File,
  uploadedBy = "reviewer",
  projectId: string = PROJECT_ID,
): Promise<CadUploadResponse> {
  // Client-side extension guard before sending. The backend validation remains
  // authoritative; this only avoids an obviously wrong request.
  if (!file.name.toLowerCase().endsWith(".dxf")) {
    return {
      ok: false,
      backendReachable: true,
      validationStatus: "rejected",
      error:
        "Only DXF files are supported in this phase. Select a .dxf file. DWG parsing is future work.",
    };
  }
  // Multipart upload; the shared JSON mutation helper does not apply here.
  try {
    const form = new FormData();
    form.append("file", file);
    form.append("uploaded_by", uploadedBy);
    const res = await fetch(
      `${API_BASE_URL}/api/v1/projects/${projectId}/cad-files/upload`,
      { method: "POST", headers: authHeaders(), body: form, cache: "no-store" },
    );
    if (!res.ok) {
      let detail = `Request failed (${res.status}).`;
      try {
        const body = (await res.json()) as { detail?: string };
        if (body.detail) detail = body.detail;
      } catch {
        // Keep generic message.
      }
      return {
        ok: false,
        backendReachable: true,
        validationStatus: "rejected",
        error: detail,
      };
    }
    const data = (await res.json()) as {
      cad_file: ApiCadFile;
      validation_status: string;
      validation_message: string;
      next_action: string;
      note: string;
    };
    return {
      ok: true,
      backendReachable: true,
      cadFile: mapCadFile(data.cad_file),
      validationStatus: data.validation_status,
      validationMessage: data.validation_message,
      nextAction: data.next_action,
      note: data.note,
    };
  } catch {
    return {
      ok: false,
      backendReachable: false,
      error:
        "The backend is not reachable. Start the API to upload a DXF file. CAD data is not simulated in the browser.",
    };
  }
}

export async function requestCadParse(cadFileId: string): Promise<{
  ok: boolean;
  backendReachable: boolean;
  run?: CadParseRun;
  error?: string;
}> {
  const result = await apiMutate<CadParseRun>(
    "POST",
    `/api/v1/cad-files/${cadFileId}/request-parse`,
    {
      map: (raw) => mapParseRun(raw as unknown as ApiParseRun),
      unavailableMessage:
        "The backend is not reachable. Start the API to request a parse.",
    },
  );
  return {
    ok: result.ok,
    backendReachable: result.backendReachable,
    run: result.data,
    error: result.error,
  };
}

export async function promoteCadFindingToWorkflow(
  cadReviewFindingId: string,
  reviewerName = "reviewer",
  reviewerNote?: string,
): Promise<CadFindingPromotionResponse> {
  const result = await apiMutate<{
    cad_review_finding_id: string;
    workflow_item_id: string | null;
    created: boolean;
    already_promoted: boolean;
    note: string;
  }>(
    "POST",
    `/api/v1/cad-review-findings/${cadReviewFindingId}/promote-to-workflow`,
    {
      body: {
        reviewer_name: reviewerName,
        reviewer_note: reviewerNote ?? null,
      },
      parseErrorDetail: false,
      unavailableMessage:
        "The backend is not reachable. Start the API to promote a CAD finding.",
    },
  );
  if (!result.ok || !result.data) {
    return {
      ok: result.ok,
      backendReachable: result.backendReachable,
      error: result.error,
    };
  }
  return {
    ok: true,
    backendReachable: true,
    cadReviewFindingId: result.data.cad_review_finding_id,
    workflowItemId: result.data.workflow_item_id,
    created: result.data.created,
    alreadyPromoted: result.data.already_promoted,
    note: result.data.note,
  };
}

export async function promoteSelectedCadFindingsToWorkflow(
  cadReviewFindingIds: string[],
  reviewerName = "reviewer",
  reviewerNote?: string,
  projectId: string = PROJECT_ID,
): Promise<CadSelectedPromotionResult> {
  const result = await apiMutate<{
    requested_count: number;
    created_count: number;
    already_promoted_count: number;
    not_found_count: number;
    workflow_item_ids: string[];
    note: string;
  }>(
    "POST",
    `/api/v1/projects/${projectId}/cad-review-findings/promote-selected`,
    {
      body: {
        cad_review_finding_ids: cadReviewFindingIds,
        reviewer_name: reviewerName,
        reviewer_note: reviewerNote ?? null,
      },
      parseErrorDetail: false,
      unavailableMessage:
        "The backend is not reachable. Start the API to promote CAD findings.",
    },
  );
  if (!result.ok || !result.data) {
    return {
      ok: result.ok,
      backendReachable: result.backendReachable,
      error: result.error,
    };
  }
  return {
    ok: true,
    backendReachable: true,
    requestedCount: result.data.requested_count,
    createdCount: result.data.created_count,
    alreadyPromotedCount: result.data.already_promoted_count,
    notFoundCount: result.data.not_found_count,
    workflowItemIds: result.data.workflow_item_ids,
    note: result.data.note,
  };
}

export async function createWorkflowItemsFromCadFindings(projectId: string = PROJECT_ID): Promise<CadWorkflowItemsResult> {
  const result = await apiMutate<{
    created_count: number;
    workflow_item_ids: string[];
    note: string;
  }>(
    "POST",
    `/api/v1/projects/${projectId}/workflow-items/from-cad-findings`,
    {
      parseErrorDetail: false,
      unavailableMessage:
        "The backend is not reachable. Start the API to create workflow items from CAD findings.",
    },
  );
  if (!result.ok || !result.data) {
    return {
      ok: result.ok,
      backendReachable: result.backendReachable,
      error: result.error,
    };
  }
  return {
    ok: true,
    backendReachable: true,
    createdCount: result.data.created_count,
    workflowItemIds: result.data.workflow_item_ids,
    note: result.data.note,
  };
}
