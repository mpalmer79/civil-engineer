// Honest release-state messaging for operational areas (pilot page, guided demo,
// workspace, and the pilot admin view). It sets accurate expectations without
// dampening the homepage hero. Every line is review-support only and makes no
// approval, certification, or compliance claim.
//
// The "compact" variant is a single reassuring line; the default variant lists
// the current pilot caveats. Capability wording follows the canonical statement
// in docs/PRODUCT.md.

export default function PilotReleaseNote({
  variant = "default",
}: {
  variant?: "default" | "compact";
}) {
  if (variant === "compact") {
    return (
      <p className="rounded-lg border border-water-100 bg-water-50 px-4 py-3 text-sm text-slate-700">
        <span className="font-semibold text-slate-900">
          Design-partner pilot.
        </span>{" "}
        This is a pilot-ready prototype. Billing is not active, and a human
        reviewer remains responsible for every review-support finding.
      </p>
    );
  }

  return (
    <div className="rounded-xl border border-water-100 bg-water-50 p-5">
      <p className="text-sm font-semibold text-slate-900">
        Release state: design-partner pilot
      </p>
      <ul className="mt-3 space-y-1.5 text-sm text-slate-700">
        <li>Design-partner pilot access is available; this is a pilot-ready prototype.</li>
        <li>Pilot requests are reviewed before any real project files are requested.</li>
        <li>Billing is not active and no payment is collected.</li>
        <li>Live AI is disabled by default unless an operator configures a provider.</li>
        <li>
          The public demo uses seeded Brookside Meadows review records; real DXF
          parsing and PDF text-layer indexing are supported as described in the
          positioning doc.
        </li>
        <li>A human reviewer remains responsible for every item.</li>
      </ul>
    </div>
  );
}
