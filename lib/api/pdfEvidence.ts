import {
  apiGetMapped,
  apiMutate,
  requireString,
  type ApiResult,
} from "./client";

// Production Foundations Sprint 2: PDF page indexing and reviewer-selected
// evidence citations. This data is backend-canonical. Read calls return a
// typed ApiResult that preserves the failure category and status; mutating
// calls return a clear { ok, error } result. Mappers assert required
// identifiers so an invalid payload surfaces as an explicit invalid_response
// failure instead of propagating undefined fields into evidence UI.
//
// NEXT_PUBLIC_API_BASE_URL is the backend origin only (no /api/v1 path); this
// client appends the /api/v1 paths itself.

export type DocumentPage = {
  documentPageId: string;
  projectId: string;
  documentId: string;
  pageNumber: number;
  pageLabel: string | null;
  extractedText: string | null;
  textExtractionStatus: string;
  textExtractionMethod: string | null;
  charCount: number;
  wordCount: number;
  extractionWarnings: string[];
  indexedAt: string | null;
};

export type DocumentIndexingSummary = {
  documentId: string;
  pageCount: number;
  pagesWithText: number;
  pagesWithoutText: number;
  warningCount: number;
  processingStatus: string;
  textExtractionStatus: string;
  indexedAt: string | null;
  summary: string;
};

export type DocumentChunkingSummary = {
  documentId: string;
  projectId: string;
  documentType: string;
  fileName: string;
  pagesChunked: number;
  chunkCount: number;
  removedPriorChunkCount: number;
};

export type EvidenceCitation = {
  evidenceCitationId: string;
  projectId: string;
  findingId: string;
  documentId: string;
  documentPageId: string | null;
  pageNumber: number | null;
  pageLabel: string | null;
  sectionLabel: string | null;
  quotedExcerpt: string | null;
  reviewerNote: string | null;
  citationType: string;
  citationStatus: string;
  createdByName: string | null;
  sourceMode: string;
  createdAt: string | null;
  updatedAt: string | null;
};

type MutationResult<T> = {
  ok: boolean;
  backendReachable: boolean;
  data?: T;
  error?: string;
};

function mapPage(p: Record<string, unknown>): DocumentPage {
  return {
    documentPageId: requireString(p.document_page_id, "document_page_id"),
    projectId: requireString(p.project_id, "project_id"),
    documentId: requireString(p.document_id, "document_id"),
    pageNumber: p.page_number as number,
    pageLabel: (p.page_label as string) ?? null,
    extractedText: (p.extracted_text as string) ?? null,
    textExtractionStatus: requireString(
      p.text_extraction_status,
      "text_extraction_status",
    ),
    textExtractionMethod: (p.text_extraction_method as string) ?? null,
    charCount: (p.char_count as number) ?? 0,
    wordCount: (p.word_count as number) ?? 0,
    extractionWarnings: (p.extraction_warnings as string[]) ?? [],
    indexedAt: (p.indexed_at as string) ?? null,
  };
}

function mapCitation(c: Record<string, unknown>): EvidenceCitation {
  return {
    evidenceCitationId: requireString(
      c.evidence_citation_id,
      "evidence_citation_id",
    ),
    projectId: requireString(c.project_id, "project_id"),
    findingId: requireString(c.finding_id, "finding_id"),
    documentId: requireString(c.document_id, "document_id"),
    documentPageId: (c.document_page_id as string) ?? null,
    pageNumber: (c.page_number as number) ?? null,
    pageLabel: (c.page_label as string) ?? null,
    sectionLabel: (c.section_label as string) ?? null,
    quotedExcerpt: (c.quoted_excerpt as string) ?? null,
    reviewerNote: (c.reviewer_note as string) ?? null,
    citationType: requireString(c.citation_type, "citation_type"),
    citationStatus: requireString(c.citation_status, "citation_status"),
    createdByName: (c.created_by_name as string) ?? null,
    sourceMode: c.source_mode as string,
    createdAt: (c.created_at as string) ?? null,
    updatedAt: (c.updated_at as string) ?? null,
  };
}

// Thin adapter over the shared mutation helper that keeps this module's
// unavailable-backend message.
async function postJson<T>(
  path: string,
  body: unknown,
  mapper: (raw: Record<string, unknown>) => T,
): Promise<MutationResult<T>> {
  return apiMutate<T>("POST", path, {
    body,
    map: mapper,
    unavailableMessage: "Backend unavailable. Start the API to use PDF indexing.",
  });
}

export async function indexPdfDocument(
  projectId: string,
  documentId: string,
): Promise<MutationResult<DocumentIndexingSummary>> {
  return postJson<DocumentIndexingSummary>(
    `/api/v1/projects/${projectId}/documents/${documentId}/index-pdf`,
    {},
    (raw) => ({
      documentId: raw.document_id as string,
      pageCount: raw.page_count as number,
      pagesWithText: raw.pages_with_text as number,
      pagesWithoutText: raw.pages_without_text as number,
      warningCount: raw.warning_count as number,
      processingStatus: raw.processing_status as string,
      textExtractionStatus: raw.text_extraction_status as string,
      indexedAt: (raw.indexed_at as string) ?? null,
      summary: raw.summary as string,
    }),
  );
}

export async function buildDocumentChunks(
  projectId: string,
  documentId: string,
): Promise<MutationResult<DocumentChunkingSummary>> {
  return postJson<DocumentChunkingSummary>(
    `/api/v1/projects/${projectId}/documents/${documentId}/chunk-pages`,
    {},
    (raw) => ({
      documentId: raw.document_id as string,
      projectId: raw.project_id as string,
      documentType: raw.document_type as string,
      fileName: raw.file_name as string,
      pagesChunked: raw.pages_chunked as number,
      chunkCount: raw.chunk_count as number,
      removedPriorChunkCount: raw.removed_prior_chunk_count as number,
    }),
  );
}

export async function listDocumentPages(
  projectId: string,
  documentId: string,
): Promise<ApiResult<DocumentPage[]>> {
  return apiGetMapped<Record<string, unknown>[], DocumentPage[]>(
    `/api/v1/projects/${projectId}/documents/${documentId}/pages`,
    (data) => data.map(mapPage),
  );
}

export async function getDocumentPage(
  projectId: string,
  documentId: string,
  pageNumber: number,
): Promise<ApiResult<DocumentPage>> {
  return apiGetMapped<Record<string, unknown>, DocumentPage>(
    `/api/v1/projects/${projectId}/documents/${documentId}/pages/${pageNumber}`,
    mapPage,
  );
}

export type CreateCitationInput = {
  documentId: string;
  documentPageId?: string;
  pageNumber?: number | null;
  sectionLabel?: string;
  quotedExcerpt?: string;
  reviewerNote?: string;
  citationType?: string;
  citationStatus?: string;
};

export async function createEvidenceCitation(
  projectId: string,
  findingId: string,
  input: CreateCitationInput,
): Promise<MutationResult<EvidenceCitation>> {
  return postJson<EvidenceCitation>(
    `/api/v1/projects/${projectId}/findings/${findingId}/citations`,
    {
      document_id: input.documentId,
      document_page_id: input.documentPageId ?? null,
      page_number: input.pageNumber ?? null,
      section_label: input.sectionLabel || null,
      quoted_excerpt: input.quotedExcerpt || null,
      reviewer_note: input.reviewerNote || null,
      citation_type: input.citationType || "reviewer_selected",
      citation_status: input.citationStatus || null,
    },
    mapCitation,
  );
}

export async function listFindingCitations(
  projectId: string,
  findingId: string,
): Promise<ApiResult<EvidenceCitation[]>> {
  return apiGetMapped<Record<string, unknown>[], EvidenceCitation[]>(
    `/api/v1/projects/${projectId}/findings/${findingId}/citations`,
    (data) => data.map(mapCitation),
  );
}

export async function listProjectEvidenceCitations(
  projectId: string,
): Promise<ApiResult<EvidenceCitation[]>> {
  return apiGetMapped<Record<string, unknown>[], EvidenceCitation[]>(
    `/api/v1/projects/${projectId}/evidence-citations`,
    (data) => data.map(mapCitation),
  );
}

export async function updateEvidenceCitation(
  projectId: string,
  findingId: string,
  citationId: string,
  input: Partial<{
    sectionLabel: string;
    quotedExcerpt: string;
    reviewerNote: string;
    citationStatus: string;
    citationType: string;
  }>,
): Promise<MutationResult<EvidenceCitation>> {
  return apiMutate<EvidenceCitation>(
    "PATCH",
    `/api/v1/projects/${projectId}/findings/${findingId}/citations/${citationId}`,
    {
      body: {
        section_label: input.sectionLabel ?? null,
        quoted_excerpt: input.quotedExcerpt ?? null,
        reviewer_note: input.reviewerNote ?? null,
        citation_status: input.citationStatus ?? null,
        citation_type: input.citationType ?? null,
      },
      map: mapCitation,
      parseErrorDetail: false,
      failureMessage: (status) => `Update failed (${status}).`,
    },
  );
}

export async function deleteEvidenceCitation(
  projectId: string,
  findingId: string,
  citationId: string,
): Promise<MutationResult<unknown>> {
  return apiMutate(
    "DELETE",
    `/api/v1/projects/${projectId}/findings/${findingId}/citations/${citationId}`,
    {
      parseResponse: false,
      parseErrorDetail: false,
      failureMessage: (status) => `Delete failed (${status}).`,
    },
  );
}
