import { PROJECT_ID, safeFetch } from "./client";

// Phase 3: document chunks and source evidence.
//
// Backend seed data is canonical for evidence starting in Phase 3. To avoid
// drift, the frontend does not duplicate the full chunk set. When the backend
// is unavailable these functions return empty results and the UI shows an
// evidence status note rather than stale data.

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

export async function getProjectChunks(): Promise<ChunkItem[]> {
  const data = await safeFetch<ApiChunk[]>(
    `/api/v1/projects/${PROJECT_ID}/chunks`,
  );
  return data ? data.map(mapChunk) : [];
}

export async function getFindingEvidence(
  findingId: string,
): Promise<EvidenceItem[]> {
  const data = await safeFetch<ApiEvidence[]>(
    `/api/v1/projects/${PROJECT_ID}/findings/${findingId}/evidence`,
  );
  return data ? data.map(mapEvidence) : [];
}

export async function getChecklistEvidence(
  checklistItemId: string,
): Promise<EvidenceItem[]> {
  const data = await safeFetch<ApiEvidence[]>(
    `/api/v1/projects/${PROJECT_ID}/checklist/${checklistItemId}/evidence`,
  );
  return data ? data.map(mapEvidence) : [];
}

export async function searchEvidence(query: string): Promise<EvidenceItem[]> {
  const data = await safeFetch<ApiEvidence[]>(
    `/api/v1/projects/${PROJECT_ID}/search?query=${encodeURIComponent(query)}`,
  );
  return data ? data.map(mapEvidence) : [];
}

// Fetch evidence for many findings in parallel, keyed by finding id.
export async function getEvidenceByFinding(
  findingIds: string[],
): Promise<Record<string, EvidenceItem[]>> {
  const entries = await Promise.all(
    findingIds.map(
      async (id) => [id, await getFindingEvidence(id)] as const,
    ),
  );
  return Object.fromEntries(entries);
}

// Group seeded chunks by document id for the documents page.
export async function getChunksByDocument(): Promise<Record<string, ChunkItem[]>> {
  const chunks = await getProjectChunks();
  const grouped: Record<string, ChunkItem[]> = {};
  for (const chunk of chunks) {
    (grouped[chunk.documentId] ??= []).push(chunk);
  }
  return grouped;
}

// Group chunks by checklist item for the checklist page evidence panels.
export async function getChunksByChecklistItem(): Promise<
  Record<string, ChunkItem[]>
> {
  const chunks = await getProjectChunks();
  const grouped: Record<string, ChunkItem[]> = {};
  for (const chunk of chunks) {
    for (const itemId of chunk.relatedChecklistItems) {
      (grouped[itemId] ??= []).push(chunk);
    }
  }
  return grouped;
}
