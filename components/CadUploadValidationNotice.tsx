// Shows the result of intake validation for a browser DXF upload. accepted is a
// neutral confirmation, needs_human_review asks a reviewer to confirm the file,
// and rejected explains why the file was not stored. None of these is an
// engineering determination about the plan.
const styles: Record<string, { box: string; label: string; title: string }> = {
  accepted: {
    box: "border-water-200 bg-water-50",
    label: "text-water-800",
    title: "Upload accepted",
  },
  needs_human_review: {
    box: "border-amber-200 bg-amber-50",
    label: "text-amber-800",
    title: "Upload needs human review",
  },
  rejected: {
    box: "border-red-200 bg-red-50",
    label: "text-red-800",
    title: "Upload rejected",
  },
};

export default function CadUploadValidationNotice({
  status,
  message,
}: {
  status: string | null;
  message: string | null;
}) {
  if (!status) return null;
  const style = styles[status] ?? styles.rejected;
  return (
    <div className={`rounded-lg border px-4 py-3 ${style.box}`}>
      <p className={`text-sm font-semibold ${style.label}`}>{style.title}</p>
      {message ? (
        <p className={`mt-1 text-sm ${style.label}`}>{message}</p>
      ) : null}
    </div>
  );
}
