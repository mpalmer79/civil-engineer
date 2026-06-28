import Link from "next/link";

import PageHeader from "@/components/PageHeader";
import WorkspaceUsageClient from "@/components/WorkspaceUsageClient";

export const metadata = {
  title: "Workspace usage",
};

export const dynamic = "force-dynamic";

export default function WorkspaceUsagePage() {
  return (
    <div>
      <PageHeader
        eyebrow="Workspace"
        title="Usage"
        description="Your organization's usage against plan limits. Limits are advisory in this phase: usage is tracked and shown, and actions are not blocked."
        actions={
          <Link href="/workspace/settings" className="btn btn-secondary">
            Back to settings
          </Link>
        }
      />
      <div className="mx-auto max-w-3xl space-y-6 px-4 py-8 sm:px-6 sm:py-10 lg:px-8">
        <WorkspaceUsageClient />
      </div>
    </div>
  );
}
