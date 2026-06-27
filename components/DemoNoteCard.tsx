import type { ReactNode } from "react";
import Link from "next/link";

// Small, tasteful in-context note that orients a visitor inside the public
// Brookside Meadows demo. It explains where the visitor is and offers a link
// back to the guided demo or Start Here. Use sparingly, only where it reduces
// confusion. It carries no engineering outcome and no final-decision wording.
export default function DemoNoteCard({
  message,
  actionHref,
  actionLabel,
}: {
  message: ReactNode;
  actionHref?: string;
  actionLabel?: string;
}) {
  return (
    <div className="alert alert-info flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
      <p className="flex items-start gap-2">
        <span
          aria-hidden="true"
          className="mt-0.5 inline-flex h-5 shrink-0 items-center rounded-full bg-water-100 px-2 text-[11px] font-semibold uppercase tracking-wide text-water-700"
        >
          Demo
        </span>
        <span>{message}</span>
      </p>
      {actionHref && actionLabel ? (
        <Link href={actionHref} className="btn btn-secondary btn-sm shrink-0">
          {actionLabel}
        </Link>
      ) : null}
    </div>
  );
}
