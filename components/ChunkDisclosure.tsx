import type { ChunkItem } from "@/lib/api";

// A native disclosure that lists seeded source chunks. Works without client
// side JavaScript. Used on the documents and checklist pages.
export default function ChunkDisclosure({
  summaryLabel,
  chunks,
  emptyNote = "No seeded source chunks for this item yet.",
}: {
  summaryLabel: string;
  chunks: ChunkItem[];
  emptyNote?: string;
}) {
  if (chunks.length === 0) {
    return (
      <span className="text-xs text-slate-400">Evidence not found</span>
    );
  }

  return (
    <details className="group">
      <summary className="cursor-pointer text-sm font-medium text-water-700 hover:text-water-600">
        {summaryLabel} ({chunks.length})
      </summary>
      <ul className="mt-2 space-y-2">
        {chunks.map((chunk) => (
          <li
            key={chunk.chunkId}
            className="rounded-lg border border-slate-200 bg-white p-3"
          >
            <div className="flex flex-wrap items-center gap-x-3 gap-y-1 text-xs text-slate-400">
              <span className="font-mono">{chunk.chunkId}</span>
              <span className="font-mono">{chunk.fileName}</span>
              {chunk.pageNumber != null ? (
                <span>page {chunk.pageNumber}</span>
              ) : null}
              {chunk.sectionHeading ? (
                <span>section: {chunk.sectionHeading}</span>
              ) : null}
            </div>
            <p className="mt-1 text-sm text-slate-700">{chunk.content}</p>
            {chunk.keywords.length > 0 ? (
              <p className="mt-1 text-xs text-slate-400">
                keywords: {chunk.keywords.join(", ")}
              </p>
            ) : null}
          </li>
        ))}
      </ul>
    </details>
  );
}
