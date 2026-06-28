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
