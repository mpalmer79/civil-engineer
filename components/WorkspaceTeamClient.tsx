"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";

import SectionCard from "@/components/SectionCard";
import EmptyState from "@/components/EmptyState";
import StatusChip from "@/components/StatusChip";
import {
  createInvitation,
  isSignedIn,
  listInvitations,
  listMyOrganizations,
  listOrganizationMembers,
  revokeInvitation,
  type Invitation,
  type Membership,
  type Organization,
} from "@/lib/api";

const INVITE_ROLES = [
  { value: "reviewer", label: "Reviewer" },
  { value: "senior_reviewer", label: "Senior reviewer" },
  { value: "read_only", label: "Read only" },
  { value: "org_admin", label: "Organization admin" },
];

// Workspace team management. An organization admin can invite teammates, see
// pending invitations, and revoke them. Non-admins see the member list only.
// Invitation tokens are delivered by email in production; outside production the
// dev token is surfaced as an accept link for local testing.
export default function WorkspaceTeamClient() {
  const [signedIn, setSignedIn] = useState<boolean | null>(null);
  const [orgs, setOrgs] = useState<Organization[] | null>(null);
  const [members, setMembers] = useState<Membership[] | null>(null);
  const [invites, setInvites] = useState<Invitation[] | null>(null);
  const [email, setEmail] = useState("");
  const [role, setRole] = useState("reviewer");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [devLink, setDevLink] = useState<string | null>(null);

  const primaryOrg = (orgs ?? []).find((o) => o.role === "org_admin") ?? (orgs ?? [])[0];
  const isAdmin = primaryOrg?.role === "org_admin";
  const orgId = primaryOrg?.organizationId ?? null;

  const refresh = useCallback(async (organizationId: string, admin: boolean) => {
    const [mResult, invResult] = await Promise.all([
      listOrganizationMembers(organizationId),
      admin ? listInvitations(organizationId) : Promise.resolve(null),
    ]);
    setMembers(mResult.ok ? mResult.data : null);
    setInvites(invResult && invResult.ok ? invResult.data : null);
  }, []);

  useEffect(() => {
    const authed = isSignedIn();
    setSignedIn(authed);
    if (!authed) return;
    listMyOrganizations().then((o) => setOrgs(o.ok ? o.data : null));
  }, []);

  useEffect(() => {
    if (orgId) void refresh(orgId, isAdmin);
  }, [orgId, isAdmin, refresh]);

  const handleInvite = async () => {
    if (!orgId) return;
    if (!email.trim()) {
      setError("Enter a teammate's email.");
      return;
    }
    setBusy(true);
    setError(null);
    setDevLink(null);
    const result = await createInvitation(orgId, { email: email.trim(), role });
    setBusy(false);
    if (!result.ok || !result.data) {
      setError(result.error ?? "Could not create the invitation.");
      return;
    }
    setEmail("");
    if (result.data.devInviteToken) {
      setDevLink(
        `/invitations/accept?token=${encodeURIComponent(result.data.devInviteToken)}`,
      );
    }
    await refresh(orgId, isAdmin);
  };

  const handleRevoke = async (invitationId: string) => {
    if (!orgId) return;
    await revokeInvitation(orgId, invitationId);
    await refresh(orgId, isAdmin);
  };

  if (signedIn === false) {
    return (
      <SectionCard title="Sign in to manage your team">
        <p className="text-sm text-slate-600">
          Sign in to view and manage your organization team.
        </p>
        <div className="mt-4 flex gap-3">
          <Link href="/login" className="btn btn-primary btn-sm">
            Sign in
          </Link>
        </div>
      </SectionCard>
    );
  }

  if (orgs !== null && !primaryOrg) {
    return (
      <SectionCard title="No organization yet">
        <p className="text-sm text-slate-600">
          You are not a member of an organization. Create one when you register a
          workspace, or accept an invitation from a teammate.
        </p>
      </SectionCard>
    );
  }

  return (
    <div className="space-y-6">
      <SectionCard title={`Team: ${primaryOrg?.organizationName ?? ""}`}>
        {members && members.length > 0 ? (
          <ul className="list-container">
            {members.map((m) => (
              <li
                key={m.membershipId}
                className="flex flex-wrap items-center justify-between gap-2 px-4 py-3 text-sm"
              >
                <span className="text-slate-800">
                  {m.displayName ?? m.userEmail ?? m.userId}
                </span>
                <StatusChip label={m.role} prefix="role" />
              </li>
            ))}
          </ul>
        ) : (
          <p className="text-sm text-slate-600">No members to show.</p>
        )}
      </SectionCard>

      {isAdmin ? (
        <>
          <SectionCard title="Invite a teammate">
            <div className="grid gap-3 sm:grid-cols-[1fr,auto,auto] sm:items-end">
              <div>
                <label className="form-label">Work email</label>
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="teammate@example.com"
                  className="form-input w-full"
                />
              </div>
              <div>
                <label className="form-label">Role</label>
                <select
                  value={role}
                  onChange={(e) => setRole(e.target.value)}
                  className="form-input"
                >
                  {INVITE_ROLES.map((r) => (
                    <option key={r.value} value={r.value}>
                      {r.label}
                    </option>
                  ))}
                </select>
              </div>
              <button
                type="button"
                onClick={handleInvite}
                disabled={busy}
                className="btn btn-primary"
              >
                {busy ? "Inviting..." : "Send invite"}
              </button>
            </div>
            {error ? <p className="alert alert-danger mt-3">{error}</p> : null}
            {devLink ? (
              <div className="alert alert-warning mt-3 text-sm">
                <p className="font-semibold">Development only</p>
                <p>
                  No email provider is configured, so the invite link is shown
                  here for local testing.
                </p>
                <Link
                  href={devLink}
                  className="mt-2 inline-block font-semibold text-water-700 hover:underline"
                >
                  Open the accept link →
                </Link>
              </div>
            ) : null}
          </SectionCard>

          <SectionCard title="Pending and past invitations">
            {invites && invites.length > 0 ? (
              <ul className="list-container">
                {invites.map((inv) => (
                  <li
                    key={inv.invitationId}
                    className="flex flex-wrap items-center justify-between gap-2 px-4 py-3 text-sm"
                  >
                    <span className="text-slate-800">
                      {inv.email}{" "}
                      <span className="text-slate-400">({inv.role})</span>
                    </span>
                    <span className="flex items-center gap-3">
                      <StatusChip label={inv.status} prefix="invite" />
                      {inv.status === "pending" ? (
                        <button
                          type="button"
                          onClick={() => handleRevoke(inv.invitationId)}
                          className="btn btn-secondary btn-sm"
                        >
                          Revoke
                        </button>
                      ) : null}
                    </span>
                  </li>
                ))}
              </ul>
            ) : (
              <EmptyState
                title="No invitations yet"
                description="Invite a teammate by email to add them to your organization."
              />
            )}
          </SectionCard>
        </>
      ) : (
        <SectionCard title="Team management">
          <p className="text-sm text-slate-600">
            Inviting and removing teammates requires an organization admin. Ask an
            admin in {primaryOrg?.organizationName} to manage invitations.
          </p>
        </SectionCard>
      )}
    </div>
  );
}
