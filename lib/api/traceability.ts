import { safeFetch } from "./client";

// Phase 4A: read-only project-wide traceability. Data is backend-canonical and
// review-support only. It organizes existing links; it does not determine that a
// requirement is satisfied. Returns null when the backend is unavailable.

export type ProjectTraceabilitySourceLink = {
  type: string;
  id: string | null;
};

export type ProjectTraceabilityRow = {
  traceabilityRowId: string;
  checklistItemId: string | null;
  checklistTitle: string | null;
  checklistRequirement: string | null;
  checklistStatus: string | null;
  evidenceCandidateId: string | null;
  evidenceCitationId: string | null;
  documentId: string | null;
  documentName: string | null;
  documentPageId: string | null;
  pageNumber: number | null;
  citationExcerpt: string | null;
  findingId: string | null;
  findingTitle: string | null;
  findingStatus: string | null;
  workflowItemId: string | null;
  workflowItemTitle: string | null;
  workflowStatus: string | null;
  cadFindingId: string | null;
  planFindingId: string | null;
  planSheetId: string | null;
  reviewPacketId: string | null;
  reviewPacketItemId: string | null;
  relationshipType: string;
  relationshipSource: string;
  reviewerActionNeeded: boolean;
  sourceLinks: ProjectTraceabilitySourceLink[];
  notes: string | null;
};

export type ProjectTraceabilitySummary = {
  totalChecklistItems: number;
  checklistItemsWithLinkedEvidence: number;
  checklistItemsWithoutLinkedEvidence: number;
  totalEvidenceCitations: number;
  totalEvidenceCandidates: number;
  totalFindings: number;
  totalWorkflowItems: number;
  totalPacketItems: number;
  totalTraceabilityRows: number;
  rowsRequiringReviewerConfirmation: number;
};

export type ProjectTraceability = {
  projectId: string;
  generatedAt: string;
  limitationsNote: string;
  hasIndexedInformation: boolean;
  summary: ProjectTraceabilitySummary;
  rows: ProjectTraceabilityRow[];
};

type Json = Record<string, unknown>;

function mapRow(r: Json): ProjectTraceabilityRow {
  return {
    traceabilityRowId: r.traceability_row_id as string,
    checklistItemId: (r.checklist_item_id as string) ?? null,
    checklistTitle: (r.checklist_title as string) ?? null,
    checklistRequirement: (r.checklist_requirement as string) ?? null,
    checklistStatus: (r.checklist_status as string) ?? null,
    evidenceCandidateId: (r.evidence_candidate_id as string) ?? null,
    evidenceCitationId: (r.evidence_citation_id as string) ?? null,
    documentId: (r.document_id as string) ?? null,
    documentName: (r.document_name as string) ?? null,
    documentPageId: (r.document_page_id as string) ?? null,
    pageNumber: (r.page_number as number) ?? null,
    citationExcerpt: (r.citation_excerpt as string) ?? null,
    findingId: (r.finding_id as string) ?? null,
    findingTitle: (r.finding_title as string) ?? null,
    findingStatus: (r.finding_status as string) ?? null,
    workflowItemId: (r.workflow_item_id as string) ?? null,
    workflowItemTitle: (r.workflow_item_title as string) ?? null,
    workflowStatus: (r.workflow_status as string) ?? null,
    cadFindingId: (r.cad_finding_id as string) ?? null,
    planFindingId: (r.plan_finding_id as string) ?? null,
    planSheetId: (r.plan_sheet_id as string) ?? null,
    reviewPacketId: (r.review_packet_id as string) ?? null,
    reviewPacketItemId: (r.review_packet_item_id as string) ?? null,
    relationshipType: r.relationship_type as string,
    relationshipSource: r.relationship_source as string,
    reviewerActionNeeded: Boolean(r.reviewer_action_needed),
    sourceLinks: ((r.source_links as Json[]) ?? []).map((l) => ({
      type: l.type as string,
      id: (l.id as string) ?? null,
    })),
    notes: (r.notes as string) ?? null,
  };
}

function mapSummary(s: Json): ProjectTraceabilitySummary {
  return {
    totalChecklistItems: (s.total_checklist_items as number) ?? 0,
    checklistItemsWithLinkedEvidence:
      (s.checklist_items_with_linked_evidence as number) ?? 0,
    checklistItemsWithoutLinkedEvidence:
      (s.checklist_items_without_linked_evidence as number) ?? 0,
    totalEvidenceCitations: (s.total_evidence_citations as number) ?? 0,
    totalEvidenceCandidates: (s.total_evidence_candidates as number) ?? 0,
    totalFindings: (s.total_findings as number) ?? 0,
    totalWorkflowItems: (s.total_workflow_items as number) ?? 0,
    totalPacketItems: (s.total_packet_items as number) ?? 0,
    totalTraceabilityRows: (s.total_traceability_rows as number) ?? 0,
    rowsRequiringReviewerConfirmation:
      (s.rows_requiring_reviewer_confirmation as number) ?? 0,
  };
}

export async function getProjectTraceability(
  projectId: string,
): Promise<ProjectTraceability | null> {
  const data = await safeFetch<Json>(
    `/api/v1/projects/${projectId}/traceability`,
  );
  if (!data) return null;
  return {
    projectId: data.project_id as string,
    generatedAt: data.generated_at as string,
    limitationsNote: (data.limitations_note as string) ?? "",
    hasIndexedInformation: Boolean(data.has_indexed_information),
    summary: mapSummary((data.summary as Json) ?? {}),
    rows: ((data.rows as Json[]) ?? []).map(mapRow),
  };
}
