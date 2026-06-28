import { API_BASE_URL, authHeaders } from "./client";

// Public pilot / design-partner request client. A pilot request is a public
// lead, not tenant-owned project data. This client only submits a request to the
// backend; it sends no data to any third-party service and never logs the form
// contents. NEXT_PUBLIC_API_BASE_URL is the backend origin only; the /api/v1
// path is appended here.

export type PilotInterestLevel = "exploring" | "evaluating" | "ready_to_pilot";

export type PilotRequestInput = {
  fullName: string;
  workEmail: string;
  firmName: string;
  roleTitle: string;
  projectType: string;
  primaryPain: string;
  interestLevel: PilotInterestLevel;
  notes?: string;
  hasSamplePackage: boolean;
};

export type PilotRequestAck = {
  pilotRequestId: string;
  received: boolean;
  message: string;
};

// Operator pipeline statuses for a design-partner conversation. Outreach state
// only; no review-support or engineering meaning.
export const PILOT_STATUSES = [
  "new",
  "contacted",
  "qualified",
  "active_pilot",
  "closed",
  "rejected",
] as const;

export type PilotStatus = (typeof PILOT_STATUSES)[number];

// A stored pilot lead, as returned to an authorized operator. No file content is
// ever included; has_sample_package is a boolean flag only. internal_notes are
// operator-only and are never returned by the public submission endpoint.
export type PilotRequestRecord = {
  pilotRequestId: string;
  fullName: string;
  workEmail: string;
  firmName: string;
  roleTitle: string;
  projectType: string;
  primaryPain: string;
  interestLevel: string;
  notes: string | null;
  hasSamplePackage: boolean;
  status: string;
  internalNotes: string | null;
  lastContactedAt: string | null;
  createdAt: string | null;
  updatedAt: string | null;
};

// Discriminated result so the admin view can render an honest state for each
// outcome without ever exposing a raw error or a stack trace.
export type PilotListResult =
  | { status: "ok"; data: PilotRequestRecord[] }
  | { status: "unauthorized" }
  | { status: "forbidden" }
  | { status: "unreachable" }
  | { status: "error"; message: string };

function mapPilotRecord(raw: Record<string, unknown>): PilotRequestRecord {
  return {
    pilotRequestId: (raw.pilot_request_id as string) ?? "",
    fullName: (raw.full_name as string) ?? "",
    workEmail: (raw.work_email as string) ?? "",
    firmName: (raw.firm_name as string) ?? "",
    roleTitle: (raw.role_title as string) ?? "",
    projectType: (raw.project_type as string) ?? "",
    primaryPain: (raw.primary_pain as string) ?? "",
    interestLevel: (raw.interest_level as string) ?? "",
    notes: (raw.notes as string) ?? null,
    hasSamplePackage: (raw.has_sample_package as boolean) ?? false,
    status: (raw.status as string) ?? "new",
    internalNotes: (raw.internal_notes as string) ?? null,
    lastContactedAt: (raw.last_contacted_at as string) ?? null,
    createdAt: (raw.created_at as string) ?? null,
    updatedAt: (raw.updated_at as string) ?? null,
  };
}

// Result of an operator mutation (status/notes). Mirrors the list result's honest
// states so the admin UI never shows a raw error.
export type PilotMutationResult =
  | { status: "ok"; data: PilotRequestRecord }
  | { status: "unauthorized" }
  | { status: "forbidden" }
  | { status: "unreachable" }
  | { status: "error"; message: string };

async function pilotPatch(
  path: string,
  body: unknown,
): Promise<PilotMutationResult> {
  try {
    const res = await fetch(`${API_BASE_URL}/api/v1/pilot-requests${path}`, {
      method: "PATCH",
      headers: authHeaders({ "Content-Type": "application/json" }),
      body: JSON.stringify(body),
      cache: "no-store",
    });
    if (res.status === 401) return { status: "unauthorized" };
    if (res.status === 403) return { status: "forbidden" };
    if (!res.ok) {
      return { status: "error", message: `Request failed (${res.status}).` };
    }
    const raw = (await res.json()) as Record<string, unknown>;
    return { status: "ok", data: mapPilotRecord(raw) };
  } catch {
    return { status: "unreachable" };
  }
}

export function updatePilotRequestStatus(
  pilotRequestId: string,
  status: PilotStatus,
  markContacted = false,
): Promise<PilotMutationResult> {
  return pilotPatch(`/${pilotRequestId}/status`, {
    status,
    mark_contacted: markContacted,
  });
}

export function updatePilotRequestNotes(
  pilotRequestId: string,
  internalNotes: string,
): Promise<PilotMutationResult> {
  return pilotPatch(`/${pilotRequestId}/notes`, {
    internal_notes: internalNotes,
  });
}

// CSV export. Returns the raw CSV text for an authorized operator so the caller
// can trigger a client-side download. No data leaves this app.
export type PilotExportResult =
  | { status: "ok"; csv: string }
  | { status: "unauthorized" }
  | { status: "forbidden" }
  | { status: "unreachable" }
  | { status: "error"; message: string };

export async function exportPilotRequestsCsv(): Promise<PilotExportResult> {
  try {
    const res = await fetch(`${API_BASE_URL}/api/v1/pilot-requests/export`, {
      headers: authHeaders(),
      cache: "no-store",
    });
    if (res.status === 401) return { status: "unauthorized" };
    if (res.status === 403) return { status: "forbidden" };
    if (!res.ok) {
      return { status: "error", message: `Request failed (${res.status}).` };
    }
    return { status: "ok", csv: await res.text() };
  } catch {
    return { status: "unreachable" };
  }
}

export async function listPilotRequests(): Promise<PilotListResult> {
  try {
    const res = await fetch(`${API_BASE_URL}/api/v1/pilot-requests`, {
      headers: authHeaders(),
      cache: "no-store",
    });
    if (res.status === 401) return { status: "unauthorized" };
    if (res.status === 403) return { status: "forbidden" };
    if (!res.ok) {
      return { status: "error", message: `Request failed (${res.status}).` };
    }
    const raw = (await res.json()) as Record<string, unknown>[];
    return { status: "ok", data: raw.map(mapPilotRecord) };
  } catch {
    return { status: "unreachable" };
  }
}

export type PilotSubmitResult = {
  ok: boolean;
  backendReachable: boolean;
  data?: PilotRequestAck;
  error?: string;
};

export async function submitPilotRequest(
  input: PilotRequestInput,
): Promise<PilotSubmitResult> {
  // Map to the backend snake_case schema. has_sample_package is a boolean flag
  // only; no file content is sent.
  const body = {
    full_name: input.fullName,
    work_email: input.workEmail,
    firm_name: input.firmName,
    role_title: input.roleTitle,
    project_type: input.projectType,
    primary_pain: input.primaryPain,
    interest_level: input.interestLevel,
    notes: input.notes ? input.notes : null,
    has_sample_package: input.hasSamplePackage,
  };

  try {
    const res = await fetch(`${API_BASE_URL}/api/v1/pilot-requests`, {
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
    const raw = (await res.json()) as Record<string, unknown>;
    return {
      ok: true,
      backendReachable: true,
      data: {
        pilotRequestId: (raw.pilot_request_id as string) ?? "",
        received: (raw.received as boolean) ?? true,
        message: (raw.message as string) ?? "",
      },
    };
  } catch {
    return {
      ok: false,
      backendReachable: false,
      error:
        "We could not reach the server to record your request. Please try again, or reach out directly.",
    };
  }
}
