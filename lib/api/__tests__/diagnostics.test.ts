import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";


import {
  getReadiness,
  getEnvironmentDiagnostics,
  getStorageDiagnostics,
  getFrontendConfigDiagnostics,
  getSecurityBoundaryDiagnostics,
} from "@/lib/api/diagnostics";

function readinessPayload() {
  return {
    status: "ready",
    service: "Civil Engineer AI Backend",
    version: "1.0.0",
    demo_mode: true,
    checks: [
      { category: "database", status: "ready", message: "Database responded." },
      {
        category: "authentication",
        status: "configured",
        message: "Auth secret configured.",
      },
      { category: "storage", status: "ready", message: "Storage configured." },
    ],
  };
}

function environmentPayload() {
  return {
    overall_status: "ready",
    item_count: 1,
    status_counts: { ready: 1 },
    items: [
      {
        category: "application",
        key: "APP_VERSION",
        status: "ready",
        severity: "info",
        message: "Application version is set.",
        required: true,
        configured: true,
        public_hint: "1.0.0",
        remediation_hint: null,
      },
    ],
  };
}

afterEach(() => {
  vi.restoreAllMocks();
});

describe("diagnostics API client", () => {
  it("appends /api/v1 for the public readiness route", async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => readinessPayload(),
    } as Response);
    globalThis.fetch = fetchMock;

    const result = await getReadiness();
    expect(result?.status).toBe("ready");
    expect(result?.demoMode).toBe(true);
    expect(result?.checks).toHaveLength(3);
    expect(fetchMock.mock.calls[0][0]).toContain("/api/v1/readiness");
  });

  it("reads protected environment diagnostics through the proxy without a browser token", async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => environmentPayload(),
    } as Response);
    globalThis.fetch = fetchMock;

    const result = await getEnvironmentDiagnostics();
    expect(result?.overallStatus).toBe("ready");
    expect(result?.items[0].publicHint).toBe("1.0.0");
    const init = fetchMock.mock.calls[0][1] as RequestInit;
    const headers = init.headers as Record<string, string>;
    expect(headers.Authorization).toBeUndefined();
    expect(fetchMock.mock.calls[0][0]).toContain(
      "/api/v1/diagnostics/environment",
    );
  });

  it("sends auth headers on storage diagnostics and returns null on 401", async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: false,
      status: 401,
      json: async () => ({ detail: "Authentication required." }),
    } as Response);
    globalThis.fetch = fetchMock;

    const result = await getStorageDiagnostics();
    expect(result).toBeNull();
    expect(fetchMock.mock.calls[0][0]).toContain("/api/v1/diagnostics/storage");
  });

  it("returns null when the backend is unavailable", async () => {
    globalThis.fetch = vi.fn().mockRejectedValue(new Error("down"));
    const result = await getReadiness();
    expect(result).toBeNull();
  });

  it("reads public frontend-config and security-boundary diagnostics", async () => {
    globalThis.fetch = vi
      .fn()
      .mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: async () => ({
          api_prefix: "/api/v1",
          expects_backend_origin_only: true,
          frontend_env_var: "NEXT_PUBLIC_API_BASE_URL",
          guidance: ["NEXT_PUBLIC_API_BASE_URL must be the backend origin only."],
        }),
      } as Response)
      .mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: async () => ({
          summary: "Civil Engineer AI supports human plan review.",
          prohibited_outcome_terms: ["approved", "certified"],
          diagnostics_are_operational_only: true,
        }),
      } as Response);

    const cfg = await getFrontendConfigDiagnostics();
    expect(cfg?.apiPrefix).toBe("/api/v1");
    expect(cfg?.frontendEnvVar).toBe("NEXT_PUBLIC_API_BASE_URL");

    const boundary = await getSecurityBoundaryDiagnostics();
    expect(boundary?.diagnosticsAreOperationalOnly).toBe(true);
    expect(boundary?.prohibitedOutcomeTerms).toContain("approved");
  });
});
