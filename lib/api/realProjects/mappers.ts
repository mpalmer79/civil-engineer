import { requireString } from "../client";
import type { ProjectDetail, ProjectDocument, ReviewerFinding } from "./types";

// Module-internal wire type and mappers shared by the read and mutation paths.
// These are not part of the public @/lib/api surface. Projects, documents, and
// findings are high-risk reviewer surfaces, so the mappers assert identifiers
// and required fields; a payload missing them surfaces as an explicit
// invalid_response failure through apiGetMapped.

export type ApiProjectDetail = {
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
  assigned_reviewer_user_id: string | null;
  assigned_reviewer_name: string | null;
  review_priority: string | null;
  review_due_date: string | null;
  last_reviewer_activity_at: string | null;
  created_at: string | null;
  updated_at: string | null;
  document_count: number;
  finding_count: number;
  audit_event_count: number;
};

// Documents are a high-risk reviewer surface, so the mapper asserts the
// identifiers and required fields. A payload missing them surfaces as an
// explicit invalid_response failure through apiGetMapped.
export function mapDocument(d: Record<string, unknown>): ProjectDocument {
  return {
    documentId: requireString(d.document_id, "document_id"),
    projectId: requireString(d.project_id, "project_id"),
    fileName: requireString(d.file_name, "file_name"),
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
    storageProvider: (d.storage_provider as string) ?? null,
    fileAvailable: (d.file_available as boolean) ?? false,
    downloadCount: (d.download_count as number) ?? 0,
    lastDownloadedAt: (d.last_downloaded_at as string) ?? null,
  };
}

// Projects are a high-risk reviewer surface, so the mapper asserts the
// identifiers and required fields before mapping.
export function mapProject(d: ApiProjectDetail): ProjectDetail {
  return {
    projectId: requireString(d.project_id, "project_id"),
    projectName: requireString(d.project_name, "project_name"),
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
    assignedReviewerUserId: d.assigned_reviewer_user_id ?? null,
    assignedReviewerName: d.assigned_reviewer_name ?? null,
    reviewPriority: d.review_priority ?? null,
    reviewDueDate: d.review_due_date ?? null,
    lastReviewerActivityAt: d.last_reviewer_activity_at ?? null,
    createdAt: d.created_at,
    updatedAt: d.updated_at,
    documentCount: d.document_count,
    findingCount: d.finding_count,
    auditEventCount: d.audit_event_count,
  };
}

// Findings are a high-risk reviewer surface, so the mapper asserts the
// identifiers and required fields before mapping.
export function mapFinding(f: Record<string, unknown>): ReviewerFinding {
  return {
    findingId: requireString(f.finding_id, "finding_id"),
    projectId: requireString(f.project_id, "project_id"),
    title: requireString(f.title, "title"),
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
  };
}
