import DataSourceNotice from "@/components/DataSourceNotice";
import PageHeader from "@/components/PageHeader";
import DocumentTable from "@/components/DocumentTable";
import MetricCard from "@/components/MetricCard";
import SectionCard from "@/components/SectionCard";
import ChunkDisclosure from "@/components/ChunkDisclosure";
import { type DocumentStatus } from "@/data/documents";
import { getDocuments, getChunksByDocument } from "@/lib/api";

const statusOrder: { status: DocumentStatus; label: string }[] = [
  { status: "present", label: "Present" },
  { status: "partial", label: "Partial" },
  { status: "missing", label: "Missing" },
  { status: "referenced_not_included", label: "Referenced, not included" },
  { status: "not_yet_submitted", label: "Not yet submitted" },
];

export default async function DocumentsPage() {
  const [documentsResult, chunksByDocument] = await Promise.all([
    getDocuments(),
    getChunksByDocument(),
  ]);
  const documents = documentsResult.data;
  const counts = (status: DocumentStatus) =>
    documents.filter((d) => d.status === status).length;
  const documentsWithChunks = documents.filter(
    (d) => (chunksByDocument[d.documentId] ?? []).length > 0,
  );

  return (
    <div>
      <PageHeader
        eyebrow="Document library"
        title="Submitted document package"
        description="The seeded Brookside Meadows submission. The system reviews a package, not a chat. Document statuses make completeness gaps visible at a glance."
      />

      <div className="mx-auto max-w-7xl space-y-8 px-4 py-10 sm:px-6 lg:px-8">
        <DataSourceNotice source={documentsResult.source} />
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

        <DocumentTable documents={documents} />

        <SectionCard
          title="Seeded source chunks"
          description="Civil Engineer AI seeds short synthetic excerpts for each document so retrieval can trace findings back to specific pages and sections. Expand a document to view its chunks."
        >
          {documentsWithChunks.length === 0 ? (
            <p className="rounded-md bg-slate-50 px-3 py-2 text-sm text-slate-500">
              Source chunks are served by the backend. Start the API to view
              seeded chunks for each document.
            </p>
          ) : (
            <ul className="space-y-3">
              {documentsWithChunks.map((doc) => (
                <li
                  key={doc.documentId}
                  className="rounded-lg bg-slate-50 p-3"
                >
                  <p className="text-sm font-semibold text-slate-800">
                    {doc.fileName}
                  </p>
                  <div className="mt-2">
                    <ChunkDisclosure
                      summaryLabel="View seeded chunks"
                      chunks={chunksByDocument[doc.documentId] ?? []}
                    />
                  </div>
                </li>
              ))}
            </ul>
          )}
        </SectionCard>

        <div className="rounded-lg border border-slate-200 bg-white px-4 py-3 text-sm text-slate-600">
          <span className="font-semibold text-slate-800">Note:</span>{" "}
          Document records and source chunks are served by the backend. Retrieval
          is keyword and metadata based in this phase; embeddings and live AI
          review are planned for later phases.
        </div>
      </div>
    </div>
  );
}
