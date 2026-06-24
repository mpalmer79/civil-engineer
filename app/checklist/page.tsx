import PageHeader from "@/components/PageHeader";
import ChecklistTable from "@/components/ChecklistTable";
import SectionCard from "@/components/SectionCard";
import MetricCard from "@/components/MetricCard";
import { type ChecklistStatus } from "@/data/checklist";
import { getChecklist, getChunksByChecklistItem } from "@/lib/api";

const statusSummary: { status: ChecklistStatus; label: string }[] = [
  { status: "supported", label: "Supported" },
  { status: "missing", label: "Missing" },
  { status: "conflicting", label: "Conflicting" },
  { status: "unclear", label: "Unclear" },
  { status: "unresolved", label: "Unresolved" },
];

export default async function ChecklistPage() {
  const [checklist, evidenceByItem] = await Promise.all([
    getChecklist(),
    getChunksByChecklistItem(),
  ]);
  const counts = (status: ChecklistStatus) =>
    checklist.filter((c) => c.expectedStatus === status).length;

  return (
    <div>
      <PageHeader
        eyebrow="Stormwater checklist"
        title="Structured review logic"
        description="Nineteen reusable stormwater checklist items applied to Brookside Meadows. The checklist, not a free-form prompt, drives what gets examined."
      />

      <div className="mx-auto max-w-7xl space-y-8 px-4 py-10 sm:px-6 lg:px-8">
        <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-5">
          {statusSummary.map((s) => (
            <MetricCard
              key={s.status}
              value={counts(s.status)}
              label={s.label}
              accent={
                s.status === "supported"
                  ? "land"
                  : s.status === "missing"
                    ? "red"
                    : "amber"
              }
            />
          ))}
        </div>

        <SectionCard title="How the checklist is used">
          <ul className="grid gap-3 text-sm text-slate-600 sm:grid-cols-2">
            <li className="rounded-lg bg-slate-50 px-3 py-2">
              The checklist drives review structure and applicability: items
              apply based on project flags such as a proposed infiltration
              practice or a downstream structure.
            </li>
            <li className="rounded-lg bg-slate-50 px-3 py-2">
              Each AI finding is tied to a specific checklist item, so every
              issue traces back to a defined requirement.
            </li>
            <li className="rounded-lg bg-slate-50 px-3 py-2">
              The system does not rely on free-form AI judgment alone; structure
              and expected evidence constrain it.
            </li>
            <li className="rounded-lg bg-slate-50 px-3 py-2">
              Human review is required before any final action. Statuses never
              include &quot;approved&quot; or &quot;compliant.&quot;
            </li>
          </ul>
        </SectionCard>

        <ChecklistTable items={checklist} evidenceByItem={evidenceByItem} />
      </div>
    </div>
  );
}
