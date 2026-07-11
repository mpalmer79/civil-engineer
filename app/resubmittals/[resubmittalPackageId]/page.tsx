import Link from "next/link";
import PageHeader from "@/components/PageHeader";
import SafetyBoundaryBanner from "@/components/SafetyBoundaryBanner";
import RequestFailureCard from "@/components/RequestFailureCard";
import { getResubmittalPackage } from "@/lib/api";

export default async function ResubmittalDetailRoute(
  props: {
    params: Promise<{ resubmittalPackageId: string }>;
  }
) {
  const params = await props.params;
  const result = await getResubmittalPackage(params.resubmittalPackageId);

  if (!result.ok) {
    return (
      <div>
        <PageHeader
          eyebrow="Resubmittal detail"
          title="Resubmittal package"
          description="A resubmittal package returned by the applicant or design engineer. Intake organizes review-support evidence and does not approve plans or certify compliance."
        />
        <div className="mx-auto max-w-5xl space-y-6 px-4 py-10 sm:px-6 lg:px-8">
          <Link
            href="/review-cycles"
            className="inline-block text-sm font-semibold text-water-700 hover:text-water-600"
          >
            Back to review cycles
          </Link>
          <RequestFailureCard failure={result} />
          <SafetyBoundaryBanner />
        </div>
      </div>
    );
  }
  const pkg = result.data;

  return (
    <div>
      <PageHeader
        eyebrow="Resubmittal detail"
        title={pkg.packageName}
        description="A resubmittal package returned by the applicant or design engineer. Intake organizes review-support evidence and does not approve plans or certify compliance."
      />
      <div className="mx-auto max-w-5xl space-y-6 px-4 py-10 sm:px-6 lg:px-8">
        <Link
          href="/review-cycles"
          className="inline-block text-sm font-semibold text-water-700 hover:text-water-600"
        >
          Back to review cycles
        </Link>

        <div className="surface-card p-6">
              <div className="flex flex-wrap items-center justify-between gap-2">
                <h3 className="text-lg font-semibold text-slate-900">
                  {pkg.packageName}
                </h3>
                <span className="rounded-full bg-slate-100 px-2.5 py-0.5 text-xs text-slate-600">
                  {pkg.status.replace(/_/g, " ")}
                </span>
              </div>
              <p className="mt-2 text-sm text-slate-600">{pkg.summary}</p>
              <p className="mt-1 text-xs text-slate-500">
                Submitted by {pkg.submittedBy}
              </p>
            </div>

            <div className="surface-card p-6">
              <h3 className="text-lg font-semibold text-slate-900">
                Linked documents
              </h3>
              {pkg.documents && pkg.documents.length > 0 ? (
                <ul className="mt-3 space-y-2">
                  {pkg.documents.map((doc) => (
                    <li
                      key={doc.resubmittalDocumentId}
                      className="rounded-md border border-slate-200 px-3 py-2 text-sm"
                    >
                      <span className="font-medium text-slate-800">
                        {doc.documentType.replace(/_/g, " ")}
                      </span>
                      {doc.fileName ? (
                        <span className="ml-2 text-xs text-slate-500">
                          {doc.fileName}
                        </span>
                      ) : null}
                      <p className="mt-0.5 text-xs text-slate-500">
                        {doc.description}
                      </p>
                    </li>
                  ))}
                </ul>
              ) : (
                <p className="mt-2 text-sm text-slate-500">
                  No linked documents yet.
                </p>
              )}
            </div>

            <div className="surface-card p-6">
              <h3 className="text-lg font-semibold text-slate-900">
                Applicant responses
              </h3>
              {pkg.applicantResponses && pkg.applicantResponses.length > 0 ? (
                <ul className="mt-3 space-y-2">
                  {pkg.applicantResponses.map((response) => (
                    <li
                      key={response.applicantResponseId}
                      className="rounded-md border border-slate-200 px-3 py-2 text-sm"
                    >
                      <span className="text-xs font-semibold uppercase tracking-wide text-slate-500">
                        {response.responseTopic}
                      </span>
                      <p className="mt-1 text-slate-700">
                        {response.responseText}
                      </p>
                    </li>
                  ))}
                </ul>
              ) : (
                <p className="mt-2 text-sm text-slate-500">
                  No applicant responses yet.
                </p>
              )}
            </div>

        <SafetyBoundaryBanner />
      </div>
    </div>
  );
}
