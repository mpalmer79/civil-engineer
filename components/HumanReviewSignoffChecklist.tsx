"use client";

import { useState } from "react";
import type { ResponsePackageSignoffCheckItem } from "@/lib/api";

// A reviewer sign-off checklist that confirms human review is still required.
// The checkboxes are local reviewer aids. They do not change backend state and
// do not approve, certify, or finalize anything.
export default function HumanReviewSignoffChecklist({
  items,
}: {
  items: ResponsePackageSignoffCheckItem[];
}) {
  const [checked, setChecked] = useState<Record<number, boolean>>({});

  return (
    <div className="surface-card p-6">
      <h3 className="text-lg font-semibold text-slate-900">
        Human review sign-off checklist
      </h3>
      <p className="mt-1 text-sm text-slate-600">
        A licensed Professional Engineer or authorized reviewer must complete
        these checks. This checklist is a reviewer aid and does not approve,
        certify, or finalize anything.
      </p>
      <ul className="mt-4 space-y-2">
        {items.map((item, index) => (
          <li key={item.label} className="flex items-start gap-3">
            <input
              id={`signoff-${index}`}
              type="checkbox"
              checked={checked[index] ?? false}
              onChange={(e) =>
                setChecked((prev) => ({ ...prev, [index]: e.target.checked }))
              }
              className="mt-1 h-4 w-4 rounded border-slate-300 text-water-600 focus:ring-water-500"
            />
            <label htmlFor={`signoff-${index}`} className="text-sm">
              <span className="font-medium text-slate-800">{item.label}</span>
              <span className="block text-slate-500">{item.detail}</span>
            </label>
          </li>
        ))}
      </ul>
    </div>
  );
}
