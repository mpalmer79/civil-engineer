import { brookside as defaultProject, type BooksideProject } from "@/data/brookside";

export default function ProjectSummaryCard({
  project: brookside = defaultProject,
}: {
  project?: BooksideProject;
}) {
  return (
    <div className="surface-card p-6">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h2 className="text-xl font-semibold text-slate-900">
            {brookside.projectName}
          </h2>
          <p className="mt-1 text-sm text-slate-500">
            {brookside.jurisdiction} · {brookside.locationContext}
          </p>
        </div>
        <span className="badge bg-water-50 text-water-700 ring-water-600/20">
          status: {brookside.status}
        </span>
      </div>

      <p className="mt-4 text-sm leading-relaxed text-slate-600">
        {brookside.summary}
      </p>

      <dl className="mt-6 grid grid-cols-2 gap-4 sm:grid-cols-3">
        {[
          { label: "Total acreage", value: `${brookside.acreage} ac` },
          { label: "Disturbed area", value: `${brookside.disturbedAcres} ac` },
          { label: "Proposed lots", value: brookside.proposedLots },
          { label: "Project type", value: brookside.projectType },
          { label: "Review type", value: brookside.reviewType },
          { label: "Review domain", value: brookside.reviewDomain },
        ].map((item) => (
          <div key={item.label} className="rounded-lg bg-slate-50 p-3">
            <dt className="text-xs font-medium uppercase tracking-wide text-slate-500">
              {item.label}
            </dt>
            <dd className="mt-1 text-sm font-semibold text-slate-900">
              {item.value}
            </dd>
          </div>
        ))}
      </dl>
    </div>
  );
}
