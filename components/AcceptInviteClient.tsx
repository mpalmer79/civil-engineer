"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";

import SectionCard from "@/components/SectionCard";
import {
  acceptInvitation,
  isSignedIn,
  lookupInvitation,
  type InvitationLookup,
} from "@/lib/api";

// Invitation acceptance. Reads the token from the link, previews the invitation
// (organization, role), and lets a signed-in user accept it. A signed-out
// visitor is prompted to sign in or register first; the token stays in the URL so
// they return here. Expired, revoked, or accepted invitations cannot be accepted.
export default function AcceptInviteClient({ token }: { token: string }) {
  const router = useRouter();
  const [signedIn, setSignedIn] = useState<boolean | null>(null);
  const [lookup, setLookup] = useState<InvitationLookup | null>(null);
  const [loaded, setLoaded] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [done, setDone] = useState<string | null>(null);

  useEffect(() => {
    setSignedIn(isSignedIn());
    if (!token) {
      setLoaded(true);
      return;
    }
    lookupInvitation(token).then((l) => {
      setLookup(l.ok ? l.data : null);
      setLoaded(true);
    });
  }, [token]);

  const handleAccept = async () => {
    setBusy(true);
    setError(null);
    const result = await acceptInvitation(token);
    setBusy(false);
    if (!result.ok || !result.data) {
      setError(result.error ?? "Could not accept the invitation.");
      return;
    }
    setDone(result.data.detail);
    router.refresh();
  };

  if (!token) {
    return (
      <SectionCard title="Invitation link is missing its token">
        <p className="text-sm text-slate-600">
          This invitation link is incomplete. Ask your teammate to resend it.
        </p>
      </SectionCard>
    );
  }

  if (!loaded) {
    return (
      <SectionCard title="Checking invitation">
        <p className="text-sm text-slate-600">Loading invitation...</p>
      </SectionCard>
    );
  }

  if (!lookup) {
    return (
      <SectionCard title="Invitation not found">
        <p className="text-sm text-slate-600">
          This invitation could not be found. It may have been revoked or the
          link may be incorrect.
        </p>
      </SectionCard>
    );
  }

  if (done) {
    return (
      <SectionCard title="Invitation accepted">
        <p className="alert alert-success">{done}</p>
        <Link href="/workspace" className="btn btn-primary mt-4">
          Go to workspace
        </Link>
      </SectionCard>
    );
  }

  return (
    <SectionCard title={`Join ${lookup.organizationName ?? "the organization"}`}>
      <dl className="grid gap-x-6 gap-y-2 sm:grid-cols-2">
        <div className="flex items-center justify-between gap-4 border-b border-slate-100 pb-2">
          <dt className="text-sm font-semibold text-slate-500">Invited email</dt>
          <dd className="text-sm text-slate-800">{lookup.email}</dd>
        </div>
        <div className="flex items-center justify-between gap-4 border-b border-slate-100 pb-2">
          <dt className="text-sm font-semibold text-slate-500">Role</dt>
          <dd className="text-sm text-slate-800">{lookup.role}</dd>
        </div>
      </dl>

      {!lookup.acceptable ? (
        <p className="alert alert-warning mt-4">
          This invitation is {lookup.status} and can no longer be accepted.
        </p>
      ) : signedIn ? (
        <div className="mt-4">
          <button
            type="button"
            onClick={handleAccept}
            disabled={busy}
            className="btn btn-primary"
          >
            {busy ? "Joining..." : "Accept invitation"}
          </button>
          {error ? <p className="alert alert-danger mt-3">{error}</p> : null}
        </div>
      ) : (
        <div className="mt-4">
          <p className="text-sm text-slate-600">
            Sign in or create an account to accept this invitation. You will
            return to this page.
          </p>
          <div className="mt-3 flex gap-3">
            <Link href="/login" className="btn btn-primary btn-sm">
              Sign in
            </Link>
            <Link href="/register" className="btn btn-secondary btn-sm">
              Create an account
            </Link>
          </div>
        </div>
      )}
    </SectionCard>
  );
}
