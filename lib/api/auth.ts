import {
  API_BASE_URL,
  authHeaders,
  clearAuthToken,
  getAuthToken,
  safeFetch,
  setAuthToken,
} from "./client";

// Production Foundations Sprint 5 local authentication and access control client.
// Tokens are stored client-side and attached as a Bearer Authorization header.
// The token is never placed in a URL and never logged. Access control protects
// review records; it does not approve plans, certify compliance, or make any
// final engineering decision.
//
// NEXT_PUBLIC_API_BASE_URL is the backend origin only (no /api/v1 path); this
// client appends the /api/v1 paths itself.

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

type AuthTokenResult = { token: string; user: CurrentUser };

function mapTokenResponse(raw: Record<string, unknown>): AuthTokenResult {
  const token = raw.access_token as string;
  setAuthToken(token);
  return { token, user: mapUser(raw.user as Record<string, unknown>) };
}

export async function registerUser(
  input: RegisterInput,
): Promise<MutationResult<AuthTokenResult>> {
  return authPost<AuthTokenResult>(
    "/api/v1/auth/register",
    {
      email: input.email,
      display_name: input.displayName,
      password: input.password,
      organization_name: input.organizationName || null,
      organization_type: input.organizationType || null,
    },
    mapTokenResponse,
  );
}

export async function loginUser(
  email: string,
  password: string,
): Promise<MutationResult<AuthTokenResult>> {
  return authPost<AuthTokenResult>(
    "/api/v1/auth/login",
    { email, password },
    mapTokenResponse,
  );
}

export function logoutUser(): void {
  clearAuthToken();
}

export function isSignedIn(): boolean {
  return getAuthToken() !== null;
}

export async function getCurrentUser(): Promise<CurrentUser | null> {
  if (!getAuthToken()) return null;
  const data = await safeFetch<Record<string, unknown>>("/api/v1/auth/me");
  return data ? mapUser(data) : null;
}

export async function listMyProjects(): Promise<UserProject[] | null> {
  if (!getAuthToken()) return null;
  const data = await safeFetch<Record<string, unknown>[]>("/api/v1/me/projects");
  if (!data) return null;
  return data.map(mapUserProject);
}

export async function listMyOrganizations(): Promise<Organization[] | null> {
  if (!getAuthToken()) return null;
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
