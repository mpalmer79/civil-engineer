import Link from "next/link";
import PageHeader from "@/components/PageHeader";
import SafetyBoundaryBanner from "@/components/SafetyBoundaryBanner";
import ResponsePackageBuilder from "@/components/ResponsePackageBuilder";

export default function ResponsePackageDetailPage({
  params,
}: {
  params: { responsePackageId: string };
}) {
  return (
    <div>
      <PageHeader
        eyebrow="External review response package"
        title="Draft response package"
        description="Inspect the response sections and items, edit draft wording, review linked evidence, manage item and package statuses, view the attachment checklist and history, and open the printable draft. The package does not send email, approve plans, certify compliance, verify CAD, or validate the design."
      />

      <div className="mx-auto max-w-7xl space-y-8 px-4 py-10 sm:px-6 lg:px-8">
        <Link
          href="/response-package"
          className="inline-block text-sm font-semibold text-water-700 hover:text-water-600"
        >
          Back to response package
        </Link>

        <ResponsePackageBuilder responsePackageId={params.responsePackageId} />

        <SafetyBoundaryBanner />
      </div>
    </div>
  );
}
