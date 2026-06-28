// Production Phase 4B organization team invitations client.
//
// An org admin can invite, list, and revoke invitations; a signed-in user can
// accept one with a token. Invitation tokens are delivered by email in
// production; outside production the backend also returns a dev token so the
// flow can be completed locally. The token is never logged.

import { API_BASE_URL, authHeaders, safeFetch } from "./client";

export type Invitation = {
  invitationId: string;
  organizationId: string;
  email: string;
  role: string;
  status: string;
  invitedByUserId: string | null;
  acceptedByUserId: string | null;
  expiresAt: string | null;
  acceptedAt: string | null;
  revokedAt: string | null;
  createdAt: string | null;
};

export type InvitationLookup = {
  organizationId: string;
  organizationName: string | null;
  email: string;
  role: string;
  status: string;
  acceptable: boolean;
  expiresAt: string | null;
};

export type MutationResult<T> = {
  ok: boolean;
  backendReachable: boolean;
  data?: T;
  error?: string;
};

function mapInvitation(raw: Record<string, unknown>): Invitation {
  return {
    invitationId: raw.invitation_id as string,
    organizationId: raw.organization_id as string,
    email: raw.email as string,
    role: raw.role as string,
    status: raw.status as string,
    invitedByUserId: (raw.invited_by_user_id as string) ?? null,
    acceptedByUserId: (raw.accepted_by_user_id as string) ?? null,
    expiresAt: (raw.expires_at as string) ?? null,
    acceptedAt: (raw.accepted_at as string) ?? null,
    revokedAt: (raw.revoked_at as string) ?? null,
    createdAt: (raw.created_at as string) ?? null,
  };
}

async function mutate<T>(
  path: string,
  body: unknown,
  mapper: (raw: Record<string, unknown>) => T,
): Promise<MutationResult<T>> {
  try {
    const res = await fetch(`${API_BASE_URL}${path}`, {
      method: "POST",
      headers: authHeaders({ "Content-Type": "application/json" }),
      body: body === undefined ? undefined : JSON.stringify(body),
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
      error: "Backend unavailable. Start the API and try again.",
    };
  }
}

export async function listInvitations(
  organizationId: string,
): Promise<Invitation[] | null> {
  const data = await safeFetch<Record<string, unknown>[]>(
    `/api/v1/organizations/${organizationId}/invitations`,
  );
  return data ? data.map(mapInvitation) : null;
}

export type CreateInvitationResult = {
  invitation: Invitation;
  devInviteToken: string | null;
  emailSent: boolean;
};

export async function createInvitation(
  organizationId: string,
  payload: { email: string; role: string },
): Promise<MutationResult<CreateInvitationResult>> {
  return mutate<CreateInvitationResult>(
    `/api/v1/organizations/${organizationId}/invitations`,
    { email: payload.email, role: payload.role },
    (raw) => ({
      invitation: mapInvitation(raw.invitation as Record<string, unknown>),
      devInviteToken: (raw.dev_invite_token as string) ?? null,
      emailSent: (raw.email_sent as boolean) ?? false,
    }),
  );
}

export async function revokeInvitation(
  organizationId: string,
  invitationId: string,
): Promise<MutationResult<Invitation>> {
  return mutate<Invitation>(
    `/api/v1/organizations/${organizationId}/invitations/${invitationId}/revoke`,
    undefined,
    mapInvitation,
  );
}

export async function lookupInvitation(
  token: string,
): Promise<InvitationLookup | null> {
  const data = await safeFetch<Record<string, unknown>>(
    `/api/v1/invitations/lookup?token=${encodeURIComponent(token)}`,
  );
  if (!data) return null;
  return {
    organizationId: data.organization_id as string,
    organizationName: (data.organization_name as string) ?? null,
    email: data.email as string,
    role: data.role as string,
    status: data.status as string,
    acceptable: (data.acceptable as boolean) ?? false,
    expiresAt: (data.expires_at as string) ?? null,
  };
}

export async function acceptInvitation(
  token: string,
): Promise<MutationResult<{ organizationId: string; role: string; detail: string }>> {
  return mutate(
    "/api/v1/invitations/accept",
    { token },
    (raw) => ({
      organizationId: raw.organization_id as string,
      role: raw.role as string,
      detail: raw.detail as string,
    }),
  );
}
