import Link from "next/link";

import PageHeader from "@/components/PageHeader";
import WorkspaceTeamClient from "@/components/WorkspaceTeamClient";

export const metadata = {
  title: "Workspace team",
};

export const dynamic = "force-dynamic";

export default function WorkspaceTeamPage() {
  return (
    <div>
      <PageHeader
        eyebrow="Workspace"
        title="Team"
        description="Manage your organization's teammates. Organization admins can invite teammates by email and revoke pending invitations. Roles control who can review records; they do not determine engineering outcomes."
        actions={
          <Link href="/workspace/settings" className="btn btn-secondary">
            Back to settings
          </Link>
        }
      />
      <div className="mx-auto max-w-3xl space-y-6 px-4 py-8 sm:px-6 sm:py-10 lg:px-8">
        <WorkspaceTeamClient />
      </div>
    </div>
  );
}
