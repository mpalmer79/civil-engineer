import { API_BASE_URL, safeFetch, authHeaders} from "./client";

// Phase 4A/4B: read-only project-wide traceability plus reviewer review actions.
// Data is backend-canonical and review-support only. It organizes existing links
// and records reviewer review actions; it does not determine that a requirement is
// satisfied. Read calls return null when the backend is unavailable.

export type ProjectTraceabilitySourceLink = {
  type: string;
  id: string | null;
};

export type ProjectTraceabilityPacketContext = {
  reviewPacketId: string;
  reviewPacketTitle: string | null;
  reviewPacketItemId: string;
  reviewPacketSectionId: string | null;
  reviewPacketSectionTitle: string | null;
  packetItemStatus: string | null;
  packetItemSource: string | null;
  packetTraceabilityRelationship: string | null;
  packetSourceLink: ProjectTraceabilitySourceLink | null;
};

export type ProjectTraceabilityLatestAction = {
  actionId: string;
  actionType: string;
  reviewerNote: string | null;
  createdBy: string;
  createdAt: string;
};

export type ProjectTraceabilityRow = {
  traceabilityRowId: string;
  traceabilityRowKey: string;
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
  packetContexts: ProjectTraceabilityPacketContext[];
  packetContextCount: number;
  latestReviewAction: ProjectTraceabilityLatestAction | null;
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

export type ProjectTraceabilityHandoffReadiness = {
  totalTraceabilityRows: number;
  rowsWithLinkedEvidence: number;
  rowsWithoutLinkedEvidence: number;
  rowsWithReviewerAction: number;
  rowsNeedingMoreInformation: number;
  rowsFollowUpNeeded: number;
  rowsNotInPacket: number;
  packetContextCount: number;
  readyForReviewerHandoffCount: number;
  note: string;
};

export type ProjectTraceability = {
  projectId: string;
  generatedAt: string;
  limitationsNote: string;
  hasIndexedInformation: boolean;
  summary: ProjectTraceabilitySummary;
  handoffReadiness: ProjectTraceabilityHandoffReadiness;
  rows: ProjectTraceabilityRow[];
};

export type ProjectTraceabilityReviewAction = {
  actionId: string;
  projectId: string;
  traceabilityRowKey: string;
  actionType: string;
  reviewerNote: string | null;
  createdBy: string;
  relationshipType: string | null;
  createdAt: string;
};

// A reviewer review action records how a reviewer reviewed one traceability link.
// reviewer_confirmed_link confirms the link is useful for review only; it does not
// mean the requirement is satisfied, approved, certified, verified, or validated.
export type TraceabilityReviewActionInput = {
  actionType: string;
  reviewerNote?: string;
  createdBy?: string;
  checklistItemId?: string | null;
  evidenceCitationId?: string | null;
  evidenceCandidateId?: string | null;
  findingId?: string | null;
  workflowItemId?: string | null;
  reviewPacketItemId?: string | null;
  relationshipType?: string | null;
};

export type TraceabilityReviewActionResult = {
  ok: boolean;
  status: number;
  backendReachable: boolean;
  action?: ProjectTraceabilityReviewAction;
  error?: string;
};

type Json = Record<string, unknown>;

function mapSourceLink(
  l: Json | null | undefined,
): ProjectTraceabilitySourceLink | null {
  if (!l) return null;
  return { type: l.type as string, id: (l.id as string) ?? null };
}

function mapPacketContext(c: Json): ProjectTraceabilityPacketContext {
  return {
    reviewPacketId: c.review_packet_id as string,
    reviewPacketTitle: (c.review_packet_title as string) ?? null,
    reviewPacketItemId: c.review_packet_item_id as string,
    reviewPacketSectionId: (c.review_packet_section_id as string) ?? null,
    reviewPacketSectionTitle: (c.review_packet_section_title as string) ?? null,
    packetItemStatus: (c.packet_item_status as string) ?? null,
    packetItemSource: (c.packet_item_source as string) ?? null,
    packetTraceabilityRelationship:
      (c.packet_traceability_relationship as string) ?? null,
    packetSourceLink: mapSourceLink(c.packet_source_link as Json | null),
  };
}

function mapLatestAction(
  a: Json | null | undefined,
): ProjectTraceabilityLatestAction | null {
  if (!a) return null;
  return {
    actionId: a.action_id as string,
    actionType: a.action_type as string,
    reviewerNote: (a.reviewer_note as string) ?? null,
    createdBy: a.created_by as string,
    createdAt: a.created_at as string,
  };
}

function mapRow(r: Json): ProjectTraceabilityRow {
  return {
    traceabilityRowId: r.traceability_row_id as string,
    traceabilityRowKey: r.traceability_row_key as string,
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
    packetContexts: ((r.packet_contexts as Json[]) ?? []).map(mapPacketContext),
    packetContextCount: (r.packet_context_count as number) ?? 0,
    latestReviewAction: mapLatestAction(r.latest_review_action as Json | null),
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

function mapHandoffReadiness(h: Json): ProjectTraceabilityHandoffReadiness {
  return {
    totalTraceabilityRows: (h.total_traceability_rows as number) ?? 0,
    rowsWithLinkedEvidence: (h.rows_with_linked_evidence as number) ?? 0,
    rowsWithoutLinkedEvidence: (h.rows_without_linked_evidence as number) ?? 0,
    rowsWithReviewerAction: (h.rows_with_reviewer_action as number) ?? 0,
    rowsNeedingMoreInformation: (h.rows_needing_more_information as number) ?? 0,
    rowsFollowUpNeeded: (h.rows_follow_up_needed as number) ?? 0,
    rowsNotInPacket: (h.rows_not_in_packet as number) ?? 0,
    packetContextCount: (h.packet_context_count as number) ?? 0,
    readyForReviewerHandoffCount:
      (h.ready_for_reviewer_handoff_count as number) ?? 0,
    note: (h.note as string) ?? "",
  };
}

function mapReviewAction(a: Json): ProjectTraceabilityReviewAction {
  return {
    actionId: a.action_id as string,
    projectId: a.project_id as string,
    traceabilityRowKey: a.traceability_row_key as string,
    actionType: a.action_type as string,
    reviewerNote: (a.reviewer_note as string) ?? null,
    createdBy: a.created_by as string,
    relationshipType: (a.relationship_type as string) ?? null,
    createdAt: a.created_at as string,
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
    handoffReadiness: mapHandoffReadiness(
      (data.handoff_readiness as Json) ?? {},
    ),
    rows: ((data.rows as Json[]) ?? []).map(mapRow),
  };
}

export async function getTraceabilityReviewActions(
  projectId: string,
  traceabilityRowKey: string,
): Promise<ProjectTraceabilityReviewAction[]> {
  const data = await safeFetch<Json>(
    `/api/v1/projects/${projectId}/traceability/${traceabilityRowKey}/review-actions`,
  );
  if (!data) return [];
  return ((data.actions as Json[]) ?? []).map(mapReviewAction);
}

export async function recordTraceabilityReviewAction(
  projectId: string,
  traceabilityRowKey: string,
  input: TraceabilityReviewActionInput,
): Promise<TraceabilityReviewActionResult> {
  try {
    const res = await fetch(
      `${API_BASE_URL}/api/v1/projects/${projectId}/traceability/${traceabilityRowKey}/review-actions`,
      {
        method: "POST",
        headers: authHeaders({ "Content-Type": "application/json" }),
        body: JSON.stringify({
          action_type: input.actionType,
          reviewer_note: input.reviewerNote ?? null,
          created_by: input.createdBy ?? null,
          checklist_item_id: input.checklistItemId ?? null,
          evidence_citation_id: input.evidenceCitationId ?? null,
          evidence_candidate_id: input.evidenceCandidateId ?? null,
          finding_id: input.findingId ?? null,
          workflow_item_id: input.workflowItemId ?? null,
          review_packet_item_id: input.reviewPacketItemId ?? null,
          relationship_type: input.relationshipType ?? null,
        }),
        cache: "no-store",
      },
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
        status: res.status,
        backendReachable: true,
        error: detail,
      };
    }
    return {
      ok: true,
      status: res.status,
      backendReachable: true,
      action: mapReviewAction((await res.json()) as Json),
    };
  } catch {
    return {
      ok: false,
      status: 0,
      backendReachable: false,
      error:
        "The backend is not reachable. Start the API to record a traceability review action. Review actions are not simulated in the browser.",
    };
  }
}
