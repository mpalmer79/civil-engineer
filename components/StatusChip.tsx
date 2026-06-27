import type { ReactNode } from "react";

// Reusable status/label chip built on the design-system chip classes. Tones are
// operational only. Green (success) is reserved for system availability and
// connection state, never for an engineering outcome such as approval or
// compliance. Project and workflow statuses default to neutral so the chip
// never implies a final review decision.
export type ChipTone =
  | "neutral"
  | "brand"
  | "success"
  | "warning"
  | "danger";

const toneClass: Record<ChipTone, string> = {
  neutral: "chip-neutral",
  brand: "chip-brand",
  success: "chip-success",
  warning: "chip-warning",
  danger: "chip-danger",
};

// Humanize a snake_case backend status into spaced words for display. This is a
// presentation helper only; it does not change the meaning of a status.
export function humanizeStatus(value: string): string {
  return value.replace(/_/g, " ");
}

export default function StatusChip({
  label,
  prefix,
  tone = "neutral",
  title,
}: {
  label: ReactNode;
  prefix?: string;
  tone?: ChipTone;
  title?: string;
}) {
  return (
    <span className={`chip ${toneClass[tone]}`} title={title}>
      {prefix ? (
        <span className="font-normal opacity-80">{prefix}</span>
      ) : null}
      {label}
    </span>
  );
}
