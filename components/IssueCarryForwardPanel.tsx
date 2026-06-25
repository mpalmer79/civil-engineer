"use client";

import type { IssueCarryForward } from "@/lib/api";

const statusStyles: Record<string, string> = {
  carried_forward: "bg-amber-50 text-amber-700",
  needs_more_information: "bg-amber-50 text-amber-700",
  needs_follow_up: "bg-amber-50 text-amber-700",
  reviewer_checked: "bg-water-50 text-water-700",
};

// Shows carried-forward review-support items and lets a reviewer carry
// unresolved items forward without creating duplicates.
export default function IssueCarryForwardPanel({
  carryForwards,
  busy,
  onCarryForward,
  message,
}: {
  carryForwards: IssueCarryForward[];
  busy: boolean;
  onCarryForward: () => void;
  message: string | null;
}) {
  return (
    <div className="surface-card p-6">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <h3 className="text-lg font-semibold text-slate-900">
          Carry unresolved items forward
        </h3>
        <button
          type="button"
          onClick={onCarryForward}
          disabled={busy}
          className="rounded-lg bg-water-600 px-3 py-1.5 text-sm font-semibold text-white transition-colors hover:bg-water-700 disabled:opacity-60"
        >
          {busy ? "Working..." : "Carry forward unresolved items"}
        </button>
      </div>
      <p className="mt-1 text-sm text-slate-600">
        Carries forward open workflow items, response items still in revision,
        unpromoted CAD findings, and revision changes needing review. Re-running
        does not create duplicates.
      </p>
      {message ? (
        <p className="mt-3 rounded-md bg-slate-50 px-3 py-2 text-sm text-slate-600">
          {message}
        </p>
      ) : null}
      {carryForwards.length === 0 ? (
        <p className="mt-4 text-sm text-slate-500">
          No carried-forward items yet.
        </p>
      ) : (
        <ul className="mt-4 space-y-2">
          {carryForwards.map((item) => (
            <li
              key={item.carryForwardId}
              className="rounded-lg border border-slate-200 px-3 py-2"
            >
              <div className="flex items-center justify-between gap-2">
                <span className="text-sm font-medium text-slate-800">
                  {item.title}
                </span>
                <span
                  className={`rounded-full px-2 py-0.5 text-[11px] ${
                    statusStyles[item.carriedForwardStatus] ??
                    statusStyles.carried_forward
                  }`}
                >
                  {item.carriedForwardStatus.replace(/_/g, " ")}
                </span>
              </div>
              <p className="mt-1 text-xs text-slate-600">{item.reason}</p>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
