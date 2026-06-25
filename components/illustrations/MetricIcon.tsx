// Faint corner watermark icons for the Brookside Meadows metric cards.
//
// These are intentionally very subtle. They sit behind the numeric value as a
// decorative watermark and must not compete with the number. Every icon shares
// the same viewBox and stroke weight and carries no embedded text. The warning
// flag uses a restrained amber accent because it maps to planted review issues.

export type MetricIconKey =
  | "site-acres"
  | "proposed-lots"
  | "disturbed-acres"
  | "documents"
  | "checklist"
  | "review-issues"
  | "evaluation";

export default function MetricIcon({ icon }: { icon: MetricIconKey }) {
  const common = {
    viewBox: "0 0 32 32",
    role: "img" as const,
    "aria-hidden": true,
    focusable: "false" as const,
    fill: "none",
    stroke: "currentColor",
    strokeWidth: 1.25,
    strokeLinecap: "round" as const,
    strokeLinejoin: "round" as const,
  };

  switch (icon) {
    // Site acres: a site polygon with a contour line.
    case "site-acres":
      return (
        <svg {...common}>
          <path d="M5 11 14 5l13 4-2 18-16 1-4-17Z" />
          <path d="M9 14c4 3 10 3 15-1" strokeWidth={1} />
        </svg>
      );
    // Proposed lots: a small grid of houses.
    case "proposed-lots":
      return (
        <svg {...common}>
          <path d="M5 14l5-4 5 4v6H5v-6Z" />
          <path d="M17 18l5-4 5 4v6h-10v-6Z" />
        </svg>
      );
    // Disturbed acres: a hatched polygon.
    case "disturbed-acres":
      return (
        <svg {...common}>
          <path d="M6 8h20v16H6z" />
          <path d="M6 14l8-6M6 20l14-12M10 24l16-12M18 24l8-6" strokeWidth={0.9} />
        </svg>
      );
    // Documents: stacked sheets.
    case "documents":
      return (
        <svg {...common}>
          <rect x="7" y="5" width="14" height="18" rx="1" />
          <path d="M11 9h7M11 13h7M11 17h5" strokeWidth={1} />
          <path d="M11 5v18" />
        </svg>
      );
    // Checklist items: a checklist.
    case "checklist":
      return (
        <svg {...common}>
          <rect x="6" y="5" width="20" height="22" rx="2" />
          <path d="M10 11l2 2 3-3M10 19l2 2 3-3" />
          <path d="M18 12h4M18 20h4" strokeWidth={1} />
        </svg>
      );
    // Planted review issues: a warning flag with amber accent.
    case "review-issues":
      return (
        <svg {...common}>
          <path d="M8 27V5" />
          <path
            d="M8 6h14l-3 4 3 4H8"
            className="text-amber-500"
            stroke="currentColor"
          />
        </svg>
      );
    // Evaluation cases: an evaluation mark inside a rounded test frame.
    case "evaluation":
      return (
        <svg {...common}>
          <rect x="6" y="6" width="20" height="20" rx="3" />
          <path d="M11 16l3 3 7-7" />
        </svg>
      );
    default:
      return null;
  }
}
