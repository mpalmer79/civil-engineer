import { API_BASE_URL, apiMutate, authHeaders } from "../client";
import { mapProject, type ApiProjectDetail } from "./mappers";
import type {
  CreateEvidenceReferenceInput,
  CreateFindingInput,
  CreateProjectInput,
  ProjectDetail,
  ProjectDocument,
  RegisterDocumentInput,
  ReviewerFinding,
} from "./types";

// Mutating calls return a clear { ok, error } result. Real project records are
// backend-canonical, so an unreachable backend surfaces as
// backendReachable: false with a reviewer-facing message.

type MutationResult<T> = {
  ok: boolean;
  backendReachable: boolean;
  data?: T;
  error?: string;
};

// Thin adapter over the shared mutation helper that keeps this module's
// unavailable-backend message.
async function postJson<T>(
  path: string,
  body: unknown,
): Promise<MutationResult<T>> {
  return apiMutate<T>("POST", path, {
    body,
    unavailableMessage:
      "Backend unavailable. Start the API to use real project intake.",
  });
}

export async function createProject(
  input: CreateProjectInput,
): Promise<MutationResult<ProjectDetail>> {
  const result = await postJson<ApiProjectDetail>("/api/v1/projects", {
    project_name: input.projectName,
    project_type: input.projectType || "Not specified",
    jurisdiction: input.jurisdiction ?? "",
    review_type: input.reviewType || "Not specified",
    review_domain: input.reviewDomain || "stormwater",
    location_context: input.locationContext ?? "",
    acreage: input.acreage ?? null,
    disturbed_area: input.disturbedArea ?? null,
    proposed_lots: input.proposedLots ?? null,
    summary: input.summary ?? null,
    applicant_name: input.applicantName || null,
    applicant_organization: input.applicantOrganization || null,
    design_engineer_name: input.designEngineerName || null,
    design_firm: input.designFirm || null,
    submission_reference: input.submissionReference || null,
    parcel_ids: input.parcelIds ?? [],
  });
  return {
    ...result,
    data: result.data ? mapProject(result.data) : undefined,
  };
}

export async function registerProjectDocument(
  projectId: string,
  input: RegisterDocumentInput,
): Promise<MutationResult<ProjectDocument>> {
  return postJson<ProjectDocument>(
    `/api/v1/projects/${projectId}/documents/register`,
    {
      original_file_name: input.originalFileName,
      document_type: input.documentType || "other",
      purpose: input.purpose || null,
      expected_key_information: input.expectedKeyInformation || null,
      content_type: input.contentType || null,
      file_size_bytes: input.fileSizeBytes ?? null,
      revision_label: input.revisionLabel || null,
      revision_date: input.revisionDate || null,
    },
  );
}

export async function uploadProjectDocument(
  projectId: string,
  file: File,
  options: { documentType?: string; purpose?: string; revisionLabel?: string } = {},
): Promise<MutationResult<ProjectDocument>> {
  try {
    const form = new FormData();
    form.append("file", file);
    form.append("document_type", options.documentType || "other");
    if (options.purpose) form.append("purpose", options.purpose);
    if (options.revisionLabel) form.append("revision_label", options.revisionLabel);
    const res = await fetch(
      `${API_BASE_URL}/api/v1/projects/${projectId}/documents/upload`,
      { method: "POST", body: form, headers: authHeaders(), cache: "no-store" },
    );
    if (!res.ok) {
      let detail = `Upload failed (${res.status}).`;
      try {
        const parsed = (await res.json()) as { detail?: string };
        if (parsed.detail) detail = parsed.detail;
      } catch {
        // Keep the generic message.
      }
      return { ok: false, backendReachable: true, error: detail };
    }
    return {
      ok: true,
      backendReachable: true,
      data: (await res.json()) as ProjectDocument,
    };
  } catch {
    return {
      ok: false,
      backendReachable: false,
      error: "Backend unavailable. Start the API to upload documents.",
    };
  }
}

export async function createProjectFinding(
  projectId: string,
  input: CreateFindingInput,
): Promise<MutationResult<ReviewerFinding>> {
  return postJson<ReviewerFinding>(
    `/api/v1/projects/${projectId}/findings`,
    {
      title: input.title,
      category: input.category || "general",
      risk_level: input.riskLevel || "medium",
      evidence_status: input.evidenceStatus || "needs_reviewer_confirmation",
      evidence_to_find: input.evidenceToFind || "",
      reason_it_matters: input.reasonItMatters || "",
      recommended_human_action: input.recommendedHumanAction || "",
      related_documents: input.relatedDocuments ?? [],
      reviewer_notes: input.reviewerNotes || null,
      human_review_status:
        input.humanReviewStatus || "needs_reviewer_confirmation",
    },
  );
}

export async function createEvidenceReference(
  findingId: string,
  input: CreateEvidenceReferenceInput,
): Promise<MutationResult<unknown>> {
  return postJson<unknown>(
    `/api/v1/findings/${findingId}/evidence-references`,
    {
      document_id: input.documentId,
      reviewer_note: input.reviewerNote,
      page_number: input.pageNumber ?? null,
      sheet_number: input.sheetNumber || null,
      section_label: input.sectionLabel || null,
    },
  );
}
