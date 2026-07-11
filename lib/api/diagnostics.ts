import { apiGetMapped, type ApiResult } from "./client";

// Production Foundations Sprint 10: deployment readiness and diagnostics. This
// client reads safe operational status only. No response carries a secret value,
// a database URL, an auth secret, object storage credentials, a token, a signed
// URL, or a raw file system path. Statuses are operational readiness indicators,
// never an approval, certification, compliance, or issue-resolution outcome.
//
// NEXT_PUBLIC_API_BASE_URL is the backend origin only (no /api/v1 path); this
// client appends the /api/v1 paths itself. Every reader returns an explicit
// ApiResult so the deployment status page renders a real unavailable state
// when a check cannot be read, never a static healthy status.

export type ReadinessCheck = {
  category: string;
  status: string;
  message: string;
};

export type Readiness = {
  status: string;
  service: string;
  version: string;
  demoMode: boolean;
  checks: ReadinessCheck[];
};

export type EnvironmentValidationItem = {
  category: string;
  key: string;
  status: string;
  severity: string;
  message: string;
  required: boolean;
  configured: boolean;
  publicHint: string | null;
  remediationHint: string | null;
};

export type EnvironmentValidation = {
  overallStatus: string;
  itemCount: number;
  statusCounts: Record<string, number>;
  items: EnvironmentValidationItem[];
};

export type StorageDiagnostics = {
  provider: string;
  configured: boolean;
  status: string;
  message: string;
  items: EnvironmentValidationItem[];
};

export type FrontendConfigDiagnostics = {
  apiPrefix: string;
  expectsBackendOriginOnly: boolean;
  frontendEnvVar: string;
  guidance: string[];
};

export type SecurityBoundaryDiagnostics = {
  summary: string;
  prohibitedOutcomeTerms: string[];
  diagnosticsAreOperationalOnly: boolean;
};

function mapItem(i: Record<string, unknown>): EnvironmentValidationItem {
  return {
    category: i.category as string,
    key: i.key as string,
    status: i.status as string,
    severity: i.severity as string,
    message: i.message as string,
    required: Boolean(i.required),
    configured: Boolean(i.configured),
    publicHint: (i.public_hint as string) ?? null,
    remediationHint: (i.remediation_hint as string) ?? null,
  };
}

export async function getReadiness(): Promise<ApiResult<Readiness>> {
  return apiGetMapped<Record<string, unknown>, Readiness>(
    "/api/v1/readiness",
    (data) => ({
      status: data.status as string,
      service: data.service as string,
      version: data.version as string,
      demoMode: Boolean(data.demo_mode),
      checks: ((data.checks as Record<string, unknown>[]) ?? []).map((c) => ({
        category: c.category as string,
        status: c.status as string,
        message: c.message as string,
      })),
    }),
  );
}

export async function getEnvironmentDiagnostics(): Promise<
  ApiResult<EnvironmentValidation>
> {
  return apiGetMapped<Record<string, unknown>, EnvironmentValidation>(
    "/api/v1/diagnostics/environment",
    (data) => ({
      overallStatus: data.overall_status as string,
      itemCount: data.item_count as number,
      statusCounts: (data.status_counts as Record<string, number>) ?? {},
      items: ((data.items as Record<string, unknown>[]) ?? []).map(mapItem),
    }),
  );
}

export async function getStorageDiagnostics(): Promise<
  ApiResult<StorageDiagnostics>
> {
  return apiGetMapped<Record<string, unknown>, StorageDiagnostics>(
    "/api/v1/diagnostics/storage",
    (data) => ({
      provider: data.provider as string,
      configured: Boolean(data.configured),
      status: data.status as string,
      message: data.message as string,
      items: ((data.items as Record<string, unknown>[]) ?? []).map(mapItem),
    }),
  );
}

export async function getFrontendConfigDiagnostics(): Promise<
  ApiResult<FrontendConfigDiagnostics>
> {
  return apiGetMapped<Record<string, unknown>, FrontendConfigDiagnostics>(
    "/api/v1/diagnostics/frontend-config",
    (data) => ({
      apiPrefix: data.api_prefix as string,
      expectsBackendOriginOnly: Boolean(data.expects_backend_origin_only),
      frontendEnvVar: data.frontend_env_var as string,
      guidance: (data.guidance as string[]) ?? [],
    }),
  );
}

export async function getSecurityBoundaryDiagnostics(): Promise<
  ApiResult<SecurityBoundaryDiagnostics>
> {
  return apiGetMapped<Record<string, unknown>, SecurityBoundaryDiagnostics>(
    "/api/v1/diagnostics/security-boundary",
    (data) => ({
      summary: data.summary as string,
      prohibitedOutcomeTerms: (data.prohibited_outcome_terms as string[]) ?? [],
      diagnosticsAreOperationalOnly: Boolean(
        data.diagnostics_are_operational_only,
      ),
    }),
  );
}
