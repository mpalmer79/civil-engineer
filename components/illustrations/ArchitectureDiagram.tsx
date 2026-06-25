// Clean, diagram-style illustration for the technical credibility section.
//
// The SVG shows the system shape only: a frontend node, a backend node, a DXF
// parser node, the API connection between frontend and backend, and a
// testing / coverage shield. There is no embedded text inside the SVG. Labels
// are provided as accessible HTML next to the diagram by the caller, and the
// SVG itself is decorative.
//
// Line work uses one consistent weight and the project slate / water palette.

export default function ArchitectureDiagram({
  className = "",
}: {
  className?: string;
}) {
  return (
    <svg
      viewBox="0 0 360 200"
      role="img"
      aria-hidden="true"
      focusable="false"
      className={className}
    >
      {/* API connection between frontend and backend */}
      <g
        fill="none"
        stroke="currentColor"
        strokeWidth="1.5"
        className="text-water-600"
      >
        <path d="M118 60h70" strokeDasharray="5 5" />
        {/* Small request / response arrowheads */}
        <path d="M180 56l8 4-8 4" strokeLinecap="round" strokeLinejoin="round" />
        <path d="M126 56l-8 4 8 4" strokeLinecap="round" strokeLinejoin="round" />
        {/* Backend down to parser node */}
        <path d="M250 84v26" strokeDasharray="5 5" />
        <path d="M246 102l4 8 4-8" strokeLinecap="round" strokeLinejoin="round" />
      </g>

      {/* Next.js frontend node */}
      <g
        fill="none"
        stroke="currentColor"
        strokeWidth="1.5"
        strokeLinejoin="round"
      >
        <rect
          x="40"
          y="36"
          width="78"
          height="48"
          rx="6"
          className="text-slate-500"
        />
        {/* Window chrome dots to suggest a browser frontend */}
        <circle cx="52" cy="48" r="2" className="text-slate-400" />
        <circle cx="60" cy="48" r="2" className="text-slate-400" />
        <circle cx="68" cy="48" r="2" className="text-slate-400" />
        <path d="M48 56h62" className="text-slate-300" strokeWidth="1" />
        <path d="M54 66h40" className="text-slate-300" strokeWidth="1" />
      </g>

      {/* FastAPI backend node */}
      <g
        fill="none"
        stroke="currentColor"
        strokeWidth="1.5"
        strokeLinejoin="round"
      >
        <rect
          x="210"
          y="36"
          width="80"
          height="48"
          rx="6"
          className="text-water-700"
        />
        {/* Stacked service lines to suggest an API server */}
        <path d="M222 52h56M222 60h56M222 68h36" className="text-water-600" strokeWidth="1" />
      </g>

      {/* DXF parser node */}
      <g
        fill="none"
        stroke="currentColor"
        strokeWidth="1.5"
        strokeLinejoin="round"
      >
        <rect
          x="208"
          y="120"
          width="84"
          height="46"
          rx="6"
          className="text-slate-500"
        />
        {/* Gear-like parser glyph */}
        <circle cx="234" cy="143" r="9" className="text-slate-500" />
        <path
          d="M234 130v-4M234 160v-4M221 143h-4M251 143h-4M225 134l-3-3M246 155l-3-3M243 134l3-3M225 152l-3 3"
          className="text-slate-400"
          strokeWidth="1"
        />
        {/* Parsed-layers stack */}
        <path d="M256 134l16 6-16 6M256 142l16 6-16 6" className="text-water-600" strokeWidth="1" />
      </g>

      {/* Testing / coverage shield */}
      <g
        fill="none"
        stroke="currentColor"
        strokeWidth="1.5"
        strokeLinecap="round"
        strokeLinejoin="round"
      >
        <path
          d="M70 118l24-8 24 8v22c0 16-13 26-24 30-11-4-24-14-24-30v-22Z"
          className="text-land-700"
        />
        <path d="M84 140l8 8 14-15" className="text-land-700" />
      </g>
    </svg>
  );
}
