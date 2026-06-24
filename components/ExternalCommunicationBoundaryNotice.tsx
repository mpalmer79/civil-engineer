// A clear notice that the response package is draft external communication
// support. It does not send email or official correspondence, and it does not
// approve, certify, stamp, verify CAD, validate the design, or replace a
// licensed Professional Engineer.
export default function ExternalCommunicationBoundaryNotice({
  text,
}: {
  text?: string;
}) {
  const body =
    text ??
    "This is draft external communication support. Civil Engineer AI does not send email or official correspondence, and it does not approve plans, certify compliance, stamp drawings, verify CAD, validate the design, or replace a licensed Professional Engineer. A human reviewer issues any response.";
  return (
    <div className="rounded-lg border border-amber-200 bg-amber-50 px-4 py-3">
      <p className="text-sm font-semibold text-amber-800">
        External communication boundary
      </p>
      <p className="mt-1 text-sm text-amber-700">{body}</p>
    </div>
  );
}
