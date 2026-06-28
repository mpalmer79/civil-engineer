import Link from "next/link";

import PageHeader from "@/components/PageHeader";
import PilotReleaseNote from "@/components/PilotReleaseNote";
import WorkspaceBillingClient from "@/components/WorkspaceBillingClient";

export const metadata = {
  title: "Workspace billing",
};

export const dynamic = "force-dynamic";

export default function WorkspaceBillingPage() {
  return (
    <div>
      <PageHeader
        eyebrow="Workspace"
        title="Billing"
        description="Your organization's plan and billing status. Billing is not active in this phase: the plan foundation is in place, but no payment is collected and no subscription is charged."
        actions={
          <Link href="/workspace/settings" className="btn btn-secondary">
            Back to settings
          </Link>
        }
      />
      <div className="mx-auto max-w-3xl space-y-6 px-4 py-8 sm:px-6 sm:py-10 lg:px-8">
        <PilotReleaseNote variant="compact" />
        <WorkspaceBillingClient />
      </div>
    </div>
  );
}
