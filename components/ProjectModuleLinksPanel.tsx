import Link from "next/link";
import type { ProjectModuleLinks } from "@/lib/api";

const severityStyles: Record<string, string> = {
  info: "text-slate-500",
  low: "text-slate-500",
  medium: "text-amber-700",
  high: "text-red-700",
  needs_human_review: "text-amber-700",
};

// Deep links into the existing modules. The dashboard links into modules rather
// than replacing them.
export default function ProjectModuleLinksPanel({
  moduleLinks,
}: {
  moduleLinks: ProjectModuleLinks | null;
}) {
  if (!moduleLinks || moduleLinks.links.length === 0) {
    return (
      <div className="surface-card p-6 text-sm text-slate-500">
        Module links are unavailable.
      </div>
    );
  }
  return (
    <div className="surface-card p-6">
      <h3 className="text-lg font-semibold text-slate-900">Modules</h3>
      <p className="mt-1 text-sm text-slate-600">{moduleLinks.note}</p>
      <div className="mt-4 grid gap-3 sm:grid-cols-2">
        {moduleLinks.links.map((link) => (
          <Link
            key={link.module}
            href={link.route}
            className="rounded-lg border border-slate-200 bg-white px-3 py-2 transition-colors hover:border-water-400"
          >
            <div className="flex items-center justify-between gap-2">
              <span className="text-sm font-semibold text-slate-800">
                {link.label}
              </span>
              {link.count > 0 ? (
                <span
                  className={`text-xs font-semibold ${
                    severityStyles[link.severity] ?? severityStyles.info
                  }`}
                >
                  {link.count}
                </span>
              ) : null}
            </div>
            <p className="mt-0.5 text-xs text-slate-500">{link.description}</p>
          </Link>
        ))}
      </div>
    </div>
  );
}
