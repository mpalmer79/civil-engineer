import { API_BASE_URL, authHeaders, safeFetch } from "./client";

// Production Foundations Sprint 7: resubmittal rounds. Registering a resubmittal
// round records an applicant submission for reviewer review. It never decides
// whether the resubmittal satisfies engineering requirements and never resolves
// or closes anything. Read calls return null when the backend is unavailable;
// mutating calls return a clear { ok, error } result.
//
// NEXT_PUBLIC_API_BASE_URL is the backend origin only (no /api/v1 path); this
// client appends the /api/v1 paths itself.

export type ResubmittalRound = {
  resubmittalRoundId: string;
  projectId: string;
  responseMatrixId: string | null;
  roundNumber: number;
  roundLabel: string;
  receivedAt: string | null;
  submittedByName: string | null;
  submittedByOrganization: string | null;
  status: string;
  summary: string | null;
  documentIds: string[];
  carriedForwardItemIds: string[];
  documentCount: number;
  carriedForwardItemCount: number;
  createdByName: string | null;
  createdAt: string | null;
  updatedAt: string | null;
};

export type ResubmittalRoundSummary = {
  resubmittalRoundId: string;
  projectId: string;
  roundNumber: number;
  status: string;
  documentCount: number;
  carriedForwardItemCount: number;
  matrixItemCount: number;
  applicantResponseSummary: Record<string, number>;
  carryForwardSummary: Record<string, number>;
};

type MutationResult<T> = {
  ok: boolean;
  backendReachable: boolean;
  data?: T;
  error?: string;
};

function mapRound(r: Record<string, unknown>): ResubmittalRound {
  return {
    resubmittalRoundId: r.resubmittal_round_id as string,
    projectId: r.project_id as string,
    responseMatrixId: (r.response_matrix_id as string) ?? null,
    roundNumber: (r.round_number as number) ?? 1,
    roundLabel: r.round_label as string,
    receivedAt: (r.received_at as string) ?? null,
    submittedByName: (r.submitted_by_name as string) ?? null,
    submittedByOrganization: (r.submitted_by_organization as string) ?? null,
    status: r.status as string,
    summary: (r.summary as string) ?? null,
    documentIds: (r.document_ids as string[]) ?? [],
    carriedForwardItemIds: (r.carried_forward_item_ids as string[]) ?? [],
    documentCount: (r.document_count as number) ?? 0,
    carriedForwardItemCount: (r.carried_forward_item_count as number) ?? 0,
    createdByName: (r.created_by_name as string) ?? null,
    createdAt: (r.created_at as string) ?? null,
    updatedAt: (r.updated_at as string) ?? null,
  };
}

function mapSummary(s: Record<string, unknown>): ResubmittalRoundSummary {
  return {
    resubmittalRoundId: s.resubmittal_round_id as string,
    projectId: s.project_id as string,
    roundNumber: (s.round_number as number) ?? 1,
    status: s.status as string,
    documentCount: (s.document_count as number) ?? 0,
    carriedForwardItemCount: (s.carried_forward_item_count as number) ?? 0,
    matrixItemCount: (s.matrix_item_count as number) ?? 0,
    applicantResponseSummary:
      (s.applicant_response_summary as Record<string, number>) ?? {},
    carryForwardSummary:
      (s.carry_forward_summary as Record<string, number>) ?? {},
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
      error: "Backend unavailable. Start the API to use resubmittal rounds.",
    };
  }
}

export async function listResubmittalRounds(
  projectId: string,
): Promise<ResubmittalRound[] | null> {
  const data = await safeFetch<Record<string, unknown>[]>(
    `/api/v1/projects/${projectId}/resubmittal-rounds`,
  );
  if (!data) return null;
  return data.map(mapRound);
}

export async function registerResubmittalRound(
  projectId: string,
  payload: {
    roundLabel?: string;
    submittedByName?: string;
    submittedByOrganization?: string;
    responseMatrixId?: string;
    summary?: string;
  },
): Promise<MutationResult<ResubmittalRound>> {
  return postJson<ResubmittalRound>(
    `/api/v1/projects/${projectId}/resubmittal-rounds`,
    {
      round_label: payload.roundLabel ?? null,
      submitted_by_name: payload.submittedByName ?? null,
      submitted_by_organization: payload.submittedByOrganization ?? null,
      response_matrix_id: payload.responseMatrixId ?? null,
      summary: payload.summary ?? null,
    },
    mapRound,
  );
}

export async function getResubmittalRound(
  projectId: string,
  roundId: string,
): Promise<ResubmittalRound | null> {
  const data = await safeFetch<Record<string, unknown>>(
    `/api/v1/projects/${projectId}/resubmittal-rounds/${roundId}`,
  );
  return data ? mapRound(data) : null;
}

export async function linkDocumentToResubmittalRound(
  projectId: string,
  roundId: string,
  documentId: string,
  payload?: { reviewerNote?: string },
): Promise<MutationResult<ResubmittalRound>> {
  return postJson<ResubmittalRound>(
    `/api/v1/projects/${projectId}/resubmittal-rounds/${roundId}/documents/${documentId}`,
    { reviewer_note: payload?.reviewerNote ?? null },
    mapRound,
  );
}

export async function carryForwardItemsToRound(
  projectId: string,
  roundId: string,
  payload: { matrixItemIds: string[]; carryForwardStatus?: string },
): Promise<MutationResult<ResubmittalRound>> {
  return postJson<ResubmittalRound>(
    `/api/v1/projects/${projectId}/resubmittal-rounds/${roundId}/carry-forward-items`,
    {
      matrix_item_ids: payload.matrixItemIds,
      carry_forward_status: payload.carryForwardStatus ?? null,
    },
    mapRound,
  );
}

export async function getResubmittalRoundSummary(
  projectId: string,
  roundId: string,
): Promise<ResubmittalRoundSummary | null> {
  const data = await safeFetch<Record<string, unknown>>(
    `/api/v1/projects/${projectId}/resubmittal-rounds/${roundId}/summary`,
  );
  return data ? mapSummary(data) : null;
}
