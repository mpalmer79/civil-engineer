import Link from "next/link";
import PageHeader from "@/components/PageHeader";
import SafetyBoundaryBanner from "@/components/SafetyBoundaryBanner";
import ReviewPacketBuilder from "@/components/ReviewPacketBuilder";

export default function ReviewPacketDetailPage({
  params,
}: {
  params: { packetId: string };
}) {
  return (
    <div>
      <PageHeader
        eyebrow="Review packet builder"
        title="Review-support packet draft"
        description="Inspect the packet sections and items, review linked evidence, view the evidence traceability matrix, record reviewer actions, and open the printable review-support summary. The packet does not approve plans, certify compliance, verify CAD, or validate the design."
      />

      <div className="mx-auto max-w-7xl space-y-8 px-4 py-10 sm:px-6 lg:px-8">
        <Link
          href="/review-packet"
          className="inline-block text-sm font-semibold text-water-700 hover:text-water-600"
        >
          Back to review packet
        </Link>

        <ReviewPacketBuilder packetId={params.packetId} />

        <SafetyBoundaryBanner />
      </div>
    </div>
  );
}
