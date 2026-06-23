import PageHeader from "@/components/PageHeader";
import DocumentTable from "@/components/DocumentTable";
import MetricCard from "@/components/MetricCard";
import { documents, type DocumentStatus } from "@/data/documents";

const statusOrder: { status: DocumentStatus; label: string }[] = [
  { status: "present", label: "Present" },
  { status: "partial", label: "Partial" },
  { status: "missing", label: "Missing" },
  { status: "referenced_not_included", label: "Referenced — not included" },
  { status: "not_yet_submitted", label: "Not yet submitted" },
];

export default function DocumentsPage() {
  const counts = (status: DocumentStatus) =>
    documents.filter((d) => d.status === status).length;

  return (
    <div>
      <PageHeader
        eyebrow="Document library"
        title="Submitted document package"
        description="The seeded Brookside Meadows submission. The system reviews a package — it is not a chat. Document statuses make completeness gaps visible at a glance."
      />

      <div className="mx-auto max-w-7xl space-y-8 px-4 py-10 sm:px-6 lg:px-8">
        <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-5">
          {statusOrder.map((s) => (
            <MetricCard
              key={s.status}
              value={counts(s.status)}
              label={s.label}
              accent={
                s.status === "present"
                  ? "land"
                  : s.status === "missing"
                    ? "red"
                    : s.status === "partial" ||
                        s.status === "referenced_not_included"
                      ? "amber"
                      : "slate"
              }
            />
          ))}
        </div>

        <DocumentTable />

        <div className="rounded-lg border border-slate-200 bg-white px-4 py-3 text-sm text-slate-600">
          <span className="font-semibold text-slate-800">Phase 1 note:</span>{" "}
          This view uses seeded synthetic document records. Later phases will add
          ingestion, chunking, embeddings, and retrieval so each document becomes
          searchable, source-linked evidence.
        </div>
      </div>
    </div>
  );
}
