import {
  evaluationCases as staticCases,
  evaluationSummary as staticSummary,
  type EvaluationCase,
} from "@/data/evaluationCases";
import MetricCard from "@/components/MetricCard";

export default function EvaluationSummary({
  evaluationCases = staticCases,
  evaluationSummary = staticSummary,
}: {
  evaluationCases?: EvaluationCase[];
  evaluationSummary?: typeof staticSummary;
}) {
  return (
    <div className="space-y-8">
      <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
        <MetricCard
          value={`${evaluationSummary.casesPassed} / ${evaluationSummary.totalCases}`}
          label="Evaluation cases passed"
          accent="land"
        />
        <MetricCard
          value={evaluationSummary.expectedFindingsDetected}
          label="Expected findings detected"
          hint="Across cases that expect a finding"
          accent="water"
        />
        <MetricCard
          value={`${Math.round(
            evaluationSummary.averageSourceCitationAccuracy * 100,
          )}%`}
          label="Avg. source citation accuracy"
          accent="water"
        />
        <MetricCard
          value={evaluationSummary.prohibitedWordingCount}
          label="Prohibited wording count"
          hint="approved / certified / compliant / safe"
          accent={
            evaluationSummary.prohibitedWordingCount === 0 ? "land" : "red"
          }
        />
      </div>

      <div className="surface-card overflow-hidden">
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-slate-200 text-sm">
            <thead className="bg-slate-50 text-left text-xs font-semibold uppercase tracking-wide text-slate-500">
              <tr>
                <th scope="col" className="px-4 py-3">
                  Evaluation case
                </th>
                <th scope="col" className="px-4 py-3">
                  Primary metric
                </th>
                <th scope="col" className="px-4 py-3">
                  Findings detected
                </th>
                <th scope="col" className="px-4 py-3">
                  Citation accuracy
                </th>
                <th scope="col" className="px-4 py-3">
                  FP
                </th>
                <th scope="col" className="px-4 py-3">
                  FN
                </th>
                <th scope="col" className="px-4 py-3">
                  Unsupported
                </th>
                <th scope="col" className="px-4 py-3">
                  Prohibited
                </th>
                <th scope="col" className="px-4 py-3">
                  Human review
                </th>
                <th scope="col" className="px-4 py-3">
                  Result
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {evaluationCases.map((c) => (
                <tr key={c.evalCaseId} className="hover:bg-slate-50">
                  <td className="px-4 py-3">
                    <div className="font-medium text-slate-900">{c.name}</div>
                    <div className="font-mono text-xs text-slate-400">
                      {c.evalCaseId}
                    </div>
                  </td>
                  <td className="px-4 py-3 text-slate-600">{c.primaryMetric}</td>
                  <td className="px-4 py-3 text-slate-600">
                    {c.expectedFindingsDetected}
                  </td>
                  <td className="px-4 py-3 text-slate-600">
                    {Math.round(c.sourceCitationAccuracy * 100)}%
                  </td>
                  <td className="px-4 py-3 text-slate-600">{c.falsePositives}</td>
                  <td className="px-4 py-3 text-slate-600">{c.falseNegatives}</td>
                  <td className="px-4 py-3 text-slate-600">
                    {c.unsupportedClaims}
                  </td>
                  <td className="px-4 py-3 text-slate-600">
                    {c.prohibitedWordingCount}
                  </td>
                  <td className="px-4 py-3 text-slate-600">
                    {c.humanReviewRequired}
                  </td>
                  <td className="px-4 py-3">
                    <span
                      className={`badge ${
                        c.passed
                          ? "bg-land-50 text-land-700 ring-land-600/20"
                          : "bg-red-50 text-red-700 ring-red-600/20"
                      }`}
                    >
                      {c.passed ? "passed" : "failed"}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
