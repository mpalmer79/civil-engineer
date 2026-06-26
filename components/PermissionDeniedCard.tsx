// Reusable permission-denied notice. Uses calm, review-support language and
// never harsh or final legal wording. Shown when a user lacks access to a
// project action.
export default function PermissionDeniedCard({
  message,
}: {
  message?: string;
}) {
  return (
    <div className="rounded-lg border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-800">
      <p className="font-semibold">Permission denied</p>
      <p className="mt-1">
        {message ??
          "You do not have access to this project action. Ask a project admin or organization admin for access."}
      </p>
    </div>
  );
}
