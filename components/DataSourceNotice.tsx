import type { DemoDataSource } from "@/lib/api/client";

// Discloses where a public demo surface's records came from. Brookside
// Meadows data is synthetic in both cases; the distinction is whether this
// render used the connected backend's seeded records or the repository's
// fixture snapshot because the backend was unreachable.
export default function DataSourceNotice({
  source,
}: {
  source: DemoDataSource;
}) {
  const backend = source === "backend_seeded";
  return (
    <p
      data-testid="data-source-notice"
      data-source={source}
      className={`inline-flex items-center gap-2 rounded-lg border px-3 py-1.5 text-xs ${
        backend
          ? "border-slate-200 bg-slate-50 text-slate-600"
          : "border-amber-200 bg-amber-50 text-amber-800"
      }`}
    >
      <span
        aria-hidden="true"
        className={`h-1.5 w-1.5 rounded-full ${backend ? "bg-slate-400" : "bg-amber-500"}`}
      />
      {backend
        ? "Seeded Brookside Meadows demo data, served by the connected backend."
        : "Seeded Brookside Meadows fixture snapshot. The demo backend is not connected right now."}
    </p>
  );
}
