import {
  API_BASE_URL,
  apiGetMapped,
  authHeaders,
  hasSessionIndicator,
  requireArray,
  requireRecord,
  requireString,
  type ApiFailure,
  type ApiResult,
} from "./client";

// Authentication and access control client. The session lives in an HttpOnly
// cookie managed by the same-origin /api/session endpoints; browser JavaScript
// never sees the backend access token. Access control protects review records;
// it does not approve plans, certify compliance, or make any final engineering
// decision.

export type CurrentUser = {
  userId: string;
  email: string;
  displayName: string;
  isActive: boolean;
  isDemoUser: boolean;
  createdAt: string | null;
  lastLoginAt: string | null;
};

export type Organization = {
  organizationId: string;
  organizationName: string;
  organizationType: string;
  sourceMode: string;
  role: string | null;
  membershipId: string | null;
};

export type Membership = {
  membershipId: string;
  organizationId: string;
  userId: string;
  userEmail: string | null;
  displayName: string | null;
  role: string;
  isActive: boolean;
};

export type UserProject = {
  projectId: string;
  projectName: string;
  sourceMode: string;
  visibilityMode: string;
  demoPublic: boolean;
  organizationId: string | null;
  accessLevel: string | null;
};

export type ProjectAccessEntry = {
  projectAccessId: string;
  projectId: string;
  organizationId: string | null;
  userId: string | null;
  accessLevel: string;
  grantedByUserId: string | null;
  isActive: boolean;
  createdAt: string | null;
};

type MutationResult<T> = {
  ok: boolean;
  backendReachable: boolean;
  data?: T;
  error?: string;
};

function mapUser(u: Record<string, unknown>): CurrentUser {
  return {
    userId: u.user_id as string,
    email: u.email as string,
    displayName: u.display_name as string,
    isActive: (u.is_active as boolean) ?? true,
    isDemoUser: (u.is_demo_user as boolean) ?? false,
    createdAt: (u.created_at as string) ?? null,
    lastLoginAt: (u.last_login_at as string) ?? null,
  };
}

// Access control shapes are high risk, so the required identifiers are
// asserted at runtime. A structurally invalid payload becomes an explicit
// invalid_response failure through apiGetMapped instead of undefined fields.
function mapOrganization(o: Record<string, unknown>): Organization {
  return {
    organizationId: requireString(o.organization_id, "organization_id"),
    organizationName: requireString(o.organization_name, "organization_name"),
    organizationType: requireString(o.organization_type, "organization_type"),
    sourceMode: requireString(o.source_mode, "source_mode"),
    role: (o.role as string) ?? null,
    membershipId: (o.membership_id as string) ?? null,
  };
}

function mapMembership(m: Record<string, unknown>): Membership {
  return {
    membershipId: requireString(m.membership_id, "membership_id"),
    organizationId: requireString(m.organization_id, "organization_id"),
    userId: requireString(m.user_id, "user_id"),
    userEmail: (m.user_email as string) ?? null,
    displayName: (m.display_name as string) ?? null,
    role: requireString(m.role, "role"),
    isActive: (m.is_active as boolean) ?? true,
  };
}

function mapUserProject(p: Record<string, unknown>): UserProject {
  return {
    projectId: requireString(p.project_id, "project_id"),
    projectName: requireString(p.project_name, "project_name"),
    sourceMode: requireString(p.source_mode, "source_mode"),
    visibilityMode: requireString(p.visibility_mode, "visibility_mode"),
    demoPublic: (p.demo_public as boolean) ?? false,
    organizationId: (p.organization_id as string) ?? null,
    accessLevel: (p.access_level as string) ?? null,
  };
}

function mapAccess(a: Record<string, unknown>): ProjectAccessEntry {
  return {
    projectAccessId: requireString(a.project_access_id, "project_access_id"),
    projectId: requireString(a.project_id, "project_id"),
    organizationId: (a.organization_id as string) ?? null,
    userId: (a.user_id as string) ?? null,
    accessLevel: requireString(a.access_level, "access_level"),
    grantedByUserId: (a.granted_by_user_id as string) ?? null,
    isActive: (a.is_active as boolean) ?? true,
    createdAt: (a.created_at as string) ?? null,
  };
}

async function authPost<T>(
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
      error: "Backend unavailable. Start the API to sign in.",
    };
  }
}

export type RegisterInput = {
  email: string;
  displayName: string;
  password: string;
  organizationName?: string;
  organizationType?: string;
};

type SessionResult = { user: CurrentUser };

// Session endpoints live on the Next.js origin (not the backend origin) so
// they can set and clear the HttpOnly session cookie.
function mapSessionResponse(raw: Record<string, unknown>): SessionResult {
  return { user: mapUser(raw.user as Record<string, unknown>) };
}

async function sessionPost<T>(
  path: string,
  body: unknown,
  mapper: (raw: Record<string, unknown>) => T,
): Promise<MutationResult<T>> {
  try {
    const res = await fetch(path, {
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
      return { ok: false, backendReachable: res.status !== 502, error: detail };
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
      error: "Backend unavailable. Start the API to sign in.",
    };
  }
}

export async function registerUser(
  input: RegisterInput,
): Promise<MutationResult<SessionResult>> {
  return sessionPost<SessionResult>(
    "/api/session/register",
    {
      email: input.email,
      display_name: input.displayName,
      password: input.password,
      organization_name: input.organizationName || null,
      organization_type: input.organizationType || null,
    },
    mapSessionResponse,
  );
}

export async function loginUser(
  email: string,
  password: string,
): Promise<MutationResult<SessionResult>> {
  return sessionPost<SessionResult>(
    "/api/session/login",
    { email, password },
    mapSessionResponse,
  );
}

export async function logoutUser(): Promise<void> {
  try {
    await fetch("/api/session/logout", {
      method: "POST",
      headers: authHeaders(),
      cache: "no-store",
    });
  } catch {
    // The indicator cookie may remain if the request failed; the next
    // authenticated call will still fail explicitly with 401.
  }
}

// Rendering optimization only: reflects the non-sensitive indicator cookie.
// It is never authorization truth; validated session state comes from
// getCurrentUser(), which calls the server-validated /api/session/status
// endpoint. Any backend 401 clears the indicator via the BFF.
export function isSignedIn(): boolean {
  return hasSessionIndicator();
}

export async function getCurrentUser(): Promise<CurrentUser | null> {
  // Skip the request when no indicator cookie exists; a stale indicator is
  // handled by the status endpoint, which validates and clears it.
  if (!hasSessionIndicator()) return null;
  try {
    const res = await fetch("/api/session/status", { cache: "no-store" });
    if (!res.ok) return null;
    const payload = (await res.json()) as {
      authenticated?: boolean;
      user?: Record<string, unknown> | null;
    };
    if (!payload.authenticated || !payload.user) return null;
    return mapUser(payload.user);
  } catch {
    return null;
  }
}

// Explicit local failure used when no session indicator cookie exists. The
// request is skipped because it would certainly return 401, and the caller
// still receives a real unauthenticated failure instead of null.
function localUnauthenticatedFailure(): ApiFailure {
  return {
    ok: false,
    kind: "unauthenticated",
    status: 401,
    message: "Sign in to view this content.",
    retryable: false,
  };
}

export async function listMyProjects(): Promise<ApiResult<UserProject[]>> {
  if (!hasSessionIndicator()) return localUnauthenticatedFailure();
  return apiGetMapped<unknown, UserProject[]>("/api/v1/me/projects", (wire) =>
    requireArray(wire, "projects").map((p) =>
      mapUserProject(requireRecord(p, "project")),
    ),
  );
}

export async function listMyOrganizations(): Promise<
  ApiResult<Organization[]>
> {
  if (!hasSessionIndicator()) return localUnauthenticatedFailure();
  return apiGetMapped<unknown, Organization[]>(
    "/api/v1/me/organizations",
    (wire) =>
      requireArray(wire, "organizations").map((o) =>
        mapOrganization(requireRecord(o, "organization")),
      ),
  );
}

export async function getOrganization(
  organizationId: string,
): Promise<ApiResult<Organization>> {
  return apiGetMapped<unknown, Organization>(
    `/api/v1/organizations/${organizationId}`,
    (wire) => mapOrganization(requireRecord(wire, "organization")),
  );
}

export async function listOrganizationMembers(
  organizationId: string,
): Promise<ApiResult<Membership[]>> {
  return apiGetMapped<unknown, Membership[]>(
    `/api/v1/organizations/${organizationId}/members`,
    (wire) =>
      requireArray(wire, "members").map((m) =>
        mapMembership(requireRecord(m, "membership")),
      ),
  );
}

export async function listProjectAccess(
  projectId: string,
): Promise<ApiResult<ProjectAccessEntry[]>> {
  return apiGetMapped<unknown, ProjectAccessEntry[]>(
    `/api/v1/projects/${projectId}/access`,
    (wire) =>
      requireArray(wire, "access_entries").map((a) =>
        mapAccess(requireRecord(a, "project_access")),
      ),
  );
}

export async function grantProjectAccess(
  projectId: string,
  payload: { accessLevel: string; userId?: string; organizationId?: string },
): Promise<MutationResult<ProjectAccessEntry>> {
  return authPost<ProjectAccessEntry>(
    `/api/v1/projects/${projectId}/access/grant`,
    {
      access_level: payload.accessLevel,
      user_id: payload.userId || null,
      organization_id: payload.organizationId || null,
    },
    mapAccess,
  );
}

// Production Phase 4B password reset. The reset token is delivered by email in
// production; outside production the backend also returns a dev token so the
// flow can be completed locally. The token is never logged.

export type PasswordResetRequestResult = {
  detail: string;
  devResetToken: string | null;
};

export async function requestPasswordReset(
  email: string,
): Promise<MutationResult<PasswordResetRequestResult>> {
  return authPost<PasswordResetRequestResult>(
    "/api/v1/auth/password-reset/request",
    { email },
    (raw) => ({
      detail: raw.detail as string,
      devResetToken: (raw.dev_reset_token as string) ?? null,
    }),
  );
}

export async function confirmPasswordReset(
  token: string,
  newPassword: string,
): Promise<MutationResult<{ detail: string }>> {
  return authPost<{ detail: string }>(
    "/api/v1/auth/password-reset/confirm",
    { token, new_password: newPassword },
    (raw) => ({ detail: raw.detail as string }),
  );
}
