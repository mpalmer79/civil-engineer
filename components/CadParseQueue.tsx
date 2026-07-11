import type { CadParseQueueItem } from "@/lib/api";

const queueStyles: Record<string, string> = {
  queued: "bg-slate-100 text-slate-600",
  parsing: "bg-water-50 text-water-700",
  completed: "bg-water-50 text-water-700",
  completed_with_warnings: "bg-amber-50 text-amber-700",
  failed: "bg-red-50 text-red-700",
  needs_human_review: "bg-amber-50 text-amber-700",
};

// Shows the manual parse queue: one row per uploaded CAD file with its derived
// queue status. A reviewer can request a parse for a queued file and open a
// parsed file for detail. A queue status of failed means a technical parse
// failure (the parser could not read the file), not an engineering failure.
export default function CadParseQueue({
  items,
  busyFileId,
  onRequestParse,
  onSelect,
}: {
  items: CadParseQueueItem[];
  busyFileId: string | null;
  onRequestParse: (cadFileId: string) => void;
  onSelect: (cadFileId: string) => void;
}) {
  return (
    <div className="surface-card p-6">
      <h3 className="text-lg font-semibold text-slate-900">Parse queue</h3>
      <p className="mt-1 text-sm text-slate-600">
        Parsing is triggered manually. A queue status of failed is a technical
        parse failure, not an engineering decision about the plan.
      </p>
      {items.length === 0 ? (
        <p className="mt-4 text-sm text-slate-600">
          No CAD files in the queue yet. Upload a DXF file to begin.
        </p>
      ) : (
        <ul className="mt-4 space-y-2">
          {items.map((item) => {
            const canParse =
              item.queueStatus === "queued" ||
              item.queueStatus === "needs_human_review" ||
              item.queueStatus === "failed";
            return (
              <li
                key={item.cadFileId}
                className="rounded-lg border border-slate-200 px-3 py-3"
              >
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <div>
                    <button
                      type="button"
                      onClick={() => onSelect(item.cadFileId)}
                      className="text-sm font-semibold text-water-700 hover:text-water-600"
                    >
                      {item.fileName}
                    </button>
                    <p className="mt-0.5 text-xs text-slate-600">
                      {item.uploadSource.replace(/_/g, " ")} ·{" "}
                      {item.findingCount} finding(s)
                      {item.warningCount > 0
                        ? ` · ${item.warningCount} warning(s)`
                        : ""}
                    </p>
                  </div>
                  <div className="flex items-center gap-2">
                    <span
                      className={`rounded-full px-2 py-0.5 text-[11px] ${
                        queueStyles[item.queueStatus] ?? queueStyles.queued
                      }`}
                    >
                      {item.queueStatus.replace(/_/g, " ")}
                    </span>
                    {canParse ? (
                      <button
                        type="button"
                        onClick={() => onRequestParse(item.cadFileId)}
                        disabled={busyFileId === item.cadFileId}
                        className="rounded-md border border-slate-300 bg-white px-2.5 py-1 text-xs font-semibold text-slate-700 transition-colors hover:bg-slate-50 disabled:opacity-60"
                      >
                        {busyFileId === item.cadFileId
                          ? "Parsing..."
                          : "Request parse"}
                      </button>
                    ) : null}
                  </div>
                </div>
                {item.errorMessage ? (
                  <p className="mt-2 rounded-md bg-red-50 px-2 py-1 text-xs text-red-700">
                    {item.errorMessage}
                  </p>
                ) : null}
              </li>
            );
          })}
        </ul>
      )}
    </div>
  );
}
