import { PROJECT_ID, apiGetMapped, type ApiResult } from "./client";

// Phase 3: document chunks and source evidence.
//
// Backend seed data is canonical for evidence starting in Phase 3. To avoid
// drift, the frontend does not duplicate the full chunk set. Read functions
// return a typed ApiResult so callers can distinguish an empty result from a
// failed request instead of collapsing both into an empty list.

export type ChunkItem = {
  chunkId: string;
  documentId: string;
  documentType: string;
  fileName: string;
  pageNumber: number | null;
  sectionHeading: string | null;
  chunkIndex: number;
  content: string;
  keywords: string[];
  relatedChecklistItems: string[];
  relatedFindings: string[];
};

export type EvidenceItem = {
  chunkId: string | null;
  documentId: string;
  fileName: string;
  documentType: string;
  pageNumber: number | null;
  sectionHeading: string | null;
  excerpt: string;
  relevanceReason: string;
  score: number;
  evidenceRole: string | null;
  safetyNote: string;
};

type ApiChunk = {
  chunk_id: string;
  document_id: string;
  document_type: string;
  file_name: string;
  page_number: number | null;
  section_heading: string | null;
  chunk_index: number;
  content: string;
  keywords: string[];
  related_checklist_items: string[];
  related_findings: string[];
};

type ApiEvidence = {
  chunk_id: string | null;
  document_id: string;
  file_name: string;
  document_type: string;
  page_number: number | null;
  section_heading: string | null;
  excerpt: string;
  relevance_reason: string;
  score: number;
  evidence_role: string | null;
  safety_note: string;
};

function mapChunk(c: ApiChunk): ChunkItem {
  return {
    chunkId: c.chunk_id,
    documentId: c.document_id,
    documentType: c.document_type,
    fileName: c.file_name,
    pageNumber: c.page_number,
    sectionHeading: c.section_heading,
    chunkIndex: c.chunk_index,
    content: c.content,
    keywords: c.keywords,
    relatedChecklistItems: c.related_checklist_items,
    relatedFindings: c.related_findings,
  };
}

function mapEvidence(e: ApiEvidence): EvidenceItem {
  return {
    chunkId: e.chunk_id,
    documentId: e.document_id,
    fileName: e.file_name,
    documentType: e.document_type,
    pageNumber: e.page_number,
    sectionHeading: e.section_heading,
    excerpt: e.excerpt,
    relevanceReason: e.relevance_reason,
    score: e.score,
    evidenceRole: e.evidence_role,
    safetyNote: e.safety_note,
  };
}

export async function getProjectChunks(): Promise<ApiResult<ChunkItem[]>> {
  return apiGetMapped<ApiChunk[], ChunkItem[]>(
    `/api/v1/projects/${PROJECT_ID}/chunks`,
    (data) => data.map(mapChunk),
  );
}

export async function getFindingEvidence(
  findingId: string,
): Promise<ApiResult<EvidenceItem[]>> {
  return apiGetMapped<ApiEvidence[], EvidenceItem[]>(
    `/api/v1/projects/${PROJECT_ID}/findings/${findingId}/evidence`,
    (data) => data.map(mapEvidence),
  );
}

export async function getChecklistEvidence(
  checklistItemId: string,
): Promise<ApiResult<EvidenceItem[]>> {
  return apiGetMapped<ApiEvidence[], EvidenceItem[]>(
    `/api/v1/projects/${PROJECT_ID}/checklist/${checklistItemId}/evidence`,
    (data) => data.map(mapEvidence),
  );
}

export async function searchEvidence(
  query: string,
): Promise<ApiResult<EvidenceItem[]>> {
  return apiGetMapped<ApiEvidence[], EvidenceItem[]>(
    `/api/v1/projects/${PROJECT_ID}/search?query=${encodeURIComponent(query)}`,
    (data) => data.map(mapEvidence),
  );
}

// Fetch evidence for many findings in parallel, keyed by finding id. This
// enriches the public Brookside Meadows findings page, whose primary data
// already discloses its source; a failed enrichment degrades to empty
// evidence lists rather than substituting fixture data.
export async function getEvidenceByFinding(
  findingIds: string[],
): Promise<Record<string, EvidenceItem[]>> {
  const entries = await Promise.all(
    findingIds.map(async (id) => {
      const result = await getFindingEvidence(id);
      return [id, result.ok ? result.data : []] as const;
    }),
  );
  return Object.fromEntries(entries);
}

// Group seeded chunks by document id for the public demo documents page. The
// page shows a DataSourceNotice for its primary data; a failed chunk fetch
// degrades to an empty enrichment (the existing empty-state note renders).
export async function getChunksByDocument(): Promise<Record<string, ChunkItem[]>> {
  const result = await getProjectChunks();
  const grouped: Record<string, ChunkItem[]> = {};
  if (!result.ok) return grouped;
  for (const chunk of result.data) {
    (grouped[chunk.documentId] ??= []).push(chunk);
  }
  return grouped;
}

// Group chunks by checklist item for the public demo checklist page evidence
// panels. Same public-demo policy as getChunksByDocument: failure degrades to
// an empty enrichment, never to substituted fixture data.
export async function getChunksByChecklistItem(): Promise<
  Record<string, ChunkItem[]>
> {
  const result = await getProjectChunks();
  const grouped: Record<string, ChunkItem[]> = {};
  if (!result.ok) return grouped;
  for (const chunk of result.data) {
    for (const itemId of chunk.relatedChecklistItems) {
      (grouped[itemId] ??= []).push(chunk);
    }
  }
  return grouped;
}
