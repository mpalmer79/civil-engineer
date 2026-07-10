import DataSourceNotice from "@/components/DataSourceNotice";
import PageHeader from "@/components/PageHeader";
import FindingCard from "@/components/FindingCard";
import SafetyBoundaryBanner from "@/components/SafetyBoundaryBanner";
import MetricCard from "@/components/MetricCard";
import { getFindings, getEvidenceByFinding } from "@/lib/api";

export default async function FindingsPage() {
  const findingsResult = await getFindings();
  const findings = findingsResult.data;
  const evidenceByFinding = await getEvidenceByFinding(
    findings.map((f) => f.findingId),
  );
  const high = findings.filter((f) => f.riskLevel === "high").length;
  const medium = findings.filter((f) => f.riskLevel === "medium").length;

  return (
    <div>
      <PageHeader
        eyebrow="Findings"
        title="Expected review-support findings"
        description="The ten issues Civil Engineer AI is expected to surface in the Brookside Meadows package. Each is a review-support issue that needs reviewer confirmation, not a final engineering conclusion."
      />

      <div className="mx-auto max-w-7xl space-y-8 px-4 py-10 sm:px-6 lg:px-8">
        <DataSourceNotice source={findingsResult.source} />
        <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
          <MetricCard value={findings.length} label="Expected findings" accent="water" />
          <MetricCard value={high} label="High risk" accent="red" />
          <MetricCard value={medium} label="Medium risk" accent="amber" />
          <MetricCard
            value={findings.filter((f) => f.humanReviewState === "pending").length}
            label="Pending human review"
            accent="amber"
          />
        </div>

        <SafetyBoundaryBanner variant="compact" />

        <div className="grid gap-6 lg:grid-cols-2">
          {findings.map((finding) => (
            <FindingCard
              key={finding.findingId}
              finding={finding}
              evidence={evidenceByFinding[finding.findingId] ?? []}
            />
          ))}
        </div>
      </div>
    </div>
  );
}
