// Decorative, blueprint-inspired site-plan illustration for the homepage hero.
//
// This is a synthetic, review-support illustration. It does not represent an
// extracted CAD drawing and contains no embedded text or labels. It reinforces
// human-in-the-loop plan review, not automated approval. The small markers are
// neutral review markers, not approval or status symbols.
//
// All line work uses a single consistent weight and the project slate / water /
// amber palette. The component is purely decorative and is hidden from
// assistive technology.

export default function SitePlanIllustration({
  className = "",
}: {
  className?: string;
}) {
  return (
    <svg
      viewBox="0 0 800 320"
      role="img"
      aria-hidden="true"
      focusable="false"
      preserveAspectRatio="xMidYMid slice"
      className={className}
    >
      {/* Faint blueprint grid */}
      <defs>
        <pattern
          id="siteplan-grid"
          width="40"
          height="40"
          patternUnits="userSpaceOnUse"
        >
          <path
            d="M40 0H0V40"
            fill="none"
            stroke="currentColor"
            strokeWidth="0.5"
            className="text-slate-300"
            opacity="0.5"
          />
        </pattern>
      </defs>
      <rect width="800" height="320" fill="url(#siteplan-grid)" />

      {/* Contour-like lines across the upland */}
      <g
        fill="none"
        stroke="currentColor"
        strokeWidth="1.25"
        className="text-slate-400"
        opacity="0.65"
      >
        <path d="M-10 70 C 140 40, 300 95, 470 60 S 760 70, 820 45" />
        <path d="M-10 110 C 150 85, 310 135, 480 100 S 770 110, 820 90" />
        <path d="M-10 150 C 160 130, 320 175, 500 140 S 780 150, 820 135" />
      </g>

      {/* Faint lot boundaries: two staggered blocks of parcels */}
      <g
        fill="none"
        stroke="currentColor"
        strokeWidth="1"
        className="text-water-600"
        opacity="0.45"
      >
        {/* Upper lot block */}
        <rect x="70" y="180" width="56" height="48" />
        <rect x="126" y="180" width="56" height="48" />
        <rect x="182" y="180" width="56" height="48" />
        <rect x="238" y="180" width="56" height="48" />
        <rect x="70" y="228" width="56" height="48" />
        <rect x="126" y="228" width="56" height="48" />
        <rect x="182" y="228" width="56" height="48" />
        <rect x="238" y="228" width="56" height="48" />
        {/* Lower-right lot block */}
        <rect x="540" y="150" width="50" height="44" />
        <rect x="590" y="150" width="50" height="44" />
        <rect x="640" y="150" width="50" height="44" />
        <rect x="540" y="194" width="50" height="44" />
        <rect x="590" y="194" width="50" height="44" />
        <rect x="640" y="194" width="50" height="44" />
      </g>

      {/* Curving internal road through the subdivision */}
      <g fill="none" strokeLinecap="round">
        <path
          d="M40 300 C 200 280, 300 200, 360 150 S 520 90, 700 120"
          stroke="currentColor"
          strokeWidth="10"
          className="text-slate-200"
        />
        <path
          d="M40 300 C 200 280, 300 200, 360 150 S 520 90, 700 120"
          stroke="currentColor"
          strokeWidth="1.5"
          strokeDasharray="6 7"
          className="text-slate-400"
        />
      </g>

      {/* Stormwater basin shape with a faint water fill */}
      <g>
        <path
          d="M360 232 C 360 210, 392 196, 424 200 C 458 204, 480 222, 474 246 C 468 270, 432 282, 398 276 C 372 271, 360 254, 360 232 Z"
          fill="currentColor"
          className="text-water-100"
          opacity="0.7"
        />
        <path
          d="M360 232 C 360 210, 392 196, 424 200 C 458 204, 480 222, 474 246 C 468 270, 432 282, 398 276 C 372 271, 360 254, 360 232 Z"
          fill="none"
          stroke="currentColor"
          strokeWidth="1.5"
          className="text-water-600"
          opacity="0.7"
        />
        {/* Inner basin contour */}
        <path
          d="M378 234 C 378 220, 400 211, 421 214 C 444 217, 458 230, 454 245 C 450 260, 426 267, 405 263 C 388 260, 378 248, 378 234 Z"
          fill="none"
          stroke="currentColor"
          strokeWidth="1"
          className="text-water-600"
          opacity="0.4"
        />
      </g>

      {/* Subtle, neutral review markers */}
      <g
        fill="none"
        stroke="currentColor"
        strokeWidth="1.5"
        className="text-amber-500"
        opacity="0.85"
      >
        {/* Diamond review marker near the basin */}
        <path d="M417 168 l8 8 -8 8 -8 -8 Z" />
        {/* Circle review marker over the lot block */}
        <circle cx="154" cy="204" r="8" />
        {/* Circle review marker on the road corridor */}
        <circle cx="612" cy="123" r="8" />
      </g>
    </svg>
  );
}
