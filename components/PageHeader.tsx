import type { ReactNode } from "react";

// Consistent full-width page header used across product pages. An optional
// eyebrow sits above the title, an optional description follows, and optional
// actions render on the right on wider screens. The subtle top-to-white wash
// gives core pages a calmer, more finished header without heavy chrome.
export default function PageHeader({
  eyebrow,
  title,
  description,
  actions,
}: {
  eyebrow?: string;
  title: string;
  description?: string;
  actions?: ReactNode;
}) {
  return (
    <div className="border-b border-slate-200 bg-gradient-to-b from-white to-slate-50">
      <div className="mx-auto flex max-w-7xl flex-col gap-4 px-4 py-10 sm:px-6 sm:py-12 lg:px-8 lg:flex-row lg:items-end lg:justify-between">
        <div>
          {eyebrow ? <p className="page-eyebrow">{eyebrow}</p> : null}
          <h1 className="page-title">{title}</h1>
          {description ? (
            <p className="page-description">{description}</p>
          ) : null}
        </div>
        {actions ? (
          <div className="flex flex-wrap items-center gap-3">{actions}</div>
        ) : null}
      </div>
    </div>
  );
}
