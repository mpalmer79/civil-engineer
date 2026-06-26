import { API_BASE_URL, authHeaders, safeFetch } from "./client";

// Production Foundations Sprint 2: PDF page indexing and reviewer-selected
// evidence citations. This data is backend-canonical. Read calls return null
// when the backend is unavailable; mutating calls return a clear { ok, error }
// result.
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
    documentPageId: p.document_page_id as string,
    projectId: p.project_id as string,
    documentId: p.document_id as string,
    pageNumber: p.page_number as number,
    pageLabel: (p.page_label as string) ?? null,
    extractedText: (p.extracted_text as string) ?? null,
    textExtractionStatus: p.text_extraction_status as string,
    textExtractionMethod: (p.text_extraction_method as string) ?? null,
    charCount: (p.char_count as number) ?? 0,
    wordCount: (p.word_count as number) ?? 0,
    extractionWarnings: (p.extraction_warnings as string[]) ?? [],
    indexedAt: (p.indexed_at as string) ?? null,
  };
}

function mapCitation(c: Record<string, unknown>): EvidenceCitation {
  return {
    evidenceCitationId: c.evidence_citation_id as string,
    projectId: c.project_id as string,
    findingId: c.finding_id as string,
    documentId: c.document_id as string,
    documentPageId: (c.document_page_id as string) ?? null,
    pageNumber: (c.page_number as number) ?? null,
    pageLabel: (c.page_label as string) ?? null,
    sectionLabel: (c.section_label as string) ?? null,
    quotedExcerpt: (c.quoted_excerpt as string) ?? null,
    reviewerNote: (c.reviewer_note as string) ?? null,
    citationType: c.citation_type as string,
    citationStatus: c.citation_status as string,
    createdByName: (c.created_by_name as string) ?? null,
    sourceMode: c.source_mode as string,
    createdAt: (c.created_at as string) ?? null,
    updatedAt: (c.updated_at as string) ?? null,
  };
}

async function postJson<T>(
  path: string,
  body: unknown,
  mapper: (raw: Record<string, unknown>) => T,
): Promise<MutationResult<T>> {
  try {
    const res = await fetch(`${API_BASE_URL}${path}`, {
      method: "POST",
      headers: authHeaders({ "Content-Type": "application/json" }),
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
    return {
      ok: true,
      backendReachable: true,
      data: mapper((await res.json()) as Record<string, unknown>),
    };
  } catch {
    return {
      ok: false,
      backendReachable: false,
      error: "Backend unavailable. Start the API to use PDF indexing.",
    };
  }
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

export async function listDocumentPages(
  projectId: string,
  documentId: string,
): Promise<DocumentPage[] | null> {
  const data = await safeFetch<Record<string, unknown>[]>(
    `/api/v1/projects/${projectId}/documents/${documentId}/pages`,
  );
  if (!data) return null;
  return data.map(mapPage);
}

export async function getDocumentPage(
  projectId: string,
  documentId: string,
  pageNumber: number,
): Promise<DocumentPage | null> {
  const data = await safeFetch<Record<string, unknown>>(
    `/api/v1/projects/${projectId}/documents/${documentId}/pages/${pageNumber}`,
  );
  return data ? mapPage(data) : null;
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
): Promise<EvidenceCitation[] | null> {
  const data = await safeFetch<Record<string, unknown>[]>(
    `/api/v1/projects/${projectId}/findings/${findingId}/citations`,
  );
  if (!data) return null;
  return data.map(mapCitation);
}

export async function listProjectEvidenceCitations(
  projectId: string,
): Promise<EvidenceCitation[] | null> {
  const data = await safeFetch<Record<string, unknown>[]>(
    `/api/v1/projects/${projectId}/evidence-citations`,
  );
  if (!data) return null;
  return data.map(mapCitation);
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
  try {
    const res = await fetch(
      `${API_BASE_URL}/api/v1/projects/${projectId}/findings/${findingId}/citations/${citationId}`,
      {
        method: "PATCH",
        headers: authHeaders({ "Content-Type": "application/json" }),
        body: JSON.stringify({
          section_label: input.sectionLabel ?? null,
          quoted_excerpt: input.quotedExcerpt ?? null,
          reviewer_note: input.reviewerNote ?? null,
          citation_status: input.citationStatus ?? null,
          citation_type: input.citationType ?? null,
        }),
        cache: "no-store",
      },
    );
    if (!res.ok) {
      return { ok: false, backendReachable: true, error: `Update failed (${res.status}).` };
    }
    return {
      ok: true,
      backendReachable: true,
      data: mapCitation((await res.json()) as Record<string, unknown>),
    };
  } catch {
    return { ok: false, backendReachable: false, error: "Backend unavailable." };
  }
}

export async function deleteEvidenceCitation(
  projectId: string,
  findingId: string,
  citationId: string,
): Promise<MutationResult<unknown>> {
  try {
    const res = await fetch(
      `${API_BASE_URL}/api/v1/projects/${projectId}/findings/${findingId}/citations/${citationId}`,
      { method: "DELETE", cache: "no-store" },
    );
    if (!res.ok) {
      return { ok: false, backendReachable: true, error: `Delete failed (${res.status}).` };
    }
    return { ok: true, backendReachable: true };
  } catch {
    return { ok: false, backendReachable: false, error: "Backend unavailable." };
  }
}
