import { API_BASE_URL, authHeaders, safeFetch } from "./client";

// Production Foundations Sprint 3: deterministic, local evidence retrieval over
// indexed PDF page text, plus a reviewer-controlled draft finding queue. This
// data is backend-canonical. Read calls return null when the backend is
// unavailable; mutating calls return a clear { ok, error } result.
//
// Retrieval is deterministic and local. There are no live AI calls. Search
// results are candidates that require reviewer confirmation, never conclusions.
//
// NEXT_PUBLIC_API_BASE_URL is the backend origin only (no /api/v1 path); this
// client appends the /api/v1 paths itself.

export type EvidenceSearchResult = {
  documentId: string;
  documentName: string;
  documentType: string | null;
  chunkId: string | null;
  documentPageId: string | null;
  pageNumber: number | null;
  pageLabel: string | null;
  textExtractionStatus: string | null;
  excerpt: string | null;
  matchTerms: string[];
  rankingScore: number;
  rankingReason: string | null;
  candidateOrigin: string | null;
  retrievalQueryId: string | null;
};

export type EvidenceSearchResponse = {
  projectId: string;
  queryText: string;
  queryType: string;
  retrievalQueryId: string | null;
  resultCount: number;
  results: EvidenceSearchResult[];
  message: string | null;
};

export type EvidenceCandidate = {
  evidenceCandidateId: string;
  projectId: string;
  retrievalQueryId: string | null;
  documentId: string;
  documentPageId: string | null;
  pageNumber: number | null;
  findingId: string | null;
  checklistItemId: string | null;
  candidateTitle: string;
  candidateExcerpt: string | null;
  matchTerms: string[];
  rankingScore: number;
  rankingReason: string | null;
  candidateStatus: string;
  candidateOrigin: string;
  reviewerNote: string | null;
  createdByName: string | null;
  createdAt: string | null;
  updatedAt: string | null;
  dismissedAt: string | null;
  promotedFindingId: string | null;
};

export type RetrievalQuery = {
  retrievalQueryId: string;
  projectId: string;
  queryText: string;
  queryType: string | null;
  filters: Record<string, unknown>;
  resultCount: number;
  relatedChecklistItemId: string | null;
  relatedFindingId: string | null;
  createdByName: string | null;
  createdAt: string | null;
};

export type PromoteResult = {
  finding: {
    findingId: string;
    projectId: string;
    title: string;
    category: string;
    riskLevel: string;
    evidenceStatus: string | null;
    humanReviewStatus: string;
    findingOrigin: string;
    sourceMode: string;
    createdByName: string | null;
  };
  citation: {
    evidenceCitationId: string;
    projectId: string;
    findingId: string;
    documentId: string;
    documentPageId: string | null;
    pageNumber: number | null;
    citationType: string;
    citationStatus: string;
  };
  candidate: EvidenceCandidate;
};

type MutationResult<T> = {
  ok: boolean;
  backendReachable: boolean;
  data?: T;
  error?: string;
};

function mapSearchResult(r: Record<string, unknown>): EvidenceSearchResult {
  return {
    documentId: r.document_id as string,
    documentName: r.document_name as string,
    documentType: (r.document_type as string) ?? null,
    chunkId: (r.chunk_id as string) ?? null,
    documentPageId: (r.document_page_id as string) ?? null,
    pageNumber: (r.page_number as number) ?? null,
    pageLabel: (r.page_label as string) ?? null,
    textExtractionStatus: (r.text_extraction_status as string) ?? null,
    excerpt: (r.excerpt as string) ?? null,
    matchTerms: (r.match_terms as string[]) ?? [],
    rankingScore: (r.ranking_score as number) ?? 0,
    rankingReason: (r.ranking_reason as string) ?? null,
    candidateOrigin: (r.candidate_origin as string) ?? null,
    retrievalQueryId: (r.retrieval_query_id as string) ?? null,
  };
}

function mapSearchResponse(
  raw: Record<string, unknown>,
): EvidenceSearchResponse {
  return {
    projectId: raw.project_id as string,
    queryText: raw.query_text as string,
    queryType: raw.query_type as string,
    retrievalQueryId: (raw.retrieval_query_id as string) ?? null,
    resultCount: (raw.result_count as number) ?? 0,
    results: ((raw.results as Record<string, unknown>[]) ?? []).map(
      mapSearchResult,
    ),
    message: (raw.message as string) ?? null,
  };
}

function mapCandidate(c: Record<string, unknown>): EvidenceCandidate {
  return {
    evidenceCandidateId: c.evidence_candidate_id as string,
    projectId: c.project_id as string,
    retrievalQueryId: (c.retrieval_query_id as string) ?? null,
    documentId: c.document_id as string,
    documentPageId: (c.document_page_id as string) ?? null,
    pageNumber: (c.page_number as number) ?? null,
    findingId: (c.finding_id as string) ?? null,
    checklistItemId: (c.checklist_item_id as string) ?? null,
    candidateTitle: c.candidate_title as string,
    candidateExcerpt: (c.candidate_excerpt as string) ?? null,
    matchTerms: (c.match_terms as string[]) ?? [],
    rankingScore: (c.ranking_score as number) ?? 0,
    rankingReason: (c.ranking_reason as string) ?? null,
    candidateStatus: c.candidate_status as string,
    candidateOrigin: c.candidate_origin as string,
    reviewerNote: (c.reviewer_note as string) ?? null,
    createdByName: (c.created_by_name as string) ?? null,
    createdAt: (c.created_at as string) ?? null,
    updatedAt: (c.updated_at as string) ?? null,
    dismissedAt: (c.dismissed_at as string) ?? null,
    promotedFindingId: (c.promoted_finding_id as string) ?? null,
  };
}

function mapRetrievalQuery(q: Record<string, unknown>): RetrievalQuery {
  return {
    retrievalQueryId: q.retrieval_query_id as string,
    projectId: q.project_id as string,
    queryText: q.query_text as string,
    queryType: (q.query_type as string) ?? null,
    filters: (q.filters as Record<string, unknown>) ?? {},
    resultCount: (q.result_count as number) ?? 0,
    relatedChecklistItemId: (q.related_checklist_item_id as string) ?? null,
    relatedFindingId: (q.related_finding_id as string) ?? null,
    createdByName: (q.created_by_name as string) ?? null,
    createdAt: (q.created_at as string) ?? null,
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
      error: "Backend unavailable. Start the API to use evidence retrieval.",
    };
  }
}

export type EvidenceSearchInput = {
  queryText: string;
  queryType?: string;
  filters?: {
    documentId?: string;
    documentType?: string;
    textExtractionStatus?: string;
    pageMin?: number;
    pageMax?: number;
    checklistItemId?: string;
    findingId?: string;
  };
  limit?: number;
};

export async function searchProjectEvidence(
  projectId: string,
  input: EvidenceSearchInput,
): Promise<MutationResult<EvidenceSearchResponse>> {
  const filters = input.filters ?? {};
  return postJson<EvidenceSearchResponse>(
    `/api/v1/projects/${projectId}/evidence-retrieval/search`,
    {
      query_text: input.queryText,
      query_type: input.queryType || "keyword",
      filters: {
        document_id: filters.documentId || null,
        document_type: filters.documentType || null,
        text_extraction_status: filters.textExtractionStatus || null,
        page_min: filters.pageMin ?? null,
        page_max: filters.pageMax ?? null,
        checklist_item_id: filters.checklistItemId || null,
        finding_id: filters.findingId || null,
      },
      limit: input.limit ?? 10,
    },
    mapSearchResponse,
  );
}

export async function searchProjectChunkEvidence(
  projectId: string,
  input: EvidenceSearchInput,
): Promise<MutationResult<EvidenceSearchResponse>> {
  // Keyword search over real-derived chunks (chunks built from indexed PDF page
  // text). Distinct from the page-text search above and never returns seeded
  // demo chunks. Results carry page-level citation context.
  const filters = input.filters ?? {};
  return postJson<EvidenceSearchResponse>(
    `/api/v1/projects/${projectId}/evidence-retrieval/chunk-search`,
    {
      query_text: input.queryText,
      filters: {
        document_id: filters.documentId || null,
        document_type: filters.documentType || null,
        page_min: filters.pageMin ?? null,
        page_max: filters.pageMax ?? null,
      },
      limit: input.limit ?? 10,
    },
    mapSearchResponse,
  );
}

export async function searchChecklistEvidence(
  projectId: string,
  checklistItemId: string,
): Promise<MutationResult<EvidenceSearchResponse>> {
  return postJson<EvidenceSearchResponse>(
    `/api/v1/projects/${projectId}/evidence-retrieval/checklist/${checklistItemId}`,
    {},
    mapSearchResponse,
  );
}

export async function searchFindingEvidence(
  projectId: string,
  findingId: string,
): Promise<MutationResult<EvidenceSearchResponse>> {
  return postJson<EvidenceSearchResponse>(
    `/api/v1/projects/${projectId}/evidence-retrieval/findings/${findingId}`,
    {},
    mapSearchResponse,
  );
}

export async function listProjectEvidenceCandidates(
  projectId: string,
  filters?: { candidateStatus?: string; findingId?: string },
): Promise<EvidenceCandidate[] | null> {
  const params = new URLSearchParams();
  if (filters?.candidateStatus)
    params.set("candidate_status", filters.candidateStatus);
  if (filters?.findingId) params.set("finding_id", filters.findingId);
  const query = params.toString() ? `?${params.toString()}` : "";
  const data = await safeFetch<Record<string, unknown>[]>(
    `/api/v1/projects/${projectId}/evidence-candidates${query}`,
  );
  if (!data) return null;
  return data.map(mapCandidate);
}

export async function getEvidenceCandidate(
  projectId: string,
  candidateId: string,
): Promise<EvidenceCandidate | null> {
  const data = await safeFetch<Record<string, unknown>>(
    `/api/v1/projects/${projectId}/evidence-candidates/${candidateId}`,
  );
  return data ? mapCandidate(data) : null;
}

export type SaveCandidateInput = {
  documentId: string;
  documentPageId?: string | null;
  pageNumber?: number | null;
  findingId?: string | null;
  checklistItemId?: string | null;
  retrievalQueryId?: string | null;
  candidateTitle: string;
  candidateExcerpt?: string | null;
  matchTerms?: string[];
  rankingScore?: number;
  rankingReason?: string | null;
  candidateOrigin?: string;
  reviewerNote?: string | null;
};

export async function saveEvidenceCandidate(
  projectId: string,
  input: SaveCandidateInput,
): Promise<MutationResult<EvidenceCandidate>> {
  return postJson<EvidenceCandidate>(
    `/api/v1/projects/${projectId}/evidence-candidates`,
    {
      document_id: input.documentId,
      document_page_id: input.documentPageId ?? null,
      page_number: input.pageNumber ?? null,
      finding_id: input.findingId ?? null,
      checklist_item_id: input.checklistItemId ?? null,
      retrieval_query_id: input.retrievalQueryId ?? null,
      candidate_title: input.candidateTitle,
      candidate_excerpt: input.candidateExcerpt ?? null,
      match_terms: input.matchTerms ?? [],
      ranking_score: input.rankingScore ?? 0,
      ranking_reason: input.rankingReason ?? null,
      candidate_origin: input.candidateOrigin || "manual_save",
      reviewer_note: input.reviewerNote ?? null,
    },
    mapCandidate,
  );
}

export async function updateEvidenceCandidate(
  projectId: string,
  candidateId: string,
  input: { candidateStatus?: string; reviewerNote?: string },
): Promise<MutationResult<EvidenceCandidate>> {
  try {
    const res = await fetch(
      `${API_BASE_URL}/api/v1/projects/${projectId}/evidence-candidates/${candidateId}`,
      {
        method: "PATCH",
        headers: authHeaders({ "Content-Type": "application/json" }),
        body: JSON.stringify({
          candidate_status: input.candidateStatus ?? null,
          reviewer_note: input.reviewerNote ?? null,
        }),
        cache: "no-store",
      },
    );
    if (!res.ok) {
      let detail = `Update failed (${res.status}).`;
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
      data: mapCandidate((await res.json()) as Record<string, unknown>),
    };
  } catch {
    return { ok: false, backendReachable: false, error: "Backend unavailable." };
  }
}

export async function dismissEvidenceCandidate(
  projectId: string,
  candidateId: string,
  note?: string,
): Promise<MutationResult<EvidenceCandidate>> {
  return postJson<EvidenceCandidate>(
    `/api/v1/projects/${projectId}/evidence-candidates/${candidateId}/dismiss`,
    { reviewer_note: note ?? null },
    mapCandidate,
  );
}

export type PromoteCandidateInput = {
  title?: string;
  category?: string;
  riskLevel?: string;
  evidenceStatus?: string;
  evidenceToFind?: string;
  reasonItMatters?: string;
  recommendedHumanAction?: string;
  reviewerNote?: string;
  citationExcerpt?: string;
  humanReviewStatus?: string;
};

export async function promoteCandidateToDraftFinding(
  projectId: string,
  candidateId: string,
  input: PromoteCandidateInput,
): Promise<MutationResult<PromoteResult>> {
  return postJson<PromoteResult>(
    `/api/v1/projects/${projectId}/evidence-candidates/${candidateId}/promote-to-draft-finding`,
    {
      title: input.title ?? null,
      category: input.category ?? null,
      risk_level: input.riskLevel ?? null,
      evidence_status: input.evidenceStatus ?? null,
      evidence_to_find: input.evidenceToFind ?? null,
      reason_it_matters: input.reasonItMatters ?? null,
      recommended_human_action: input.recommendedHumanAction ?? null,
      reviewer_note: input.reviewerNote ?? null,
      citation_excerpt: input.citationExcerpt ?? null,
      human_review_status: input.humanReviewStatus ?? null,
    },
    (raw) => ({
      finding: mapPromoteFinding(
        raw.finding as Record<string, unknown>,
      ),
      citation: mapPromoteCitation(
        raw.citation as Record<string, unknown>,
      ),
      candidate: mapCandidate(raw.candidate as Record<string, unknown>),
    }),
  );
}

function mapPromoteFinding(f: Record<string, unknown>): PromoteResult["finding"] {
  return {
    findingId: f.finding_id as string,
    projectId: f.project_id as string,
    title: f.title as string,
    category: f.category as string,
    riskLevel: f.risk_level as string,
    evidenceStatus: (f.evidence_status as string) ?? null,
    humanReviewStatus: f.human_review_status as string,
    findingOrigin: f.finding_origin as string,
    sourceMode: f.source_mode as string,
    createdByName: (f.created_by_name as string) ?? null,
  };
}

function mapPromoteCitation(
  c: Record<string, unknown>,
): PromoteResult["citation"] {
  return {
    evidenceCitationId: c.evidence_citation_id as string,
    projectId: c.project_id as string,
    findingId: c.finding_id as string,
    documentId: c.document_id as string,
    documentPageId: (c.document_page_id as string) ?? null,
    pageNumber: (c.page_number as number) ?? null,
    citationType: c.citation_type as string,
    citationStatus: c.citation_status as string,
  };
}

export async function listRetrievalQueries(
  projectId: string,
): Promise<RetrievalQuery[] | null> {
  const data = await safeFetch<Record<string, unknown>[]>(
    `/api/v1/projects/${projectId}/retrieval-queries`,
  );
  if (!data) return null;
  return data.map(mapRetrievalQuery);
}
