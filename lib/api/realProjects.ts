import { API_BASE_URL, safeFetch } from "./client";

// Production Foundations Sprint 1: real project intake and persistent review
// records. This data is backend-canonical. The frontend does not simulate real
// project records. Read calls return null or empty arrays when the backend is
// unavailable; mutating calls return a clear { ok, error } result.
//
// NEXT_PUBLIC_API_BASE_URL is the backend origin only (for example
// http://localhost:8000). It must not include the /api/v1 path; this client
// appends /api/v1 paths itself.

export type ProjectSourceMode = "demo_fixture" | "user_created";

export type ProjectDetail = {
  projectId: string;
  projectName: string;
  projectType: string;
  locationContext: string;
  jurisdiction: string;
  reviewType: string;
  reviewDomain: string;
  acreage: number;
  disturbedArea: number;
  proposedLots: number;
  status: string;
  summary: string;
  sourceMode: string;
  createdByName: string | null;
  applicantName: string | null;
  applicantOrganization: string | null;
  designEngineerName: string | null;
  designFirm: string | null;
  submissionReference: string | null;
  reviewRoundCurrent: number;
  parcelIds: string[];
  createdAt: string | null;
  updatedAt: string | null;
  documentCount: number;
  findingCount: number;
  auditEventCount: number;
};

export type ProjectDocument = {
  documentId: string;
  projectId: string;
  fileName: string;
  originalFileName: string | null;
  documentType: string;
  status: string;
  purpose: string;
  expectedKeyInformation: string;
  sourceMode: string;
  uploadStatus: string | null;
  processingStatus: string | null;
  contentType: string | null;
  fileSizeBytes: number | null;
  checksumSha256: string | null;
  revisionLabel: string | null;
  revisionDate: string | null;
  uploadedByName: string | null;
  uploadedAt: string | null;
  registeredAt: string | null;
  pageCount: number | null;
  indexedAt: string | null;
  textExtractionStatus: string | null;
  textExtractionSummary: string | null;
  extractionWarningCount: number;
};

function mapDocument(d: Record<string, unknown>): ProjectDocument {
  return {
    documentId: d.document_id as string,
    projectId: d.project_id as string,
    fileName: d.file_name as string,
    originalFileName: (d.original_file_name as string) ?? null,
    documentType: d.document_type as string,
    status: d.status as string,
    purpose: d.purpose as string,
    expectedKeyInformation: d.expected_key_information as string,
    sourceMode: d.source_mode as string,
    uploadStatus: (d.upload_status as string) ?? null,
    processingStatus: (d.processing_status as string) ?? null,
    contentType: (d.content_type as string) ?? null,
    fileSizeBytes: (d.file_size_bytes as number) ?? null,
    checksumSha256: (d.checksum_sha256 as string) ?? null,
    revisionLabel: (d.revision_label as string) ?? null,
    revisionDate: (d.revision_date as string) ?? null,
    uploadedByName: (d.uploaded_by_name as string) ?? null,
    uploadedAt: (d.uploaded_at as string) ?? null,
    registeredAt: (d.registered_at as string) ?? null,
    pageCount: (d.page_count as number) ?? null,
    indexedAt: (d.indexed_at as string) ?? null,
    textExtractionStatus: (d.text_extraction_status as string) ?? null,
    textExtractionSummary: (d.text_extraction_summary as string) ?? null,
    extractionWarningCount: (d.extraction_warning_count as number) ?? 0,
  };
}

export type ReviewerFinding = {
  findingId: string;
  projectId: string;
  title: string;
  category: string;
  riskLevel: string;
  evidenceStatus: string | null;
  evidenceToFind: string;
  reasonItMatters: string;
  recommendedHumanAction: string;
  humanReviewStatus: string;
  relatedDocuments: string[];
  relatedChecklistItems: string[];
  sourceMode: string;
  findingOrigin: string;
  reviewerNotes: string | null;
  createdByName: string | null;
  createdAt: string | null;
};

export type ProjectAuditEvent = {
  auditEventId: string;
  projectId: string;
  eventType: string;
  actorType: string;
  actorDisplayName: string | null;
  relatedEntityType: string;
  relatedEntityId: string;
  description: string;
  timestamp: string;
  eventMetadata: Record<string, unknown>;
};

type ApiProjectDetail = {
  project_id: string;
  project_name: string;
  project_type: string;
  location_context: string;
  jurisdiction: string;
  review_type: string;
  review_domain: string;
  acreage: number;
  disturbed_area: number;
  proposed_lots: number;
  status: string;
  summary: string;
  source_mode: string;
  created_by_name: string | null;
  applicant_name: string | null;
  applicant_organization: string | null;
  design_engineer_name: string | null;
  design_firm: string | null;
  submission_reference: string | null;
  review_round_current: number;
  parcel_ids: string[];
  created_at: string | null;
  updated_at: string | null;
  document_count: number;
  finding_count: number;
  audit_event_count: number;
};

function mapProject(d: ApiProjectDetail): ProjectDetail {
  return {
    projectId: d.project_id,
    projectName: d.project_name,
    projectType: d.project_type,
    locationContext: d.location_context,
    jurisdiction: d.jurisdiction,
    reviewType: d.review_type,
    reviewDomain: d.review_domain,
    acreage: d.acreage,
    disturbedArea: d.disturbed_area,
    proposedLots: d.proposed_lots,
    status: d.status,
    summary: d.summary,
    sourceMode: d.source_mode,
    createdByName: d.created_by_name,
    applicantName: d.applicant_name,
    applicantOrganization: d.applicant_organization,
    designEngineerName: d.design_engineer_name,
    designFirm: d.design_firm,
    submissionReference: d.submission_reference,
    reviewRoundCurrent: d.review_round_current,
    parcelIds: d.parcel_ids ?? [],
    createdAt: d.created_at,
    updatedAt: d.updated_at,
    documentCount: d.document_count,
    findingCount: d.finding_count,
    auditEventCount: d.audit_event_count,
  };
}

export async function listProjects(
  sourceMode?: ProjectSourceMode | "all",
): Promise<ProjectDetail[] | null> {
  const query =
    sourceMode && sourceMode !== "all" ? `?source_mode=${sourceMode}` : "";
  const data = await safeFetch<ApiProjectDetail[]>(
    `/api/v1/projects${query}`,
  );
  if (!data) return null;
  return data.map(mapProject);
}

export async function getProjectDetail(
  projectId: string,
): Promise<ProjectDetail | null> {
  const data = await safeFetch<ApiProjectDetail>(
    `/api/v1/projects/${projectId}`,
  );
  return data ? mapProject(data) : null;
}

export type CreateProjectInput = {
  projectName: string;
  projectType?: string;
  jurisdiction?: string;
  reviewType?: string;
  reviewDomain?: string;
  locationContext?: string;
  acreage?: number | null;
  disturbedArea?: number | null;
  proposedLots?: number | null;
  summary?: string;
  applicantName?: string;
  applicantOrganization?: string;
  designEngineerName?: string;
  designFirm?: string;
  submissionReference?: string;
  parcelIds?: string[];
};

type MutationResult<T> = {
  ok: boolean;
  backendReachable: boolean;
  data?: T;
  error?: string;
};

async function postJson<T>(
  path: string,
  body: unknown,
): Promise<MutationResult<T>> {
  try {
    const res = await fetch(`${API_BASE_URL}${path}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
      cache: "no-store",
    });
    if (!res.ok) {
      let detail = `Request failed (${res.status}).`;
      try {
        const parsed = (await res.json()) as { detail?: string };
        if (parsed.detail) detail = parsed.detail;
      } catch {
        // Keep the generic message.
      }
      return { ok: false, backendReachable: true, error: detail };
    }
    return { ok: true, backendReachable: true, data: (await res.json()) as T };
  } catch {
    return {
      ok: false,
      backendReachable: false,
      error: "Backend unavailable. Start the API to use real project intake.",
    };
  }
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

export async function listProjectDocuments(
  projectId: string,
): Promise<ProjectDocument[] | null> {
  const data = await safeFetch<Record<string, unknown>[]>(
    `/api/v1/projects/${projectId}/documents`,
  );
  if (!data) return null;
  return data.map(mapDocument);
}

export async function getProjectDocument(
  projectId: string,
  documentId: string,
): Promise<ProjectDocument | null> {
  const docs = await listProjectDocuments(projectId);
  if (!docs) return null;
  return docs.find((d) => d.documentId === documentId) ?? null;
}

export type RegisterDocumentInput = {
  originalFileName: string;
  documentType?: string;
  purpose?: string;
  expectedKeyInformation?: string;
  contentType?: string;
  fileSizeBytes?: number | null;
  revisionLabel?: string;
  revisionDate?: string;
};

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
      { method: "POST", body: form, cache: "no-store" },
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

export async function listProjectFindings(
  projectId: string,
): Promise<ReviewerFinding[] | null> {
  const data = await safeFetch<Record<string, unknown>[]>(
    `/api/v1/projects/${projectId}/findings`,
  );
  if (!data) return null;
  return data.map((f) => ({
    findingId: f.finding_id as string,
    projectId: f.project_id as string,
    title: f.title as string,
    category: f.category as string,
    riskLevel: f.risk_level as string,
    evidenceStatus: (f.evidence_status as string) ?? null,
    evidenceToFind: f.evidence_to_find as string,
    reasonItMatters: f.reason_it_matters as string,
    recommendedHumanAction: f.recommended_human_action as string,
    humanReviewStatus: f.human_review_status as string,
    relatedDocuments: (f.related_documents as string[]) ?? [],
    relatedChecklistItems: (f.related_checklist_items as string[]) ?? [],
    sourceMode: f.source_mode as string,
    findingOrigin: f.finding_origin as string,
    reviewerNotes: (f.reviewer_notes as string) ?? null,
    createdByName: (f.created_by_name as string) ?? null,
    createdAt: (f.created_at as string) ?? null,
  }));
}

export async function getProjectFinding(
  projectId: string,
  findingId: string,
): Promise<ReviewerFinding | null> {
  const findings = await listProjectFindings(projectId);
  if (!findings) return null;
  return findings.find((f) => f.findingId === findingId) ?? null;
}

export type CreateFindingInput = {
  title: string;
  category?: string;
  riskLevel?: string;
  evidenceStatus?: string;
  evidenceToFind?: string;
  reasonItMatters?: string;
  recommendedHumanAction?: string;
  relatedDocuments?: string[];
  reviewerNotes?: string;
  humanReviewStatus?: string;
};

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

export async function listProjectAuditEvents(
  projectId: string,
): Promise<ProjectAuditEvent[] | null> {
  const data = await safeFetch<Record<string, unknown>[]>(
    `/api/v1/projects/${projectId}/audit-events`,
  );
  if (!data) return null;
  return data.map((e) => ({
    auditEventId: e.audit_event_id as string,
    projectId: e.project_id as string,
    eventType: e.event_type as string,
    actorType: e.actor_type as string,
    actorDisplayName: (e.actor_display_name as string) ?? null,
    relatedEntityType: e.related_entity_type as string,
    relatedEntityId: e.related_entity_id as string,
    description: e.description as string,
    timestamp: e.timestamp as string,
    eventMetadata: (e.event_metadata as Record<string, unknown>) ?? {},
  }));
}

export type CreateEvidenceReferenceInput = {
  documentId: string;
  reviewerNote: string;
  pageNumber?: number | null;
  sheetNumber?: string;
  sectionLabel?: string;
};

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
