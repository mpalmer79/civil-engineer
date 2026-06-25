// Restrained trust / boundary visual for the professional-boundary banner.
//
// The illustration combines a drafting triangle and an engineer's scale with a
// neutral review checkpoint. It is meant to signal careful, human-led review,
// not certification or approval. It carries no embedded text, no PE stamp, and
// no approval, certified, compliant, safe, passed, or verified imagery. The
// checkpoint mark is a neutral reviewer-action marker, kept in the slate /
// water palette rather than a green success color.

export default function BoundaryMark({
  className = "",
}: {
  className?: string;
}) {
  return (
    <svg
      viewBox="0 0 96 96"
      role="img"
      aria-hidden="true"
      focusable="false"
      fill="none"
      className={className}
    >
      {/* Drafting triangle */}
      <g
        stroke="currentColor"
        strokeWidth="1.75"
        strokeLinejoin="round"
        className="text-water-700"
      >
        <path d="M20 22h44L20 66V22Z" />
        {/* Inner cutout to read as a real drafting triangle */}
        <path d="M28 32h24L28 54V32Z" className="text-water-600" strokeWidth="1" />
      </g>

      {/* Engineer's scale / ruler crossing the lower right */}
      <g
        stroke="currentColor"
        strokeWidth="1.75"
        strokeLinecap="round"
        strokeLinejoin="round"
        className="text-slate-500"
      >
        <path d="M44 78l34-34 6 6-34 34-8 2 2-8Z" />
        <path
          d="M58 62l4 4M64 56l4 4M70 50l4 4"
          strokeWidth="1"
          className="text-slate-400"
        />
      </g>

      {/* Neutral review checkpoint: a reviewer-action marker, not a status seal */}
      <g
        stroke="currentColor"
        strokeWidth="1.75"
        strokeLinecap="round"
        strokeLinejoin="round"
        className="text-water-700"
      >
        <circle cx="30" cy="70" r="11" fill="none" />
        <path d="M25 70l4 4 6-7" />
      </g>
    </svg>
  );
}
