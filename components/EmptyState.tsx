import type { ReactNode } from "react";

// A consistent empty-state block for lists and pages with no data yet. Keeps the
// "no records" experience readable and professional instead of a bare line of
// text. An optional action (a link or button) can be passed in.
export default function EmptyState({
  title,
  description,
  action,
}: {
  title: string;
  description?: string;
  action?: ReactNode;
}) {
  return (
    <div className="empty-state">
      <p className="text-base font-semibold text-slate-800">{title}</p>
      {description ? (
        <p className="mx-auto mt-1.5 max-w-md text-sm text-slate-600">
          {description}
        </p>
      ) : null}
      {action ? (
        <div className="mt-4 flex flex-wrap justify-center gap-3">{action}</div>
      ) : null}
    </div>
  );
}
