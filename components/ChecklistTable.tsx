import { checklist } from "@/data/checklist";
import StatusBadge from "@/components/StatusBadge";
import RiskBadge from "@/components/RiskBadge";

export default function ChecklistTable() {
  return (
    <div className="surface-card overflow-hidden">
      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-slate-200 text-sm">
          <thead className="bg-slate-50 text-left text-xs font-semibold uppercase tracking-wide text-slate-500">
            <tr>
              <th scope="col" className="px-4 py-3">
                Checklist item
              </th>
              <th scope="col" className="px-4 py-3">
                Category
              </th>
              <th scope="col" className="px-4 py-3">
                Requirement
              </th>
              <th scope="col" className="px-4 py-3">
                Expected evidence
              </th>
              <th scope="col" className="px-4 py-3">
                Supporting documents
              </th>
              <th scope="col" className="px-4 py-3">
                Risk
              </th>
              <th scope="col" className="px-4 py-3">
                Expected Brookside status
              </th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {checklist.map((item) => (
              <tr
                key={item.checklistItemId}
                className="align-top hover:bg-slate-50"
              >
                <td className="px-4 py-3">
                  <div className="font-mono text-xs text-slate-500">
                    {item.checklistItemId}
                  </div>
                </td>
                <td className="px-4 py-3 text-slate-600">{item.category}</td>
                <td className="px-4 py-3 text-slate-700">{item.requirement}</td>
                <td className="px-4 py-3 text-slate-600">
                  {item.expectedEvidence}
                </td>
                <td className="px-4 py-3 font-mono text-xs text-slate-500">
                  {item.supportingDocuments}
                </td>
                <td className="px-4 py-3">
                  <RiskBadge level={item.riskLevel} />
                </td>
                <td className="px-4 py-3">
                  <div className="flex flex-col items-start gap-1">
                    <StatusBadge status={item.expectedStatus} />
                    {item.plantedIssue ? (
                      <span className="font-mono text-[11px] text-amber-600">
                        {item.plantedIssue}
                      </span>
                    ) : null}
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
