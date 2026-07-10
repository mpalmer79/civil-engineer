import Link from "next/link";
import PageHeader from "@/components/PageHeader";
import SafetyBoundaryBanner from "@/components/SafetyBoundaryBanner";
import CadIntakePage from "@/components/CadIntakePage";

export default async function CadIntakeDetailRoute(
  props: {
    params: Promise<{ cadFileId: string }>;
  }
) {
  const params = await props.params;
  return (
    <div>
      <PageHeader
        eyebrow="Real CAD file intake"
        title="DXF file review"
        description="Inspect the parsed DXF metadata for a single CAD file: layers, text, blocks, reference candidates, plan sheet comparison, and CAD review findings. It does not verify CAD, validate design, certify compliance, or approve plans."
      />

      <div className="mx-auto max-w-7xl space-y-8 px-4 py-10 sm:px-6 lg:px-8">
        <Link
          href="/cad-intake"
          className="inline-block text-sm font-semibold text-water-700 hover:text-water-600"
        >
          Back to CAD intake
        </Link>

        <CadIntakePage initialCadFileId={params.cadFileId} />

        <SafetyBoundaryBanner />
      </div>
    </div>
  );
}
