"use client";

import { useEffect, useState } from "react";
import Link from "next/link";

import PageHeader from "@/components/PageHeader";
import SectionCard from "@/components/SectionCard";
import StatusChip from "@/components/StatusChip";
import EmptyState from "@/components/EmptyState";
import PermissionDeniedCard from "@/components/PermissionDeniedCard";
import {
  grantProjectAccess,
  isSignedIn,
  listProjectAccess,
  type ProjectAccessEntry,
} from "@/lib/api";

const ACCESS_LEVELS = [
  "project_admin",
  "senior_reviewer",
  "reviewer",
  "read_only",
  "applicant_placeholder",
];

export default function ProjectAccessPage({
  params,
}: {
  params: { projectId: string };
}) {
  const [entries, setEntries] = useState<ProjectAccessEntry[] | null>(null);
  const [loaded, setLoaded] = useState(false);
  const [signedIn, setSignedIn] = useState(false);
  const [userId, setUserId] = useState("");
  const [accessLevel, setAccessLevel] = useState("reviewer");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);

  const load = () => {
    listProjectAccess(params.projectId).then((e) => {
      setEntries(e);
      setLoaded(true);
    });
  };

  useEffect(() => {
    setSignedIn(isSignedIn());
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [params.projectId]);

  const handleGrant = async () => {
    if (!userId.trim()) {
      setError("Enter the user id to grant access to.");
      return;
    }
    setBusy(true);
    setError(null);
    setMessage(null);
    const result = await grantProjectAccess(params.projectId, {
      accessLevel,
      userId: userId.trim(),
    });
    setBusy(false);
    if (!result.ok) {
      setError(result.error ?? "Could not grant access.");
      return;
    }
    setMessage("Access granted.");
    setUserId("");
    load();
  };

  return (
    <div>
      <PageHeader
        eyebrow="Access control"
        title="Project access"
        description="Who can view or take reviewer actions on this project. Access controls review records; it does not approve plans, certify compliance, or determine engineering outcomes."
      />
      <div className="mx-auto max-w-4xl space-y-6 px-4 py-10 sm:px-6 lg:px-8">
        <Link href={`/projects/${params.projectId}`} className="nav-link">
          Back to project
        </Link>

        {loaded && !signedIn ? (
          <PermissionDeniedCard message="Sign in to view and manage project access. Ask a project admin or organization admin for access." />
        ) : null}

        {entries !== null ? (
          <SectionCard title="Current access">
            {entries.length === 0 ? (
              <EmptyState title="No access entries yet, or you do not have access to view them" />
            ) : (
              <ul className="list-container">
                {entries.map((e) => (
                  <li
                    key={e.projectAccessId}
                    className="flex flex-wrap items-center justify-between gap-2 px-4 py-3 text-sm"
                  >
                    <span className="text-slate-800">
                      {e.userId
                        ? `User ${e.userId}`
                        : `Organization ${e.organizationId}`}
                    </span>
                    <StatusChip
                      label={`${e.accessLevel}${e.isActive ? "" : " (inactive)"}`}
                      prefix="access"
                      tone={e.isActive ? "neutral" : "warning"}
                    />
                  </li>
                ))}
              </ul>
            )}
          </SectionCard>
        ) : null}

        {signedIn ? (
          <SectionCard
            title="Grant access"
            description="Project admins can grant access to a user. If you are not a project admin, the grant will be declined."
          >
            <div className="grid gap-4 sm:grid-cols-2">
              <div className="form-field">
                <label htmlFor="access-user-id" className="form-label">
                  User id
                </label>
                <input
                  id="access-user-id"
                  type="text"
                  value={userId}
                  onChange={(e) => setUserId(e.target.value)}
                  placeholder="user_..."
                  className="form-input"
                />
              </div>
              <div className="form-field">
                <label htmlFor="access-level" className="form-label">
                  Access level
                </label>
                <select
                  id="access-level"
                  value={accessLevel}
                  onChange={(e) => setAccessLevel(e.target.value)}
                  className="form-input"
                >
                  {ACCESS_LEVELS.map((l) => (
                    <option key={l} value={l}>
                      {l}
                    </option>
                  ))}
                </select>
              </div>
            </div>
            {error ? <p className="alert alert-danger mt-3">{error}</p> : null}
            {message ? (
              <p className="alert alert-success mt-3">{message}</p>
            ) : null}
            <button
              type="button"
              onClick={handleGrant}
              disabled={busy}
              className="btn btn-primary mt-4"
            >
              {busy ? "Granting..." : "Grant access"}
            </button>
          </SectionCard>
        ) : null}
      </div>
    </div>
  );
}
