import { API_BASE_URL, authHeaders, safeFetch } from "./client";
import type { EvidenceSearchResponse } from "./evidenceRetrieval";

// Production Foundations Sprint 4: checklist-driven evidence review and rule
// pack foundation. This data is backend-canonical. Read calls return null when
// the backend is unavailable; mutating calls return a clear { ok, error }
// result.
//
// A rule pack is a reusable review-support template, not a legal ordinance and
// not a compliance standard. Checklist status is review-support only. There are
// no live AI calls.
//
// NEXT_PUBLIC_API_BASE_URL is the backend origin only (no /api/v1 path); this
// client appends the /api/v1 paths itself.

export type RulePackItem = {
  rulePackItemId: string;
  rulePackId: string;
  itemCode: string;
  category: string;
  requirementText: string;
  expectedEvidence: string;
  applicabilityNote: string | null;
  riskLevel: string;
  reviewDomain: string;
  referenceLabel: string | null;
  sortOrder: number;
  isActive: boolean;
};

export type RulePack = {
  rulePackId: string;
  name: string;
  jurisdictionName: string;
  reviewDomain: string;
  description: string | null;
  versionLabel: string;
  sourceMode: string;
  isActive: boolean;
  createdByName: string | null;
  createdAt: string | null;
  updatedAt: string | null;
  itemCount: number;
  items?: RulePackItem[];
};

export type ProjectChecklist = {
  projectChecklistId: string;
  projectId: string;
  rulePackId: string | null;
  name: string;
  status: string;
  sourceMode: string;
  createdByName: string | null;
  createdAt: string | null;
  updatedAt: string | null;
  itemCount: number;
  evidenceStatusSummary: Record<string, number>;
  reviewStatusSummary: Record<string, number>;
  items?: ProjectChecklistItem[];
};

export type ProjectChecklistItem = {
  projectChecklistItemId: string;
  projectChecklistId: string;
  projectId: string;
  rulePackItemId: string | null;
  itemCode: string;
  category: string;
  requirementText: string;
  expectedEvidence: string;
  applicabilityStatus: string;
  evidenceStatus: string;
  reviewStatus: string;
  riskLevel: string;
  reviewerNote: string | null;
  relatedFindingId: string | null;
  sortOrder: number;
  reviewedByName: string | null;
  reviewedAt: string | null;
  createdAt: string | null;
  updatedAt: string | null;
};

export type ChecklistDraftFindingResult = {
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
    relatedChecklistItems: string[];
    createdByName: string | null;
  };
  citation: {
    evidenceCitationId: string;
    findingId: string;
    documentId: string;
    pageNumber: number | null;
    citationType: string;
    citationStatus: string;
    citationContext: string;
  } | null;
  checklistItem: ProjectChecklistItem;
};

type MutationResult<T> = {
  ok: boolean;
  backendReachable: boolean;
  data?: T;
  error?: string;
};

function mapRulePackItem(i: Record<string, unknown>): RulePackItem {
  return {
    rulePackItemId: i.rule_pack_item_id as string,
    rulePackId: i.rule_pack_id as string,
    itemCode: i.item_code as string,
    category: i.category as string,
    requirementText: i.requirement_text as string,
    expectedEvidence: i.expected_evidence as string,
    applicabilityNote: (i.applicability_note as string) ?? null,
    riskLevel: i.risk_level as string,
    reviewDomain: i.review_domain as string,
    referenceLabel: (i.reference_label as string) ?? null,
    sortOrder: (i.sort_order as number) ?? 0,
    isActive: (i.is_active as boolean) ?? true,
  };
}

function mapRulePack(p: Record<string, unknown>): RulePack {
  return {
    rulePackId: p.rule_pack_id as string,
    name: p.name as string,
    jurisdictionName: p.jurisdiction_name as string,
    reviewDomain: p.review_domain as string,
    description: (p.description as string) ?? null,
    versionLabel: p.version_label as string,
    sourceMode: p.source_mode as string,
    isActive: (p.is_active as boolean) ?? true,
    createdByName: (p.created_by_name as string) ?? null,
    createdAt: (p.created_at as string) ?? null,
    updatedAt: (p.updated_at as string) ?? null,
    itemCount: (p.item_count as number) ?? 0,
    items: Array.isArray(p.items)
      ? (p.items as Record<string, unknown>[]).map(mapRulePackItem)
      : undefined,
  };
}

function mapChecklistItem(i: Record<string, unknown>): ProjectChecklistItem {
  return {
    projectChecklistItemId: i.project_checklist_item_id as string,
    projectChecklistId: i.project_checklist_id as string,
    projectId: i.project_id as string,
    rulePackItemId: (i.rule_pack_item_id as string) ?? null,
    itemCode: i.item_code as string,
    category: i.category as string,
    requirementText: i.requirement_text as string,
    expectedEvidence: i.expected_evidence as string,
    applicabilityStatus: i.applicability_status as string,
    evidenceStatus: i.evidence_status as string,
    reviewStatus: i.review_status as string,
    riskLevel: i.risk_level as string,
    reviewerNote: (i.reviewer_note as string) ?? null,
    relatedFindingId: (i.related_finding_id as string) ?? null,
    sortOrder: (i.sort_order as number) ?? 0,
    reviewedByName: (i.reviewed_by_name as string) ?? null,
    reviewedAt: (i.reviewed_at as string) ?? null,
    createdAt: (i.created_at as string) ?? null,
    updatedAt: (i.updated_at as string) ?? null,
  };
}

function mapChecklist(c: Record<string, unknown>): ProjectChecklist {
  return {
    projectChecklistId: c.project_checklist_id as string,
    projectId: c.project_id as string,
    rulePackId: (c.rule_pack_id as string) ?? null,
    name: c.name as string,
    status: c.status as string,
    sourceMode: c.source_mode as string,
    createdByName: (c.created_by_name as string) ?? null,
    createdAt: (c.created_at as string) ?? null,
    updatedAt: (c.updated_at as string) ?? null,
    itemCount: (c.item_count as number) ?? 0,
    evidenceStatusSummary:
      (c.evidence_status_summary as Record<string, number>) ?? {},
    reviewStatusSummary:
      (c.review_status_summary as Record<string, number>) ?? {},
    items: Array.isArray(c.items)
      ? (c.items as Record<string, unknown>[]).map(mapChecklistItem)
      : undefined,
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
      error: "Backend unavailable. Start the API to use checklist review.",
    };
  }
}

export async function listRulePacks(): Promise<RulePack[] | null> {
  const data = await safeFetch<Record<string, unknown>[]>("/api/v1/rule-packs");
  if (!data) return null;
  return data.map(mapRulePack);
}

export async function getRulePack(
  rulePackId: string,
): Promise<RulePack | null> {
  const data = await safeFetch<Record<string, unknown>>(
    `/api/v1/rule-packs/${rulePackId}`,
  );
  return data ? mapRulePack(data) : null;
}

export async function listProjectChecklists(
  projectId: string,
): Promise<ProjectChecklist[] | null> {
  const data = await safeFetch<Record<string, unknown>[]>(
    `/api/v1/projects/${projectId}/checklists`,
  );
  if (!data) return null;
  return data.map(mapChecklist);
}

export async function createProjectChecklistFromRulePack(
  projectId: string,
  payload: { rulePackId: string; name?: string },
): Promise<MutationResult<ProjectChecklist>> {
  return postJson<ProjectChecklist>(
    `/api/v1/projects/${projectId}/checklists/from-rule-pack`,
    { rule_pack_id: payload.rulePackId, name: payload.name ?? null },
    mapChecklist,
  );
}

export async function getProjectChecklist(
  projectId: string,
  checklistId: string,
): Promise<ProjectChecklist | null> {
  const data = await safeFetch<Record<string, unknown>>(
    `/api/v1/projects/${projectId}/checklists/${checklistId}`,
  );
  return data ? mapChecklist(data) : null;
}

export async function listProjectChecklistItems(
  projectId: string,
  checklistId: string,
): Promise<ProjectChecklistItem[] | null> {
  const data = await safeFetch<Record<string, unknown>[]>(
    `/api/v1/projects/${projectId}/checklists/${checklistId}/items`,
  );
  if (!data) return null;
  return data.map(mapChecklistItem);
}

export async function updateProjectChecklistItem(
  projectId: string,
  checklistItemId: string,
  payload: {
    applicabilityStatus?: string;
    evidenceStatus?: string;
    reviewStatus?: string;
    reviewerNote?: string;
  },
): Promise<MutationResult<ProjectChecklistItem>> {
  try {
    const res = await fetch(
      `${API_BASE_URL}/api/v1/projects/${projectId}/checklist-items/${checklistItemId}`,
      {
        method: "PATCH",
        headers: authHeaders({ "Content-Type": "application/json" }),
        body: JSON.stringify({
          applicability_status: payload.applicabilityStatus ?? null,
          evidence_status: payload.evidenceStatus ?? null,
          review_status: payload.reviewStatus ?? null,
          reviewer_note: payload.reviewerNote ?? null,
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
      data: mapChecklistItem((await res.json()) as Record<string, unknown>),
    };
  } catch {
    return { ok: false, backendReachable: false, error: "Backend unavailable." };
  }
}

export async function searchChecklistItemEvidence(
  projectId: string,
  checklistItemId: string,
  payload?: { queryText?: string; limit?: number },
): Promise<MutationResult<EvidenceSearchResponse>> {
  // Reuse the evidence search response mapper from the retrieval client by
  // mapping inline here to keep this module self-contained.
  return postJson<EvidenceSearchResponse>(
    `/api/v1/projects/${projectId}/checklist-items/${checklistItemId}/evidence-search`,
    {
      query_text: payload?.queryText ?? null,
      limit: payload?.limit ?? 10,
    },
    (raw) => ({
      projectId: raw.project_id as string,
      queryText: raw.query_text as string,
      queryType: raw.query_type as string,
      retrievalQueryId: (raw.retrieval_query_id as string) ?? null,
      resultCount: (raw.result_count as number) ?? 0,
      results: ((raw.results as Record<string, unknown>[]) ?? []).map((r) => ({
        documentId: r.document_id as string,
        documentName: r.document_name as string,
        documentType: (r.document_type as string) ?? null,
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
      })),
      message: (raw.message as string) ?? null,
    }),
  );
}

export async function linkChecklistEvidence(
  projectId: string,
  checklistItemId: string,
  payload: {
    documentId: string;
    documentPageId?: string;
    pageNumber?: number | null;
    evidenceCitationId?: string;
    evidenceCandidateId?: string;
    quotedExcerpt?: string;
    reviewerNote?: string;
    linkStatus?: string;
  },
): Promise<MutationResult<Record<string, unknown>>> {
  return postJson<Record<string, unknown>>(
    `/api/v1/projects/${projectId}/checklist-items/${checklistItemId}/evidence-links`,
    {
      document_id: payload.documentId,
      document_page_id: payload.documentPageId ?? null,
      page_number: payload.pageNumber ?? null,
      evidence_citation_id: payload.evidenceCitationId ?? null,
      evidence_candidate_id: payload.evidenceCandidateId ?? null,
      quoted_excerpt: payload.quotedExcerpt ?? null,
      reviewer_note: payload.reviewerNote ?? null,
      link_status: payload.linkStatus ?? "reviewer_selected",
    },
    (raw) => raw,
  );
}

export type CreateChecklistDraftFindingInput = {
  title?: string;
  category?: string;
  riskLevel?: string;
  evidenceStatus?: string;
  evidenceToFind?: string;
  reasonItMatters?: string;
  recommendedHumanAction?: string;
  reviewerNote?: string;
  humanReviewStatus?: string;
  documentId?: string;
  documentPageId?: string;
  pageNumber?: number | null;
  citationExcerpt?: string;
};

export async function createDraftFindingFromChecklistItem(
  projectId: string,
  checklistItemId: string,
  input: CreateChecklistDraftFindingInput,
): Promise<MutationResult<ChecklistDraftFindingResult>> {
  return postJson<ChecklistDraftFindingResult>(
    `/api/v1/projects/${projectId}/checklist-items/${checklistItemId}/draft-finding`,
    {
      title: input.title ?? null,
      category: input.category ?? null,
      risk_level: input.riskLevel ?? null,
      evidence_status: input.evidenceStatus ?? null,
      evidence_to_find: input.evidenceToFind ?? null,
      reason_it_matters: input.reasonItMatters ?? null,
      recommended_human_action: input.recommendedHumanAction ?? null,
      reviewer_note: input.reviewerNote ?? null,
      human_review_status: input.humanReviewStatus ?? null,
      document_id: input.documentId ?? null,
      document_page_id: input.documentPageId ?? null,
      page_number: input.pageNumber ?? null,
      citation_excerpt: input.citationExcerpt ?? null,
    },
    (raw) => {
      const finding = raw.finding as Record<string, unknown>;
      const citation = raw.citation as Record<string, unknown> | null;
      return {
        finding: {
          findingId: finding.finding_id as string,
          projectId: finding.project_id as string,
          title: finding.title as string,
          category: finding.category as string,
          riskLevel: finding.risk_level as string,
          evidenceStatus: (finding.evidence_status as string) ?? null,
          humanReviewStatus: finding.human_review_status as string,
          findingOrigin: finding.finding_origin as string,
          sourceMode: finding.source_mode as string,
          relatedChecklistItems:
            (finding.related_checklist_items as string[]) ?? [],
          createdByName: (finding.created_by_name as string) ?? null,
        },
        citation: citation
          ? {
              evidenceCitationId: citation.evidence_citation_id as string,
              findingId: citation.finding_id as string,
              documentId: citation.document_id as string,
              pageNumber: (citation.page_number as number) ?? null,
              citationType: citation.citation_type as string,
              citationStatus: citation.citation_status as string,
              citationContext: citation.citation_context as string,
            }
          : null,
        checklistItem: mapChecklistItem(
          raw.checklist_item as Record<string, unknown>,
        ),
      };
    },
  );
}
