import type { CadParseQueueItem } from "@/lib/api";

// Surfaces parse failures with clear technical wording. A parse failure means
// the parser could not read the DXF file (for example a malformed or truncated
// file). It is a technical parse failure, never an engineering failure or a
// statement about whether the design is sound.
export default function CadParseFailurePanel({
  items,
}: {
  items: CadParseQueueItem[];
}) {
  const failures = items.filter((item) => item.queueStatus === "failed");
  if (failures.length === 0) {
    return null;
  }
  return (
    <div className="rounded-lg border border-red-200 bg-red-50 p-4">
      <p className="text-sm font-semibold text-red-800">
        Parse failures (technical)
      </p>
      <p className="mt-1 text-xs text-red-700">
        These files could not be read by the DXF parser. This is a technical
        parse failure, not an engineering determination. Re-export or repair the
        DXF file and request the parse again.
      </p>
      <ul className="mt-3 space-y-2">
        {failures.map((item) => (
          <li
            key={item.cadFileId}
            className="rounded-md border border-red-200 bg-white px-3 py-2"
          >
            <p className="text-sm font-medium text-slate-800">
              {item.fileName}
            </p>
            <p className="mt-0.5 text-xs text-red-700">
              {item.errorMessage ?? "The DXF parser could not read this file."}
            </p>
          </li>
        ))}
      </ul>
    </div>
  );
}
