import {
  API_BASE_URL,
  authHeaders,
  hasSessionIndicator,
  safeFetch,
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

function mapOrganization(o: Record<string, unknown>): Organization {
  return {
    organizationId: o.organization_id as string,
    organizationName: o.organization_name as string,
    organizationType: o.organization_type as string,
    sourceMode: o.source_mode as string,
    role: (o.role as string) ?? null,
    membershipId: (o.membership_id as string) ?? null,
  };
}

function mapMembership(m: Record<string, unknown>): Membership {
  return {
    membershipId: m.membership_id as string,
    organizationId: m.organization_id as string,
    userId: m.user_id as string,
    userEmail: (m.user_email as string) ?? null,
    displayName: (m.display_name as string) ?? null,
    role: m.role as string,
    isActive: (m.is_active as boolean) ?? true,
  };
}

function mapUserProject(p: Record<string, unknown>): UserProject {
  return {
    projectId: p.project_id as string,
    projectName: p.project_name as string,
    sourceMode: p.source_mode as string,
    visibilityMode: p.visibility_mode as string,
    demoPublic: (p.demo_public as boolean) ?? false,
    organizationId: (p.organization_id as string) ?? null,
    accessLevel: (p.access_level as string) ?? null,
  };
}

function mapAccess(a: Record<string, unknown>): ProjectAccessEntry {
  return {
    projectAccessId: a.project_access_id as string,
    projectId: a.project_id as string,
    organizationId: (a.organization_id as string) ?? null,
    userId: (a.user_id as string) ?? null,
    accessLevel: a.access_level as string,
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

export async function listMyProjects(): Promise<UserProject[] | null> {
  if (!hasSessionIndicator()) return null;
  const data = await safeFetch<Record<string, unknown>[]>("/api/v1/me/projects");
  if (!data) return null;
  return data.map(mapUserProject);
}

export async function listMyOrganizations(): Promise<Organization[] | null> {
  if (!hasSessionIndicator()) return null;
  const data = await safeFetch<Record<string, unknown>[]>(
    "/api/v1/me/organizations",
  );
  if (!data) return null;
  return data.map(mapOrganization);
}

export async function getOrganization(
  organizationId: string,
): Promise<Organization | null> {
  const data = await safeFetch<Record<string, unknown>>(
    `/api/v1/organizations/${organizationId}`,
  );
  return data ? mapOrganization(data) : null;
}

export async function listOrganizationMembers(
  organizationId: string,
): Promise<Membership[] | null> {
  const data = await safeFetch<Record<string, unknown>[]>(
    `/api/v1/organizations/${organizationId}/members`,
  );
  if (!data) return null;
  return data.map(mapMembership);
}

export async function listProjectAccess(
  projectId: string,
): Promise<ProjectAccessEntry[] | null> {
  const data = await safeFetch<Record<string, unknown>[]>(
    `/api/v1/projects/${projectId}/access`,
  );
  if (!data) return null;
  return data.map(mapAccess);
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
