// Small, consistent line icons for the eight homepage workflow steps.
//
// Every icon shares the same 24x24 viewBox, the same single stroke weight, and
// the project slate / water palette so the row reads as one set. Icons are
// decorative and contain no embedded text. The amber accent appears only on the
// findings step, where the concept maps to a flagged review item.
//
// `step` is the workflow step key. Unknown keys fall back to a neutral document
// mark so the layout never breaks.

export type WorkflowStepKey =
  | "intake"
  | "metadata"
  | "findings"
  | "packet"
  | "workflow"
  | "response"
  | "resubmittal"
  | "command-center";

function IconFrame({ children }: { children: React.ReactNode }) {
  return (
    <svg
      viewBox="0 0 24 24"
      role="img"
      aria-hidden="true"
      focusable="false"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.5"
      strokeLinecap="round"
      strokeLinejoin="round"
      className="h-5 w-5"
    >
      {children}
    </svg>
  );
}

export default function WorkflowStepIcon({ step }: { step: WorkflowStepKey }) {
  switch (step) {
    // DXF upload and parsing: a sheet with an upload arrow.
    case "intake":
      return (
        <IconFrame>
          <path d="M6 14V5a1 1 0 0 1 1-1h6l4 4v6" />
          <path d="M13 4v4h4" />
          <path d="M12 21v-7" />
          <path d="M9 17l3-3 3 3" />
        </IconFrame>
      );
    // Extracted CAD metadata: stacked layers.
    case "metadata":
      return (
        <IconFrame>
          <path d="M12 4 3 8.5 12 13l9-4.5L12 4Z" />
          <path d="M3 12.5 12 17l9-4.5" />
          <path d="M3 16.5 12 21l9-4.5" />
        </IconFrame>
      );
    // Findings organization: a flagged review item (amber accent).
    case "findings":
      return (
        <IconFrame>
          <path d="M6 21V4" />
          <path
            d="M6 5h10l-2 3 2 3H6"
            className="text-amber-500"
            stroke="currentColor"
          />
        </IconFrame>
      );
    // Review packet building: a binder of grouped sheets.
    case "packet":
      return (
        <IconFrame>
          <rect x="5" y="4" width="14" height="16" rx="1" />
          <path d="M9 4v16" />
          <path d="M12.5 9h4" />
          <path d="M12.5 13h4" />
        </IconFrame>
      );
    // Workflow tracking: kanban columns.
    case "workflow":
      return (
        <IconFrame>
          <rect x="3" y="4" width="5" height="16" rx="1" />
          <rect x="9.5" y="4" width="5" height="11" rx="1" />
          <rect x="16" y="4" width="5" height="14" rx="1" />
        </IconFrame>
      );
    // Response package generation: an outgoing document envelope.
    case "response":
      return (
        <IconFrame>
          <rect x="3" y="6" width="18" height="13" rx="1.5" />
          <path d="M3.5 7l8.5 6 8.5-6" />
          <path d="M12 3v3" />
        </IconFrame>
      );
    // Resubmittal and revision comparison: two overlapping sheets.
    case "resubmittal":
      return (
        <IconFrame>
          <rect x="4" y="4" width="11" height="14" rx="1" />
          <path d="M9 8h12v12H9" />
          <path d="M12 13l2 2 3-3" />
        </IconFrame>
      );
    // Reviewer command center: a dashboard grid.
    case "command-center":
      return (
        <IconFrame>
          <rect x="3" y="4" width="8" height="6" rx="1" />
          <rect x="13" y="4" width="8" height="10" rx="1" />
          <rect x="3" y="12" width="8" height="8" rx="1" />
          <rect x="13" y="16" width="8" height="4" rx="1" />
        </IconFrame>
      );
    default:
      return (
        <IconFrame>
          <path d="M6 4h8l4 4v12H6V4Z" />
          <path d="M14 4v4h4" />
        </IconFrame>
      );
  }
}
